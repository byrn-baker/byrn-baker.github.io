---
title: Deploying K3s with Ansible
date: 2024-03-20 12:00:00 -500
categories: [100DaysOfHomeLab]
tags: [kubernetes,ansible,100DaysOfHomeLab]
image:
  path: /assets/img/headers/k3s_ansible.webp
---

# Day 4 - Automating VMs and deploying k3s
I decided that it was time to create some tasks that could build and destroy VMs for my k3s cluster, after I had to tear it all down a couple of times. I found this great quick start from [technotim](https://technotim.live/posts/k3s-etcd-ansible/), which provided a big jump ahead of the game.

I wanted to add a little bit of my own twist to it, however, I wanted the ability to also create VMs in Proxmox as well. With a little bit of google foo I found the [Proxmox API documentation](https://pve.proxmox.com/pve-docs/api-viewer/index.html#/nodes), armed with this I set off to automate. You can find my [git repo here](https://github.com/byrn-baker/k3s-ansible/tree/private)

## Planning
If you followed along with [technotims](https://technotim.live/posts/k3s-etcd-ansible/) post and cloned his repository you should have yourself an inventory. Adding the creation of VMs to the mix on this I want to keep original k3s-ansible repo intact as much as possible. I don't like inventory files in the ini format so that was the first thing I changed. While I was at it I figured this would also be a good place to add hostvars as well that might be specific to my VM requirements. Most of the time in Ansible it all starts with the inventory.

To create a vm with the API in Proxmox we need a couple of pieces of information
- vmid
- host storage
- how man vcpus
- how much memory

The inventory seemed like the right place for these items for now. Each node could require something a little different so they could be customized easiest here. I added the iscsi target later for the addition of long-horn, more on this later.
```yaml
all:
  children:
    k3s_cluster:
      children:
        master:
          hosts:
            k3s01:
              ansible_host: 192.168.30.38
              vmid: 2001
              storage: "dell-pve-ssd-01"
              vcpus: 10
              memory: 4096
            k3s02:
              ansible_host: 192.168.30.39
              vmid: 2002
              storage: "dell-pve-ssd-01"
              vcpus: 10
              memory: 4096
            k3s03:  
              ansible_host: 192.168.30.40
              vmid: 2003
              storage: "dell-pve-ssd-01"
              vcpus: 10
              memory: 4096
        node:
          hosts:
            k3s11: 
              ansible_host: 192.168.30.48
              vmid: 2011
              storage: "dell-pve-ssd-01"
              vcpus: 10
              memory: 16384
              iscsi_target: iqn.2000-01.com.synology:DiskStation4bay.k3s11.cc3fdd5a09f
            k3s12: 
              ansible_host: 192.168.30.49
              vmid: 2012
              storage: "dell-pve-ssd-01"
              vcpus: 10
              memory: 16384
              iscsi_target: iqn.2000-01.com.synology:DiskStation4bay.k3s12.cc3fdd5a09f
            k3s13: 
              ansible_host: 192.168.30.50
              vmid: 2013
              storage: "dell-pve-ssd-01"
              vcpus: 10
              memory: 16384
              iscsi_target: iqn.2000-01.com.synology:DiskStation4bay.k3s13.cc3fdd5a09f
```
This inventory resembles the original k3s-ansible repo for the ```site.yml``` deployment playbook to still function.

## deploy_k3s-vms.yml
For this to work that way I wanted I would need a way to iterate over my inventory while keeping the playbook run locally on the host. 
```yaml
---
- name: Prepare Proxmox VM Cluster
  hosts: localhost
  gather_facts: true

  vars_prompt:
    - name: node
      prompt: What Prox node do you want to deploy on?
      private: false
    - name: template_id
      prompt: What Prox template do you want to use (Prox Template VMID)?
      private: false

  roles:
    - role: deploy_proxmox_vm
      when: prox_api is defined
```
I figured while we are here lets ask a couple of question to gather a few more items needed to deploy vms via the Prox API. Using roles helps to keep the various tasks organized. I placed my API tasks in the ```./roles/deploy_proxmox_vm/tasks/main.yml```. Because I wanted to run these tasks from the localhost, I needed to figure out how to iterate over my existing inventory, so I figured this out while I tinkered around with it a bit. Notice in the playbook above that I am gathering facts on the localhost. This is needed so that I can pull in the inventory as a dictionary. Once we have that then we can use the ansible magic variables for our host_vars. This creates a variable of the hosts in the group 'k3s_cluster' and then I can look through the dictionary and pull out what I need from there, like host_ip.

```yaml
{% raw %}
---
- name: Include tasks for each host in k3s_cluster
  include_tasks: build_vms.yml
  loop: "{{ groups['k3s_cluster'] }}"
  loop_control:
    loop_var: target_host
  vars:
    host_ip: "{{ hostvars[target_host]['ansible_host'] }}"
{% endraw %}
```
### API Calls
The include_tasks is a way where you can loop over several tasks for a single "host" from your dictionary. From here I could now start to figure out all the API calls needed to build the VMs.

```yaml
{% raw %}
---
- name: Print hostname
  debug:
    msg: "Running tasks for {{ target_host }}"

- set_fact:
    vmid: "{{ hostvars[target_host]['vmid'] }}"
    storage: "{{ hostvars[target_host]['storage'] }}"
    vcpus: "{{ hostvars[target_host]['vcpus'] }}"
    memory: "{{ hostvars[target_host]['memory'] }}"

- name: Clone the Ubuntu VM Template for {{ target_host }}
  uri:
    url: "{{prox_api}}nodes/{{node}}/qemu/{{template_id}}/clone"
    method: POST
    headers:
      Authorization: "{{ prox_auth }}"
      Content-Type: "application/json"
    body_format: json
    body:
      newid: "{{ vmid }}"
      full: true
      name: "{{ target_host }}"
      storage: "{{ storage }}"
    validate_certs: no
  register: create_vm

- name: Wait for {{ target_host }} VM cloning to finish
  uri:
    url: "{{prox_api}}nodes/{{node}}/qemu/{{ vmid }}/status/current"
    method: GET
    headers:
      Authorization: "{{ prox_auth }}"
    validate_certs: no
  register: vm_status
  until: vm_status.json.data.lock is not defined
  retries: 100
  delay: 10
{% endraw %}
```
I set facts for the variables I need at the top, easier this way as I needed to reuse a couple more than once. I already created an VM template that makes use of cloud-init prior, so I will use this for my k3s cluster. Check out this post from [technotim](https://technotim.live/posts/cloud-init-cloud-image/) to learn more about how to make a template.

When cloning a VM it does take a minute or two so you will want to adjust accordingly. The wait task here verifies that the new VM has been created before moving on.

```yaml
{% raw %}
- set_fact: 
    vm_ip: "{{ host_ip }}/24"
- set_fact:
    vm_network: "{{ vm_ip | ansible.utils.ipaddr('network') }}"
- set_fact:
    vm_gateway: "{{ vm_network | ansible.utils.ipaddr('address') | ipmath(1) }}"

- name: Update {{ target_host }} vm IP to match the inventory
  uri:
    url: "{{ prox_api }}nodes/{{node}}/qemu/{{ vmid }}/config"
    method: PUT
    headers:
      Authorization: "{{ prox_auth }}"
      Content-Type: "application/json"
    body_format: json
    body:
      cores: "{{ vcpus|int }}"
      memory: "{{ memory|int }}"
      ipconfig0: "ip={{ vm_ip }},gw={{ vm_gateway }}"
      ciuser: "{{ ansible_user }}"
      cipassword: "{{ ansible_pass }}"
      nameserver: "{{ vm_gateway }}"
      sshkeys: "{{ ssh_key }}"
    validate_certs: no
  register: modify_vm
{% endraw %}
```
I needed a couple pieces of information to correctly generate the cloud-init file. So I use the set_fact and ipaddr module to do some subnet math. At the same time I updated the VM so that it is sized and configured correctly upon first boot.

```yaml
{% raw %}
- name: Expanding the bootdisk on {{ target_host }}
  uri:
    url: "{{ prox_api }}nodes/{{node}}/qemu/{{ vmid }}/resize"
    method: PUT
    headers:
      Authorization: "{{ prox_auth }}"
      Content-Type: "application/json"
    body_format: json
    body:
      disk: "scsi0"
      size: "+38G"
    validate_certs: no
  register: expand_bootdisk

- name: Start {{ target_host }}
  uri:
    url: "{{prox_api}}nodes/{{node}}/qemu/{{ vmid }}/status/start"
    method: POST
    headers:
      Authorization: "{{ prox_auth }}"
      Content-Type: "application/json"
    body: "{}"
    validate_certs: no
  register: start_vm
{% endraw %}
```
Finally I resize the VMs boot disk and start it up. This process loops over each host in your inventory until all tasks have been completed for each host.

After creating all of this I decided to add an additional task to my ```main.yml``` in my role to validate that the VMs have all booted and are reachable with my standard username and ssh key.

```yaml
{% raw %}
---
- name: Include tasks for each host in k3s_cluster
  include_tasks: build_vms.yml
  loop: "{{ groups['k3s_cluster'] }}"
  loop_control:
    loop_var: target_host
  vars:
    host_ip: "{{ hostvars[target_host]['ansible_host'] }}"

- name: Check if VMs are available
  ansible.builtin.wait_for:
    host: "{{ host_ip }}"
    port: 22
    state: started
    delay: 10
    timeout: 300
  loop: "{{ groups['k3s_cluster'] }}"
  loop_control:
    loop_var: target_host
  vars:
    host_ip: "{{ hostvars[target_host]['ansible_host'] }}"
{% endraw %}
```

After completing this part of my automation I can now run the ```site.yml``` from the original k3s-ansible repo and setup a clean cluster from scratch.

## Time to destroy all the VMs
If you want to tear everything down quickly and start all over you can do that too. I created a new playbook called ```destroy-k3s-vms.yml```

```yaml
---
- name: Prepare Proxmox VM Cluster
  hosts: localhost
  gather_facts: true

  vars_prompt:
    - name: node
      prompt: What Prox node do you want to remove the VMs from?
      private: false

  roles:
    - role: destroy_proxmox_vm
      when: prox_api is defined
```
Again I wanted to iterate over my inventory the same way I did creating the VMs. Before we do that we need to know what node in the Proxmox cluster the nodes are deployed on.

The main.yml:
```yaml
{% raw %}
---
- name: Include tasks for each host in k3s_cluster
  include_tasks: destroy_vms.yml
  loop: "{{ groups['k3s_cluster'] }}"
  loop_control:
    loop_var: target_host
  vars:
    host_ip: "{{ hostvars[target_host]['ansible_host'] }}"
{% endraw %}
```

destroy_vms.yml:
```yaml
{% raw %}
---
- name: Print hostname
  debug:
    msg: "Running tasks for {{ target_host }}"

- set_fact:
    vmid: "{{ hostvars[target_host]['vmid'] }}"

- name: Stop VM
  uri:
    url: "{{prox_api}}nodes/{{node}}/qemu/{{ vmid }}/status/stop"
    method: POST
    headers:
      Authorization: "{{ prox_auth }}"
      Content-Type: "application/json"
    body: "{}"
    validate_certs: no

- name: Check that VM has stopped
  uri:
    url: "{{prox_api}}nodes/{{node}}/qemu/{{ vmid }}/status/current"
    method: GET
    headers:
      Authorization: "{{ prox_auth }}"
      Content-Type: "application/json"
    validate_certs: no
  register: stopped_vm
  until: stopped_vm.json.data.status == "stopped"
  retries: 20
  delay: 5


- name: Destroy VM
  uri:
    url: "{{prox_api}}nodes/{{node}}/qemu/{{ vmid }}"
    method: DELETE
    headers:
      Authorization: "{{ prox_auth }}"
      Content-Type: "application/json"
    validate_certs: no
  register: delete_vm
  when: stopped_vm.json.data.status == "stopped"
{% endraw %}
```
It is as easy as stopping the VM and deleting the VM. You need to make sure that the VM has stopped before you can delete the VM so this middle task just validates that has happened before performing the delete task.