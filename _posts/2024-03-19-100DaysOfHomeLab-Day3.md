---
title: Deploying Nautobot on Kubernetes
date: 2024-03-19 12:00:00 -500
categories: [100DaysOfHomeLab]
tags: [nautobot,kubernetes,cicd]
---

# Day 3 - Creating a CI/CD flow and adding Nautobot Apps

## Previous Posts, what did we do?
In the previous posts I setup flux, organized the folders for pulling the Nautobot container, and configureing an ingress route to work through traefik. Then I created my own custom image so that I could eventually add additional Nautobot Apps or my own App. 

## Automating testing, and deploying of a new version of my custom container

We can use github actions to trigger after creating a new release of our container image. The CI/CD workflow will Lint, Build, Test, then Deploy.

Update the Makefile to include the following below the pull command:
```bash
# Get current branch by default
tag := $(shell git rev-parse --abbrev-ref HEAD)
values := "./kubernetes/values.yaml"

build:
	docker build -t ghcr.io/byrn-baker/nautobot-kubernetes:$(tag) .

push:
	docker push ghcr.io/byrn-baker/nautobot-kubernetes:$(tag)

pull:
	docker pull ghcr.io/byrn-baker/nautobot-kubernetes:$(tag)

lint:
	@echo "Linting..."
	@sleep 1
	@echo "Done."

test:
	@echo "Testing..."
	@sleep 1
	@echo "Done."

update-tag:
	sed -i 's/tag: \".*\"/tag: \"$(tag)\"/g' $(values)
```

We are not building any lint or test steps into this, but instead will just simulate them. The update-tag will take our new releases and update the values.yaml file so that when flux reconciles it will pull the latest image.

To create github workflows you will need a new folder and instructions to tell github what it should do when you make a commit. 

The workflows file will execute four jobs in order from top to bottom, lint, build, test, deploy. This will require a secret to be created in the repository, as it is referenced below in the build step.
Create /.github/workflows/cicd.yaml:
```yaml
---
name: "CI/CD"
on:
  push:
    branches:
      - "*"
  pull_request:
  release:
    types:
      - "created"

permissions:
  packages: "write"
  contents: "write"
  id-token: "write"

jobs:
  lint:
    runs-on: "ubuntu-22.04"
    steps:
      - name: "Check out repository code"
        uses: "actions/checkout@v3"
      - name: "Linting"
        run: "make lint"
  build:
    runs-on: "ubuntu-22.04"
    needs:
      - "lint"
    steps:
      - name: "Check out repository code"
        uses: "actions/checkout@v3"
      - name: "Build the image"
        run: "make tag=${{ github.ref_name }} build"
      - name: "Login to ghcr.io"
        run: "echo ${{ secrets.REPO_TOKEN }} | docker login ghcr.io -u USERNAME --password-stdin"
      - name: "Push the image to the repository"
        run: "make tag=${{ github.ref_name }} push"
  test:
    runs-on: "ubuntu-22.04"
    needs:
      - "build"
    steps:
      - name: "Check out repository code"
        uses: "actions/checkout@v3"
      - name: "Run tests"
        run: "make test"
  deploy:
    runs-on: "ubuntu-22.04"
    needs:
      - "test"
    if: "${{ github.event_name == 'release' }}"
    steps:
      - name: "Check out repository code"
        uses: "actions/checkout@v3"
        with:
          ref: "main"
      - name: "Update the image tag"
        run: "make tag=${{ github.ref_name }} update-tag"
      - name: "Commit changes"
        run: |
          git config user.name github-actions
          git config user.email github-actions@github.com
          git commit -am "Updating the Docker image tag"
          git push origin main
```

The build job will create a new image and assign a tag that corresponds to my release naming. Test will ensure that the image can be run without errors, and deploy will update the tag in the values.yaml. After updating the values.yaml it will commit and push the change back to the repo in the main branch. This will only happen if the above tests are successful as based on the if the github.event_name == release.

From the main Code page there is a releases link on the right side. Click that to get started.
<img src="/assets/lib/github-releases.png" alt="">

Create a release with whatever version or numbering you would like to use. Then click over onto actions and you can watch the CI/CD process. IT should look like this when completed.

<img src="/assets/lib/github-cicd.png" alt="">

Now run a pull on your local machine. You should see that the tag has been updated in your values.yaml.

Flux should also reconcile and you should see that your Nautobot pods will have restarting. You should see that the image has also changed to the new tag you created in your release.

```bash
kubectl get helmreleases -n nautobot
```
```
NAME       AGE    READY     STATUS
nautobot   2d7h   Unknown   Running 'upgrade' action with timeout of 5m0s
```
```bash
kubectl describe pod nautobot-default-56cb8d9c8d-kjlp2  -n nautobot | grep Image
```
```
    Image:         ghcr.io/byrn-baker/nautobot-kubernetes:v0.0.2
    Image ID:      ghcr.io/byrn-baker/nautobot-kubernetes@sha256:58c10087d7134a355e019c5eaadebb3214c727491a4c2a9ec784903a96696afa
    Image:         ghcr.io/byrn-baker/nautobot-kubernetes:v0.0.2
    Image ID:      ghcr.io/byrn-baker/nautobot-kubernetes@sha256:58c10087d7134a355e019c5eaadebb3214c727491a4c2a9ec784903a96696afa
```

## Adding Nautobot Apps to our custom image.
Create a new file in the root of your working directory called ```requirements.txt``` and place a couple of Nautobot Apps in there.
```bash
echo -e "nautobot_plugin_nornir\nnautobot-golden-config" > requirements.txt
```
We also need a new directory to store the nautobot_config.py file that requires updating from the default that comes in our image. This file is used to customize the Nautobot Application and has lots of switches, but we only care about the Apps portion for now. Check out the [nautobot-golden-config](https://docs.nautobot.com/projects/golden-config/en/latest/admin/install/). This site provides what is required in the nautobot_config.py. You can use the example on repo as well.

Also update the Dockerfile to include installing these additional packages on our custom container. 
```bash
ARG NAUTOBOT_VERSION=2.1.5
ARG PYTHON_VERSION=3.11
FROM ghcr.io/nautobot/nautobot:${NAUTOBOT_VERSION}-py${PYTHON_VERSION}

COPY requirements.txt /tmp/

RUN pip install -r /tmp/requirements.txt

COPY ./configuration/nautobot_config.py /opt/nautobot/
```
Now commit these changes and create a new release version, this will trigger the CI/CD workflow and push this new image to our cluster. After the new pods come up you should see that the Nautobot Apps are now added to our deployment.