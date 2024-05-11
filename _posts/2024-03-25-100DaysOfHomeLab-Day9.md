---
title: Deploying K3s with Ansible - Part 6
date: 2024-03-25 12:00:00 -500
categories: [100DaysOfHomeLab]
tags: [kubernetes,cicd,ansible,OPNsense,100DaysOfHomeLab]
image:
  path: /assets/img/headers/k3s_ansible.webp
---

# Adding host overrides to OPNsense firewall
I use OPNsense as my firewall, DHCP, DNS server for my homelab. I've set an internal domain that I use so that when hosts pickup a DHCP address the hostname used in that exchange is added to the DNS records and it provided an FQDN. My Homelab however I want to use a different domain so there is where host overrides come in handy as a quick way to supply your internal DNS server with different domains without having to configure an entirely new system.

This can be done through the GUI of course, but since I am building the deployment automation with Ansible I might as well have a task for this as well. OPNsnse has an API, and also its own Ansible module, so check out these resources to learn more about [OPNsense-API](https://docs.opnsense.org/development/api.html) and [OPNsense Ansible Module](https://github.com/ansibleguy/collection_opnsense).

install-opnsense-host-overrides.yml
```yaml
{% raw %}
- hosts: localhost
  gather_facts: no
  module_defaults:
    group/ansibleguy.opnsense.all:
      firewall: "{{ firewall_ip }}"
      api_port: "{{ firewall_port }}"
      api_key: "{{ opn_key }}"
      api_secret: "{{ opn_secret }}"
      ssl_verify: false
  
  tasks:
    - set_fact:
        overrides:
          - hostname: 'traefik'
          - hostname: 'rancher'
          - hostname: 'gitlab'
          - hostname: 'registery'
          - hostname: 'minio'
          - hostname: 'kas'
          - hostname: 'nautobot'


    - name: Adding
      ansibleguy.opnsense.unbound_host:
        hostname: "{{ item.hostname }}"
        domain: "{{ install_domain }}"
        value: "{{ traefik_ip  }}"
        description: "k3s redirect"
        reload: false
      loop: "{{ overrides }}"
    
    - name: Reloading
      ansibleguy.opnsense.reload:
        target: "unbound"
{% endraw %}
```

1. Set the various required variables so that ansible can communicate with the firewall. 
2. Use set_fact to create a list of hostnames I want to override.
3. Add the hostnames to the unbound DNS server on the firewall iterating through the overrides list.
4. Reload the unbound service.

item.hostname is pulling from the overrides list from the set_fact. install_domain, and traefik_ip is set in the group_vars. Because we are using Traefik as our proxy we want to make sure that when going to traefik.example.com that unbound provides the IP of Traefik as the IP address. From there Traefik picks up the requested hostname in the headers and directs the inbound requests to the correct service inside the cluster.

```bash
$ dig traefik.homelab.example.com
;; communications error to 127.0.0.53#53: timed out

; <<>> DiG 9.18.18-0ubuntu0.22.04.2-Ubuntu <<>> traefik.homelab.example.com
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 3956
;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 65494
;; QUESTION SECTION:
;traefik.homelab.example.com.   IN      A

;; ANSWER SECTION:
traefik.homelab.example.com. 3600 IN    A       192.168.30.80

;; Query time: 4 msec
;; SERVER: 127.0.0.53#53(127.0.0.53) (UDP)
;; WHEN: Sat Mar 30 17:01:01 UTC 2024
;; MSG SIZE  rcvd: 72
```