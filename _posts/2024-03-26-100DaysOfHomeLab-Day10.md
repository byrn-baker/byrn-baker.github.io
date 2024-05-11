---
title: Deploying K3s with Ansible - Part 7
date: 2024-03-26 12:00:00 -500
categories: [100DaysOfHomeLab]
tags: [kubernetes,cicd,ansible,gitlab,100DaysOfHomeLab]
image:
  path: /assets/img/headers/k3s_ansible.webp
---

# Deploying Gitlab with Helm Charts
In the previous posts, we create VMs for a k3s cluster, deployed the k3s cluster, added traefik for proxying requests to service, added cert-manager to handle issuing certifications from LetsEncrypt, deployed the Rancher-UI and installed Longhorn for persistent storage across our nodes, and configured hostname overrides on unbound dns service running on my OPNsense firewall.

I wanted to host gitlab internally as well so I checked out their documentation to see what was needed and how to setup the helm chart values to work with traefik. You can look at those for your self [here](https://docs.gitlab.com/charts/). Like the Rancher UI the Gitlab deployment uses its own ingress proxy with nginx. Leaving the defaults works, but I would have to manage that ingress separately and if I want to make it public I would not be able to ports 443 to both traefik and nginx.

# Ansible Playbook for gitlab
Nothing new here I am using the same workflow as before. This is a role that is placed in ```./roles/install-gitlab/tasks/main.yml```. 
1. Start by adding the helmchart to your helm repo. 
2. Create a new namespace for gitlab. 
3. Install gitlab
4. Create a middleware for the namespace
5. Apply the ingress route for gitlab in the namespace.

```yaml
{% raw %}
---
- block: 
  - name: Add gitlab Helm repository
    kubernetes.core.helm_repository:
      name: gitlab
      repo_url: https://charts.gitlab.io/

  - name: Update Helm repositories
    kubernetes.core.helm_repository:
      name: gitlab
      repo_url: https://charts.gitlab.io/
      force_update: yes
  
  - name: Create gitlab namespace
    kubernetes.core.k8s:
      api_version: v1
      kind: Namespace
      name: gitlab
      state: present

  - name: Install gitlab-staging Helm chart
    kubernetes.core.helm:
      name: gitlab
      chart_ref: gitlab/gitlab
      release_namespace: gitlab
      values: "{{ staging_gitlab_values }}"
      state: present

  - name: Apply default headers
    kubernetes.core.k8s:
      state: present
      definition: "{{ lookup('template', 'default-headers.j2') }}"

  - name: Apply Traefik-Gitlab staging ingress
    community.kubernetes.k8s:
      state: present
      definition: "{{ lookup('template', 'staging-ingress.j2') }}"
    register: ingress_output
  tags: staging-install
{% endraw %}
```

## Gitlab Helm Values
Finding the correct helm values was a little tricky, but they are all listed [here](https://docs.gitlab.com/charts/installation/command-line-options.html). The important stuff that we need to make changes to are below.

### gitlab global
1. You need to set the root domain so this would be homelab.example.com
2. edition comes defaulted to enterprise edition and we are not paying for this so change it to community edition
3. ingress is enabled, but the provider is traefik and the class is the traefik-external we setup in the begining.
4. annotations for the ingress that we will have a certificate, it will be on port 443 and the entrypoint will be websecure. Again this was something created with the installation of traefik at the beginning.
5. Cert-Manager is already installed and gitlab helm does not need to manage any certificates for the ingress.

```yaml
{% raw %}
staging_gitlab_values:
  global:
    hosts:
      domain: "{{ commonname | replace('*.', '') }}"
    edition: ce
    ingress:
      enabled: true
      provider: traefik
      class: traefik-external
      annotations: 
        kubernetes.io/tls-acme: true
        traefik.ingress.kubernetes.io/router.tls: "true"
        traefik.ingress.kubernetes.io/router.entrypoints: websecure
      configureCertmanager: false
{% endraw %}
```

### additional gitlab settings
1. Cert-Manager is already installed
2. certmanager-issuer we will use our cloudflare email
3. nginx is set to false so it is not installed
4. postgresql image can be changed to a different version, but this is the recommended version for this helm chart.
5. persistence is enabled and it will use the longhorn application for this storage.
6. Registry, minio, gitlab, gitlab-pages, and webservice are all seperate services we will need to create ingress routes for. The helm chart needs to be informed of this and the certificate we intend to use. So use the secret name we setup for staging to validate this all works.
7. The toolbox configuration ensures that there is one instance of the GitLab Toolbox component running and that it is scheduled on a different node than instances of the Gitaly component to improve fault tolerance and reliability of the GitLab deployment.
```yaml
{% raw %}
staging_gitlab_values:
  certmanager:
    install: false
  certmanager-issuer:
    email: "{{ cf_email }}"
  nginx-ingress:
    enabled: false
  postgresql:
    image:
      tag: 13.6.0
  persistence:
    enabled: true
    gitaly:
      enabled: true
      storageClassName: my-gitaly-storage
  # CUSTOM - Required for separately managed certmanager
  registry:
    ingress:
      tls:
        secretName: "{{ staging_secret }}"
  minio:
    ingress:
      tls:
        secretName: "{{ staging_secret }}"
  gitlab:
    gitlab-pages:
      ingress:
        tls:
          secretName: "{{ staging_secret }}"
    webservice:
      ingress:
        path: 
        tls:
          secretName: "{{ staging_secret }}"
    toolbox:
      replicas: 1
      antiAffinityLabels:
        matchLabels:
          app: 'gitaly'
{% endraw %}
```

### Default headers and Ingress Route
The last two tasks in this playbook are apply the default headers middleware from the Traefik playbook, but in the gitlab namespace. The ingress route is where what hostname gets routed to which service.

Default Headers
```yaml
{% raw %}
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: default-headers
  namespace: gitlab
spec:
  headers:
    browserXssFilter: true
    contentTypeNosniff: true
    forceSTSHeader: true
    stsIncludeSubdomains: true
    stsPreload: true
    stsSeconds: 15552000
    customFrameOptionsValue: SAMEORIGIN
    customRequestHeaders:
      X-Forwarded-Proto: https
{% endraw %}
```

IngressRoute: There is one configuration for each service that gitlab uses - ```./roles/install-gitlab/templates/staging-ingress.j2```
1. gitlab main website or web service
2. MinIO in GitLab serves as a scalable and reliable object storage solution, enabling efficient storage and management of artifacts, backups, and other data generated and consumed by GitLab instances.
3. GitLab Container Registry serves as a centralized repository for storing Docker images used in GitLab projects, providing seamless integration with CI/CD pipelines, facilitating collaboration and sharing, and offering security and access control features to manage container image storage effectively.
4. SSH service in GitLab plays a crucial role in enabling secure communication and authentication for Git operations, providing a reliable and secure method for users to interact with GitLab repositories and for CI/CD pipelines to execute tasks securely.


```yaml
{% raw %}
---
apiVersion: traefik.containo.us/v1alpha1
kind: IngressRoute
metadata:
  name: gitlab
  namespace: gitlab
  annotations:
    kubernetes.io/ingress.class: traefik-external
spec:
  entryPoints:
    - websecure
    - web
  routes:
    - match: Host(`gitlab.{{ install_domain }}`) && PathPrefix(`/admin/sidekiq`)
      kind: Rule
      services:
        - name: gitlab-webservice-default
          port: 8080
    - match: Host(`gitlab.{{ install_domain }}`)
      kind: Rule
      services:
        - name: gitlab-webservice-default
          port: 8181
      middlewares:
        - name: default-headers
          namespace: gitlab
  tls:
    secretName: {{ staging_secret }}
---
apiVersion: traefik.containo.us/v1alpha1
kind: IngressRoute
metadata:
  name: minio
  namespace: gitlab
  annotations:
    kubernetes.io/ingress.class: traefik-external
spec:
  entryPoints:
    - websecure
  routes:
    - match: Host(`minio.{{ install_domain }}`)
      kind: Rule
      services:
        - name: gitlab-minio-svc
          port: 9000
  tls:
    secretName: {{ staging_secret }}
---
apiVersion: traefik.containo.us/v1alpha1
kind: IngressRoute
metadata:
  name: registry
  namespace: gitlab
  annotations:
    kubernetes.io/ingress.class: traefik-external
spec:
  entryPoints:
    - websecure
  routes:
    - match: Host(`registry.{{ install_domain }}`)
      kind: Rule
      services:
        - name: gitlab-registry
          port: 5000
  tls:
    secretName: {{ staging_secret }}
---
apiVersion: traefik.containo.us/v1alpha1
kind: IngressRouteTCP
metadata:
  name: gitlab-ssh
  namespace: gitlab
  annotations:
    kubernetes.io/ingress.class: traefik-external
spec:
  entryPoints:
    - gitlab-ssh
  routes:
    - match: HostSNI(`*`)
      kind: Rule
      services:
        - name: gitlab-gitlab-shell
          port: 22
{% endraw %}
```

Getting SSH to work with Traefik took me a minute to figure out. The missing piece was not the ingress route but understanding that I needed to create an entry point that I could use before this would work with Traefik. If you recall when setting up traefik I mentioned this piece. Make sure that your traefik_values included this section called gitlab-ssh.

```yaml
{% raw %}
ports:
    web:
      redirectTo:
        port: websecure
        priority: 10
    websecure:
      tls:
        enabled: true
    gitlab-ssh:
      port: 22
      expose: true
      exposedPort: 22
      protocol: TCP
{% endraw %}
```

Once all of these are in place you should be ready to install gitlab.