---
title: Nautobot Workshop Blog Series - Part 3 Adding Devices to Nautobot via Ansible
date: 2025-06-26 09:00:00 -6
categories: [Nautobot, Ansible, Automation]
tags: [NetworkAutomation, NetworkSourceOfTruth, nautobot, AutomationPlatform, NautobotTutorials]
image:
  path: /assets/img/nautobot_workshop/light_title_image-50.webp
---

# Nautobot Workshop Blog Series

**"Nautobot Workshop"** is a blog series that guides you through building a fully automated network lab using Nautobot, Containerlab, and Docker. Starting from environment setup on Ubuntu, each post will walk through deploying Nautobot with `nautobot-docker-compose`, modeling network topologies with Containerlab and vrnetlab-based routers, and populating Nautobot with real device data using Ansible.

You'll also learn how to:
- Use Nautobot’s GraphQL API for dynamic inventory
- Generate device configurations with Jinja2 templates
- Enforce configuration compliance using the Golden Config plugin

This series is ideal for network engineers looking to integrate source of truth, automation, and lab simulation into a streamlined workflow.

---

## Part 3: Adding Devices to Nautobot via Ansible

In this post, we will accomplish the following:

1. Create a Python virtual environment to manage our Ansible playbooks.
2. Create a file that contains all of the necessary elements for our Nautobot Source of Truth (NSoT).
3. Create a playbook and tasks that will populate our NSoT.

---

### 🐍 Creating Python Environment

In your `Nautobot-Workshop` folder, create a new folder called `ansible-lab`.

```bash
cd Nautobot-Workshop
mkdir ansible-lab
cd ansible-lab
sudo apt update
sudo apt install -y python3-venv
python3 -m venv .ansible
source .ansible/bin/activate
```

Once in the virtual environment, install Ansible and Pynautobot:

```bash
pip install ansible pynautobot
touch ansible.cfg
```

Use this [ansible.cfg](https://github.com/byrn-baker/Nautobot-Workshop/blob/main/ansible-lab/ansible.cfg) as a reference.

Install the Nautobot Ansible collection:

```bash
ansible-galaxy collection install networktocode.nautobot
```

> Having the Nautobot Ansible collection in your project folder helps with portability. When you need to look at an example for a module, they exist in:
> `ansible-lab/ansible_collections/networktocode/nautobot/plugins/modules`
{: .prompt-tip }

Start your Nautobot Docker instance from a separate terminal if it's not running:

```bash
cd nautobot-docker-compose
invoke debug
```

> Using a Python virtual environment isolates your project’s dependencies, ensuring compatibility and reproducibility across systems.
{: .prompt-tip }

---

### 🧾 Creating Ansible Playbook and Tasks

Create your base inventory and playbook files:

```bash
touch inventory/group_vars/all.yml
touch pb.build-lab.yml
```

`all.yml`:

```yaml
nb_url: "<your-url-here>"
nb_token: "<your-token-here>"
```

> To create an API key in Nautobot, navigate to the admin panel and click your profile. You'll find a link for "API Tokens" where you can generate a token.
{: .prompt-tip }

Now create the role folder and task structure:

```bash
mkdir -p roles/load_nautobot/tasks
touch roles/load_nautobot/tasks/main.yml
```

Expected structure:

```
.
├── pb.build-lab.yml
├── inventory
│   └── group_vars
│       └── all.yml
└── roles
    └── load_nautobot
        └── tasks
            └── main.yml
```

---

### 📂 Creating the Nautobot Data Files

In your root project directory, create the following data files:

- `nautobot-data/extensible_data.yml`
- `nautobot-data/organization_data.yml`
- `nautobot-data/ipam_data.yml`
- `nautobot-data/nautobot_devices.yml`

These files will contain everything needed to populate Nautobot and build the topology.

| Section                                      | Nautobot Functionality Unlocked                               |
|---------------------------------------------|---------------------------------------------------------------|
| `location_types`, `locations`               | Physical/logical hierarchy, mapping, grouping                 |
| `roles`                                     | Automation, compliance, filtering by function                 |
| `manufacturers`, `device_types`, `platforms`| Inventory modeling, config templating, plugin filtering       |
| `software_versions`                         | OS version tracking, Nornir group matching                    |
| `prefixes`, `ip_addresses`                  | IPAM, interface mapping, VRF/subnet usage                     |
| `devices`, `interfaces`                     | Topology, inventory, config generation, connection validation |

View these sample files on GitHub:

- [extensible_data.yml](https://github.com/byrn-baker/Nautobot-Workshop/blob/main/ansible-lab/nautobot-data/extensible_data.yml)
- [organization_data.yml](https://github.com/byrn-baker/Nautobot-Workshop/blob/main/ansible-lab/nautobot-data/origanization_data.yml)
- [ipam_data.yml](https://github.com/byrn-baker/Nautobot-Workshop/blob/main/ansible-lab/nautobot-data/ipam_data.yml)
- [nautobot_devices.yml](https://github.com/byrn-baker/Nautobot-Workshop/blob/main/ansible-lab/nautobot-data/nautobot_devices.yml)

---

## 🛠️ Managing Nautobot with Ansible

### 🔗 `main.yml` (Playbook Structure)

This top-level playbook includes tasks in logical order:

1. `extensibility.yml`: Define custom fields and allowed values
2. `organizational.yml`: Build hierarchy with locations and roles
3. `ipam.yml`: Configure IP space, prefixes, addresses
4. `devices.yml`: Define devices, assign platforms, IPs, and interfaces

---

### 📦 `extensibility.yml` – Custom Fields & Metadata

**Create Custom Fields**
- Module: `networktocode.nautobot.custom_field`

**Create Choices for Custom Fields**
- Module: `networktocode.nautobot.custom_field_choice`

---

### 🏢 `organizational.yml` – Location and Role Modeling

**Create Location Types**
- Module: `networktocode.nautobot.location_type`

**Create Locations**
- Module: `networktocode.nautobot.location`

**Create Roles**
- Module: `networktocode.nautobot.role`

---

### 🌐 `ipam.yml` – IP Address Management

**Create Namespaces**
- Module: `networktocode.nautobot.namespace`

**Create VRFs**
- Module: `networktocode.nautobot.vrf`

**Create Prefixes**
- Module: `networktocode.nautobot.prefix`

**Create IP Addresses**
- Module: `networktocode.nautobot.ip_address`

**Tag Loopbacks**
- Logic: Tag `/32` or `/128` IPs with `loopback` role

---

### 🖥️ `devices.yml` – Device & Network Provisioning

**Create Manufacturers**
- Module: `networktocode.nautobot.manufacturer`

**Create Device Types**
- Module: `networktocode.nautobot.device_type`

**Create Platforms**
- Module: `networktocode.nautobot.platform`

**Create Software Versions**
- Module: `networktocode.nautobot.software_version`

**Create Devices**
- Module: `networktocode.nautobot.device`

**Assign Software to Devices**
- Logic: Use `uri` module with PATCH to assign software versions

**Create Interfaces**
- Module: `networktocode.nautobot.device_interface`

**Assign IPs to Interfaces**
- Module: `networktocode.nautobot.ip_address_to_interface`

---

Stay tuned for Part 4 where we'll use this data to dynamically generate configuration templates and validate configuration compliance with Golden Config!

