---
title: Lesson 2 - Creating the inventory yaml file
date: 2021-07-31 12:00:00 -500
categories: [AnsibleWorkshop]
tags: [ansible,ansibleworkshop]
image:
  path: /assets/img/ansible_workshop/ansible_workshop.webp
---

## Section 2: Creating the inventory yaml file
{% include embed/youtube.html id='qmLRvnriQLY' %}
[Ansible inventory Documentation can be found here](https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html#) 
We will be constructing our inventory file with yaml format. Each pod has a bootstrap configuration that includes IP addressing to each node. Your control nodes (Jumpbox VM) has the /etc/hosts file built and each node has been assigned a hostname and an IP address.
Here are the groupings we will be building in our inventory file.
1. Routers
    *   podxr1
2. Core Switches
    *   podxsw1
    *   podxsw2
3. Access Switches
    *   podxsw3

The inventory file is what Ansible will use to connect to each of the managed hosts. We can assign each host to a group and each group to a parent group. Our file structure example is below along with the inventory.yml file.
```
inventory/
    inventory.yml
    group_vars/
        all/
            all.yml
    host_vars/
        podxr1/
        podxsw1/
        podxsw2/
        podxsw3/
```
inventory.yml - Our inventory file will use groupings of "all". "pod1" will be a child group of the parent "all". "routers", "core_switches" and "access_switches" will all be children of the parent group "pod1". 
```yaml
---
all:
  children:
    pod1:
      children:
        routers:
          hosts:
            pod1r1:    
        core_switches:
          hosts:
            pod1sw1:
            pod1sw2:
        access_switches:
          hosts:
            pod1sw3:
```
Each host will be defined under the lower groupings (routers, core_switches, and access_switches). We can store variables in our plays in these folders, including sensitive information like passwords. In this workshop, we will keep information like usernames and passwords under the group_vars/all folder in a file called "all.yml" If you were to have devices or device groups that did not use the same password, then you could create a file of the device name under the host_vars/{{ device_name }} folder. In this workshop all devices share login and OS. If you want to learn more about encrypting files with ansible use the ansible docs on [Ansible Vault](https://docs.ansible.com/ansible/latest/user_guide/vault.html)
```yaml
---
###########################################
# Stored variables for login and device OS
###########################################

ansible_password: Labuser!23
ansible_user: pod1
ansible_network_os: ios
```