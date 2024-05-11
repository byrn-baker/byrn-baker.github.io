---
title: Deploying K3s with Ansible - Part 4
date: 2024-03-23 12:00:00 -500
categories: [100DaysOfHomeLab]
tags: [kubernetes,ansible,rancher-ui,100DaysOfHomeLab]
image:
  path: /assets/img/headers/k3s_ansible.webp
---

# Adding Rancher-UI - Incase you want a GUI to help with managing your cluster
Rancher UI can be installed on your cluster with the helm chart, however it will install its own load balancer and ingress, and by default will not use your traefik proxy that was setup in the my first post on this topic.

Again we will use a similar process to perform the install with the helm charts from previous posts.

```yaml
{% raw %}
- block: 
  - name: Add Rancher Helm repository
    kubernetes.core.helm_repository:
      name: rancher
      repo_url: https://releases.rancher.com/server-charts/stable

  - name: Update Helm Rancher repositories
    kubernetes.core.helm_repository:
      name: rancher
      repo_url: https://releases.rancher.com/server-charts/stable
      force_update: yes

  - name: Check if cert-manager is installed
    kubernetes.core.k8s_info:
      kind: Namespace
      name: cert-manager
    register: cert_manager_namespace

  - fail:
      msg: "cert-manager is not installed. Please install cert-manager before proceeding."
    when: cert_manager_namespace.resources | length == 0

  - name: Create cattle-system namespace
    kubernetes.core.k8s:
      api_version: v1
      kind: Namespace
      name: cattle-system
      state: present

  - name: Install Rancher Helm chart
    kubernetes.core.helm:
      name: rancher
      chart_ref: rancher-stable/rancher
      release_namespace: cattle-system
      values: "{{staging_rancher_ui_values }}"
      state: present
{% endraw %}
```

We need to make some minor adjustments to the normal installation in the helm values so that is works with our existing staging wildcard certificate and traefik proxy. These values can be found in the rancher helm chart docs, the hostname I have defined in groups_vars, along with the password, and version I want to install. The version of rancher UI will depending on the version of k3s you are using and you can also find more details about that [here](https://ranchermanager.docs.rancher.com/).
```yaml
{% raw %}
staging_rancher_ui_values:
  hostname: "{{ rancher_hostname}}"
  replicas: 3
  bootstrapPassword: "{{ rancher_password }}"
  version: "{{ rancher_version }}"
  ingress:
    tls: 
      source: local-example-com-staging-tls
{% endraw %}
```

The ingress route here will point inbound requests to the cluster for rancher to the rancher-ui service
```yaml
{% raw %}
- name: Apply Production Traefik ingress for Rancher UI
    kubernetes.core.k8s:
      state: present
      definition: "{{ lookup('template', 'staging-ingress.j2') }}"
tags: staging-install
{% endraw %}
```

./roles/install-rancher-ui/templates/staging-ingress.j2:
```yaml
{% raw %}
apiVersion: traefik.containo.us/v1alpha1
kind: IngressRoute
metadata:
  name: rancher-ui-ingress
  namespace: cattle-system
  annotations: 
    kubernetes.io/ingress.class: traefik-external
spec:
  entryPoints:
    - websecure
  routes:
    - match: Host(`rancher.{{ install_domain }}`)
      kind: Rule
      services:
        - name: rancher
          port: 443
  tls:
    secretName: {{ staging_secret }}
{% endraw %}
```

Here is the service for Rancher-UI from kubectl
```bash
$ kubectl get svc -n cattle-system
NAME              TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
rancher           ClusterIP   10.43.2.94     <none>        80/TCP,443/TCP   4d3h
rancher-webhook   ClusterIP   10.43.46.135   <none>        443/TCP          4d3h
```

Here is a view from the traefik dashboard showing the mapping is working
<img src="./assets/img/traefik-dashboard.webp" alt="">

You can run this from command line with the tags
```bash
ansible-playbook install-rancher-ui.yml --tags "staging-install"
```