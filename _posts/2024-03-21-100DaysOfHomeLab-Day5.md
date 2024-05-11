---
title: Deploying K3s with Ansible - Part 2
date: 2024-03-21 12:00:00 -500
categories: [100DaysOfHomeLab]
tags: [kubernetes,ansible,traefik,100DaysOfHomeLab]
image:
  path: /assets/img/headers/k3s_ansible.webp
---

# Day 5 - Deploying Traefik with ansible
After creating the VMs and using the site.yml to create the k3s cluster, its time to deploy stuff on it. One of the reason I started down this road was to host this blog. I needed something easy ,fast and did not look terrible. I also wanted something I could secure with SSL certificates and would work with cloudflare. Kubernetes made sense because I could accomplish those things and learn a little bit about CI/CD pipelines and using the built in tool provided by gitlab. I'll post on these topics more later, first lets talk about Traefik.

Before we deploy services like a webserver into the cluster we need something that can direct traffic from outside the cluster to specific service inside the cluster. Traefik can be use as a load balancer, API gateway, Kubernetes Ingress, and Certificate Management. I want to use it as an a Kubernetes Ingress, this will direct inbound traffic to the different services deployed behind the cluster based on the FQDN you use in DNS.

Part of the ```sites.yml``` playbook MetalLB is setup to perform the load balancing and if you look through the example group_vars you will notice that it is mentioned a few times and there are a pool of IPs assigned to it. Check out this post from [technotim](https://technotim.live/posts/reverse-proxy-kubernetes/) if you want to learn a little bit more about how metalLB and Traefik work together.

## Automating Traefik helm install with Ansible
Ansible has a kubernetes module which is great because I can take all of the kubectl commands and helm command and just use Ansible task to make this a bit more repeatable. I can setup a nice workflow and re-use it as much as is needed.

I am using the block feature in ansible so I can block tasks together and run those with specific tags

Adding helm charts:
```yaml
- block: 
  - name: Add Traefik Helm repository
    kubernetes.core.helm_repository:
      name: traefik
      repo_url: https://helm.traefik.io/traefik

  - name: Update Helm repositories
    kubernetes.core.helm_repository:
      name: traefik
      repo_url: https://helm.traefik.io/traefik
      force_update: yes
```

Create a namespace for traefik and install it with the helm charts. The traefik_values variables are all stored under ```./roles/install-traefik/vars/main.yml```. These are where you can make specific configurations to the helm charts when install applications like this. I will reuse this method a lot. If you would like route more than http and https requests this is where you would add those "entry points". Under the ports section you can create entry points and what they should do. These values are always defined by the helm chart and you can find more details about them in the helm chart readme for the application you are installing.
```yaml
{% raw %}
- name: Create Traefik namespace
    kubernetes.core.k8s:
      api_version: v1
      kind: Namespace
      name: traefik
      state: present

  - name: Install Traefik Helm chart
    kubernetes.core.helm:
      name: traefik
      chart_ref: traefik/traefik
      release_namespace: kube-system
      values: "{{ traefik_values }}"
      state: present
{% endraw %}
```

```yaml
traefik_values:
  globalArguments:
    - "--global.sendanonymoususage=false"
    - "--global.checknewversion=false"

  additionalArguments:
    - "--serversTransport.insecureSkipVerify=true"
    - "--log.level=INFO"

  deployment:
    enabled: true
    replicas: 3
    annotations: {}
    podAnnotations: {}
    additionalContainers: []
    initContainers: []

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
  ingressRoute:
    dashboard:
      enabled: false

  providers:
    kubernetesCRD:
      enabled: true
      ingressClass: traefik-external
      allowExternalNameServices: true
    kubernetesIngress:
      enabled: true
      allowExternalNameServices: true
      publishedService:
        enabled: false

  rbac:
    enabled: true

  service:
    enabled: true
    type: LoadBalancer
    annotations: {}
    labels: {}
    spec:
      loadBalancerIP: 192.168.30.80 # this should be an IP in the MetalLB range
    loadBalancerSourceRanges: []
    externalIPs: []
```
Create a default middleware:
> middleware refers to a set of functionalities that can be applied to HTTP requests and responses as they pass through the Traefik proxy. Middleware allows you to modify, filter, or enhance incoming requests or outgoing responses, providing a way to implement various features and behaviors within your network infrastructure.
{: .prompt-tip }

I want to use variables when configuring these apps so I decided to go with Jinja2 templates to facilitate this. I can define those variables in group_vars and leave the ability to make adjustments depending on the environment later on. Normally you would create a yaml file and store this information and call it up with a kubectl command.
```yaml
{% raw %}
- name: Apply default headers
    kubernetes.core.k8s:
      state: present
      definition: "{{ lookup('template', 'default-headers.j2') }}"
{% endraw %}
```

No variable in here, but you never know that could change some day.
```yaml
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: default-headers
  namespace: default
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
```

Traefik comes with a nice dashboard where you can easily validate you new ingress routes and if your certificate has been applied or not. The dashboard requires the password to be base64 encoded

```yaml
{% raw %}
- name: Generate base64-encoded admin password
    shell: htpasswd -nb admin password | openssl base64
    register: base64_password

  - debug:
      var: base64_password.stdout

  - name: Apply Traefik dashboard secret
    kubernetes.core.k8s:
      state: present
      definition: "{{ lookup('template', 'secret-dashboard.j2') }}"
{% endraw %}
```

The secret_dashboard.j2 is a secret that is stored in kubernetes and is used with the traefik dashboard login.
```yaml
---
{% raw %}
apiVersion: v1
kind: Secret
metadata:
  name: traefik-dashboard-auth
  namespace: traefik
type: Opaque
data:
  users: {{base64_password.stdout}}
{% endraw %}
```

Finally we can add a new middleware for the dashboard that uses the above secret we just created. We can also add the Traefik ingress route as well.
```yaml
{% raw %}
- name: Apply middleware
    kubernetes.core.k8s:
      state: present
      definition: "{{ lookup('template', 'middleware.j2') }}"
  
  - name: Apply Traefik ingress
    kubernetes.core.k8s:
      state: present
      definition: "{{ lookup('template', 'staging-ingress.j2') }}"
  tags: staging-install
```

```yaml
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: traefik-dashboard-basicauth
  namespace: traefik
spec:
  basicAuth:
    secret: traefik-dashboard-auth
{% endraw %}
```

This ingress route is what will route outside requests into the traefik dashboard service, or container that is running inside the cluster. When installing from the helm chart one of the things defined was the ingress.class. This is created then and you will use that class for your ingress routes along with the entryPoints. The variables used here again are all defined in my group_vars. The staging_secret is the name of our staging certificate that we will get from LetEncrypt in the next step of the process.
```yaml
{% raw %}
apiVersion: traefik.containo.us/v1alpha1
kind: IngressRoute
metadata:
  name: traefik-dashboard
  namespace: traefik
  annotations: 
    kubernetes.io/ingress.class: traefik-external
spec:
  entryPoints:
    - websecure
  routes:
    - match: Host(`traefik.{{ install_domain }}`)
      kind: Rule
      middlewares:
        - name: traefik-dashboard-basicauth
          namespace: traefik
      services:
        - name: api@internal
          kind: TraefikService
  tls:
    secretName: {{ staging_secret }}
{% endraw %}
```