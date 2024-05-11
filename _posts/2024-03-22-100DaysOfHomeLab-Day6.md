---
title: Deploying K3s with Ansible - Part 3
date: 2024-03-22 12:00:00 -500
categories: [100DaysOfHomeLab]
tags: [kubernetes,ansible,cert-manager,100DaysOfHomeLab]
image:
  path: /assets/img/headers/k3s_ansible.webp
---

# Day 6 - Deploying Cert-Manager with ansible
Cert-manager is a Kubernetes native certificate management controller. It helps automate the management and issuance of TLS certificates from various certificate authorities (CAs) such as Let's Encrypt, Venafi, HashiCorp Vault, or a custom CA. I am going to use this in conjunction with emberstacks reflector so that when I create a new certificate for my homelab I can mirror that certificate to more than one namespace.
> In Kubernetes, a namespace is a virtual cluster or a logical partition of Kubernetes resources within a Kubernetes cluster. It's a way to divide cluster resources between multiple users (or teams) and provide a scope for Kubernetes objects.
{: .prompt-tip }

I will be using LetsEncrypt to generate the certificates for my homelab, this way anything I self host will always have a certificate and I can avoid the warning when I use the services.

## Installing Cert-Manager
I will re-use a lot of the same process from the previous post. These steps are pretty much straight from the Helm Chart for cert-manager

```yaml
{% raw %}
---
### Installing Cert Manager
- block:
  - name: Add jetstack Helm repository
    kubernetes.core.helm_repository:
      name: jetstack
      repo_url: https://charts.jetstack.io

  - name: Update Helm jetstack repositories
    kubernetes.core.helm_repository:
      name: jetstack
      repo_url: https://charts.jetstack.io
      force_update: yes

  - name: Create cert-manager namespace
    kubernetes.core.k8s:
      api_version: v1
      kind: Namespace
      name: cert-manager
      state: present

  - name: Apply cert-manager CRDs
    kubernetes.core.k8s:
      state: present
      src: "https://github.com/cert-manager/cert-manager/releases/download/v{{certmanager_version}}/cert-manager.crds.yaml"

  - name: Install cert-manager Helm chart
    kubernetes.core.helm:
      name: cert-manager
      chart_ref: jetstack/cert-manager
      release_namespace: cert-manager
      values: "{{ cert_manager }}"
      chart_version: "{{ certmanager_version }}"
      state: present
{% endraw %}
```

## Setting up a cloudflare secret and installing reflector

The secret being created here is so that cert-manager and can validate that you own the domain that you are using for the certificates.
```yaml
{% raw %}
- name: Apply issuers secrets
    kubernetes.core.k8s:
      state: present
      definition: "{{ lookup('template', 'secret-cf-token.j2') }}"
{% endraw %}

```
./roles/install-cert-manager/templates/secret-cf-token.j2:

```yaml
{% raw %}
---
apiVersion: v1
kind: Secret
metadata:
  name: cloudflare-token-secret
  namespace: cert-manager
type: Opaque
stringData:
  cloudflare-token: {{ cf_token }}
{% endraw %}
```

Next Task:
```yaml
{% raw %}
- name: Add emberstack Helm repository
    kubernetes.core.helm_repository:
      name: emberstack
      repo_url: https://emberstack.github.io/helm-charts

  - name: Update Helm repository
    kubernetes.core.helm_repository:
      name: emberstack
      repo_url: https://emberstack.github.io/helm-charts
      force_update: yes

  - name: Install reflector Helm chart
    kubernetes.core.helm:
      name: reflector
      chart_ref: emberstack/reflector
      release_namespace: default
      state: present
{% endraw %}
```

This configuration sets up a ClusterIssuer resource named letsencrypt-staging, which uses Let's Encrypt's staging environment for issuing TLS certificates and employs Cloudflare for DNS challenge validation.
> testing with a staging environment before obtaining a real certificate helps ensure a smooth and error-free deployment of TLS certificates in production environments while minimizing risks associated with misconfigurations or excessive certificate requests. LetsEncrypt rate limits and this will avoid being limited from requested certificates.
{: .prompt-tip }

```yaml
{% raw %}
- name: Apply Staging ClusterIssuer
    kubernetes.core.k8s:
      state: present
      definition: "{{ lookup('template', 'letsencrypt-staging.j2') }}"
{% endraw %}
```
./roles/install-cert-manager/templates/letsencrypt-staging.j2:

```yaml
{% raw %}
---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: {{ cf_email }}
    privateKeySecretRef:
      name: letsencrypt-staging
    solvers:
      - dns01:
          cloudflare:
            email: {{ cf_email }}
            apiTokenSecretRef:
              name: cloudflare-token-secret
              key: cloudflare-token
        selector:
          dnsZones: {{ cf_zones }}
{% endraw %}
```

Now we can request the certificate from LetsEncrypt, The 'Get challenges' task will check the challenge of the LetsEncrypt check of the cloudflare dns to ensure you are the owner of the domain. I then store the certificate and key in another folder so that I have them incase I need them again later on.

```yaml
{% raw %}
- name: Generate Staging Certificate
    kubernetes.core.k8s:
      state: present
      definition: "{{ lookup('template', 'stage-local-byrnbaker-me.j2') }}"

  - name: Get challenges
    kubernetes.core.k8s_info:
      kind: Challenge
      namespace: default
    register: result
    until: result.resources | length == 0
    retries: 20
    delay: 30
  
  - name: Capture the certificate for use later
    shell: |
      kubectl get secret {{ staging_secret }} -n default -o jsonpath="{.data.tls\.crt}" | base64 --decode > ./generated_certificate/staging-tls.crt
  - name: Capture the certificate for use later
    shell: |
      kubectl get secret {{ staging_secret }} -n default -o jsonpath="{.data.tls\.key}" | base64 --decode > ./generated_certificate/staging-tls.key
  tags: staging-install
{% endraw %}
```

This block of tasks would be run with the tag at command line.
```bash 
ansible-playbook install-traefik.yml --tags "staging-install"
```