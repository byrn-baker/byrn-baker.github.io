---
title: Lesson 1 - Install Python3, pip3 and Ansible
date: 2021-07-30 12:00:00 -500
categories: [AnsibleWorkshop]
tags: [ansible,ansibleworkshop]
image:
  path: /assets/img/ansible_workshop/ansible_workshop.webp
---

Open the terminal window. type pwd in the terminal and it should be showing you your home directory (/home/lab_user1) for example.
In the terminal window type the below commands one at a time.
```bash
mkdir Ansible_Workshop && cd Ansible_Workshop
sudo apt update
sudo apt install python3-pip python3-venv
```
Now we will create a new python virtual environment
```bash
python3 -m venv .venv
```
Activate the virtual environment
```bash
source .venv/bin/activate
```
Now that we are inside the python environment we can install packages here that will not affect our system python environment. This allows you to use different versions of ansible or other python packages that can potentially conflict. This also helps make your Ansible playbooks portable.

Now run the below command in terminal to install the packages
```bash
pip3 install wheel ansible pyats genie colorama 
```
Now that we have ansible installed we need to add a module that will help us connect and configure our topology
```bash
ansible-galaxy collection install cisco.ios clay584.genie
```