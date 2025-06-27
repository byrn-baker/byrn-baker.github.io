---
title: Nautobot Workshop Blog Series - Part 4 Building ContainerLab topology from the Nautobot Inventory
date: 2025-06-26 9:00:00 -6
categories: [Nautobot,Ansible,Automtation]
tags: [NetworkAutomation,NetworkSourceOfTruth,nautobot,AutomationPlatform,NautobotTutorials]
image:
  path: /assets/img/nautobot_workshop/light_title_image-50.webp
---

# Nautobot Workshop Blog Series

**Nautobot Workshop** is a hands-on blog series for building a fully automated network lab using Nautobot, Containerlab, and Docker. Starting with a basic Ubuntu setup, each post walks through:

- Deploying Nautobot via `nautobot-docker-compose`
- Modeling topologies with Containerlab and vrnetlab routers
- Populating Nautobot with real device data using Ansible
- Generating configurations with Jinja2 templates
- Enforcing compliance with the Golden Config plugin
- Leveraging Nautobot’s GraphQL API for dynamic inventory

This series is perfect for network engineers aiming to combine source of truth, automation, and simulation in a streamlined workflow.

🚀 All project files are available in this [GitHub repo](https://github.com/byrn-baker/Nautobot-Workshop)


## Part 4: Building ContainerLab topology from the Nautobot Inventory
<div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
  <iframe src="https://www.youtube.com/embed/_euaOmjJimw" 
          frameborder="0" 
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
          allowfullscreen 
          style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
  </iframe>
</div>

[▶️ Watch the video](https://youtu.be/_euaOmjJimw)

### Using GraphQL and Ansible
The easiest way to pull data from Nautobot that gathers all data you might require for a Jinja2 template using Ansible is the GraphQL query module. We can pull all devices, their interfaces, and connected interface details with a single query and use those variables to populate a template.

Nautobot has a GraphQL sandbox that can be used to test queries, and provide helpful auto completion of fields that might be available to models you want data returned for. This can be easily accessed by using the GraphQL link on the bottom right of any page in the Nautobot App.

<img src="/assets/img/nautobot_workshop/graphql.webp" alt="">
<img src="/assets/img/nautobot_workshop/graphql2.webp" alt="">

In this example above we use a simple json like structure for the query

```graphql
{
  devices {
    name
  }
}
```

Which produces the output in json format

```json
{
  "data": {
    "devices": [
      {
        "name": "CE1"
      },
      {
        "name": "CE2"
      },
      {
        "name": "East-Leaf01"
      },
      {
        "name": "East-Leaf02"
      },
      {
        "name": "East-Spine01"
      },
      {
        "name": "East-Spine02"
      },
      {
        "name": "P1"
      },
      {
        "name": "P2"
      },
      {
        "name": "P3"
      },
      {
        "name": "P4"
      },
      {
        "name": "PE1"
      },
      {
        "name": "PE2"
      },
      {
        "name": "PE3"
      },
      {
        "name": "RR1"
      },
      {
        "name": "West-Leaf01"
      },
      {
        "name": "West-Leaf02"
      },
      {
        "name": "West-Spine01"
      },
      {
        "name": "West-Spine02"
      },
      {
        "name": "clabbr220"
      }
    ]
  }
}
```

We can add filtering to the devices we want to query

```graphql
{
  devices (role: "Provider Router") {
    name
  }
}
```

The filtered results
```json
{
  "data": {
    "devices": [
      {
        "name": "P1"
      },
      {
        "name": "P2"
      },
      {
        "name": "P3"
      },
      {
        "name": "P4"
      }
    ]
  }
}
```

Because this sandbox will only have the devices we need for our lab topology we will not require any filters at this time. However we do want specific details on the devices and their interfaces so that we can properly provision and connect the virtualized nodes in our topology.

First lets create add to our Ansible Playbook from the previous post. We will comment out the "load_nautobot" role because this should already have been done in the previous task, we will leave it here because we want this to be a repeatable process that can be run inside a new sandbox at anytime.

```pb.build-lab.yml```:
```yaml
---
- name: Populate Nautobot & Generate Containerlab topology from Nautobot
  hosts: localhost
  gather_facts: false

  roles:
    # - load_nautobot
    - build_clab_topology
```

Under your roles folder add a new folder for the role, create a ```main.yml``` under the task folder and a ```containerlab_topology.j2``` under the templates folder.

```bash
(.ansible) ubuntu@containerlabs:~/Nautobot-Workshop/ansible-lab$ mkdir -p roles/build_clab_topology/tasks
(.ansible) ubuntu@containerlabs:~/Nautobot-Workshop/ansible-lab$ touch roles/build_clab_topology/tasks/main.yml
(.ansible) ubuntu@containerlabs:~/Nautobot-Workshop/ansible-lab$ mkdir -p roles/build_clab_topology/templates/
(.ansible) ubuntu@containerlabs:~/Nautobot-Workshop/ansible-lab$ touch roles/build_clab_topology/templates/containerlab_topology.j2
(.ansible) ubuntu@containerlabs:~/Nautobot-Workshop/ansible-lab$ tree roles/
roles/
├── build_clab_topology
│   ├── tasks
│   │   └── main.yml
│   └── templates
│       └── containerlab_topology.j2
└── load_nautobot
    └── tasks
        └── main.yml

6 directories, 3 files
```

In our ```main.yml``` under the tasks folder we will build the tasks to perform the GraphQL query and then template the output into a new YAML files called ```initial_configs.j2```, and ```containerlab-topology.yml```. Beisdes the device name and interfaces, the model, platform and software version, and connected interfaces are important because we will use those variable in our Jinja template that builds the topology.

main.yml:
```yaml
---
- name: Get data from Nautobot
  networktocode.nautobot.query_graphql:
    url: "{{ nb_url }}"
    token: "{{ nb_token }}"
    validate_certs: false
    query: |
      {
        devices {
          name
          primary_ip4 {
            address
            host
          }
          device_type {
            model
            manufacturer{
              name
            }
          }
          platform{
            name
          }
          software_version {
          version
          }
          interfaces {
            name
            mgmt_only
            ip_addresses{
              address
            }
            connected_interface {
              name
              device {
                name
              }
            }
          }
        }
      }
  register: "nb_devices"

- name: Create initial Configs for each device
  template:
    src: "initial_configs.j2"
    dest: "~/labs/startup-configs/{{ item.name }}.txt"
  loop: "{{ nb_devices.data.devices }}"
  when: item.device_type.model == 'ceos'

- name: Render Containerlab topology
  template:
    src: "containerlab_topology.j2"
    dest: "~/labs/nautobot-workshop-topology.clab.yml"
```

Update the two templates ```tempaltes/initial_configs.j2```, and ```templates/containerlab_topology.j2``` files with the following

initial_configs.j2:
```jinja
{%raw%}
#jinja2: lstrip_blocks: True, trim_blocks: True
{% if item.device_type.model == "ceos" %}
no aaa root
!
username admin privilege 15 role network-admin secret 0 admin
!
management api http-commands
   vrf clab-mgmt
      no shutdown
   protocol http
   protocol https
   no shutdown
!
no service interface inactive port-id allocation disabled
!
transceiver qsfp default-mode 4x10G
!
service routing protocols model multi-agent
!
vrf instance clab-mgmt
   description clab-mgmt
!
hostname {{ item.name }}
!
spanning-tree mode mstp
!
system l1
   unsupported speed action error
   unsupported error-correction action error
!
management api gnmi
   transport grpc default
!
management api netconf
   transport ssh default
!
{% for int in item.interfaces if int.mgmt_only == true %}
interface {{ int.name}}
 vrf forwarding clab-mgmt
 ip address {{ int.ip_addresses[0].address }}
!
{% endfor %}
!
ip routing
!
ip routing vrf clab-mgmt
!
{% for int in item.interfaces if int.mgmt_only == true %}
ip route vrf clab-mgmt 0.0.0.0 0.0.0.0 {{ int.name }} 192.168.220.1
{% endfor %}
{% endif %}
{%endraw%}
```

containerlab_topology.j2`:
```jinja
{%raw%}
#jinja2: lstrip_blocks: True, trim_blocks: True
{% set delay_targets = ["vrnetlab/vr-xrv9k", "vrnetlab/n9kv"] %}
{% set global_delay = [0] %}

name: nautobot_workshop
mgmt:
  network: clab-mgmt
  ipv4-subnet: 192.168.220.0/24

topology:
  nodes:
{% for device in nb_devices["data"]["devices"] %}
  {% if device.software_version is not none and device.platform is not none %}
    {% set model = device.device_type.model | lower %}
    {% if "ceos" in model %}
      {% set kind = "ceos" %}
      {% set image = "ceos:" ~ device.software_version.version %}
    {% else %}
      {% set kind = (device.device_type.manufacturer.name ~ "_" ~ device.device_type.model) | lower %}
      {% set image_base = "vrnetlab/" ~ kind %}
      {% set image = image_base ~ ":" ~ device.software_version.version %}
    {% endif %}
    {{ device.name }}:
      kind: {{ kind }}
      image: {{ image }}
      mgmt-ipv4: {{ device.primary_ip4.address | ansible.utils.ipaddr('address') }}
      {% if "ceos" in model %}
      startup-config: ./startup-configs/{{ device.name }}.txt
      {% endif %}
      {% if image_base is defined and image_base in delay_targets %}
      startup-delay: {{ global_delay[0] * 30 }}
      {% set _ = global_delay.append(global_delay.pop() + 1) %}
      {% endif %}
      env:
        HOSTNAME: {{ device.name }}
  {% endif %}
{% endfor %}

  links:
{% set ns = {'seen': []} %}
{% for device in nb_devices["data"]["devices"] %}
  {% if device.software_version is not none and device.platform is not none %}
    {% for iface in device.interfaces %}
      {% if iface.connected_interface %}
        {% set local = device.name ~ ':' ~ iface.name %}
        {% set remote = iface.connected_interface.device.name ~ ':' ~ iface.connected_interface.name %}
        {% set endpoints = [local, remote]|sort %}
        {% if endpoints not in ns.seen %}
          - endpoints: ["{{ endpoints[0] }}", "{{ endpoints[1] }}"]
          {% set _ = ns.seen.append(endpoints) %}
        {% endif %}
      {% endif %}
    {% endfor %}
  {% endif %}
{% endfor %}
{%endraw%}
```

Recapping:
- This Ansible playbook automates the process of generating a Containerlab topology and initial startup configurations for devices managed in Nautobot. The workflow begins with a GraphQL query to Nautobot, retrieving a rich dataset for all devices, including their names, models, platforms, software versions, IP addresses, and interface connections. This data is stored in the nb_devices variable and used in two subsequent templating tasks. The first template (initial_configs.j2) builds a startup configuration for each ceos device, setting up management VRFs, IP addressing, and routing. The second template (containerlab_topology.j2) dynamically constructs the entire Containerlab topology YAML by iterating over the devices and their connections. It uses device metadata to set the appropriate kind and image, applies startup configs to ceos nodes, and adds startup delays for specific image types. Additionally, the link definitions are intelligently deduplicated using a seen list to ensure that each point-to-point link is only rendered once. Together, these tasks allow the automation of network lab deployment using Nautobot as a source of truth.

I am using a secondary interface on my VM for my container lab deployment. This allows me to dedicate an additional network connection (eth1) on my Ubuntu host specifically for my lab’s management VLAN.

In my netplan configuration, I’ve defined this second interface (eth1) with no IP addressing on the host. I’ve also created a bridge called clab-mgmt and added eth1 as its member interface. In my Containerlab topology file, I reference this bridge and connect the management interfaces of my virtual devices to it.

The management IP addresses will be assigned within the initial configuration of each virtual node when they boot up, not on the Ubuntu host itself.

```yaml
network:
  version: 2
  ethernets:
    eth1:
      match:
        macaddress: bc:24:11:35:23:90
      dhcp4: false
      dhcp6: false
 
  bridges:
    clab-mgmt:
      interfaces: [eth1]
      parameters:
        stp: false
        forward-delay: 0
```

Once you have the secondary interface configured you will need a docker bridge network created as well

```bash
$ docker network create \
  --driver=bridge \
  --subnet=192.168.220.0/24 \
  --gateway=192.168.220.1 \
  --opt "com.docker.network.bridge.name"="clab-mgmt" \
  clab-mgmt
```

With the topology file built we can start the containerlab up

```bash
ubuntu@containerlabs:~/labs$ containerlab deploy
04:26:46 INFO Containerlab started version=0.68.0
04:26:46 INFO Parsing & checking topology file=nautobot-workshop-topology.clab.yml
04:26:46 INFO Destroying lab name=nautobot_workshop
04:26:47 INFO Removed container name=clab-nautobot_workshop-CE1
04:26:47 INFO Removed container name=clab-nautobot_workshop-East-Spine02
04:26:47 INFO Removed container name=clab-nautobot_workshop-East-Leaf01
04:26:47 INFO Removed container name=clab-nautobot_workshop-RR1
04:26:47 INFO Removed container name=clab-nautobot_workshop-P2
04:26:47 INFO Removed container name=clab-nautobot_workshop-CE2
04:26:47 INFO Removed container name=clab-nautobot_workshop-P1
04:26:48 INFO Removed container name=clab-nautobot_workshop-West-Leaf01
04:26:48 INFO Removed container name=clab-nautobot_workshop-East-Spine01
04:26:48 INFO Removed container name=clab-nautobot_workshop-P4
04:26:48 INFO Removed container name=clab-nautobot_workshop-PE2
04:26:48 INFO Removed container name=clab-nautobot_workshop-West-Leaf02
04:26:48 INFO Removed container name=clab-nautobot_workshop-PE1
04:26:48 INFO Removed container name=clab-nautobot_workshop-West-Spine01
04:26:48 INFO Removed container name=clab-nautobot_workshop-P3
04:26:48 INFO Removed container name=clab-nautobot_workshop-West-Spine02
04:26:48 INFO Removed container name=clab-nautobot_workshop-PE3
04:26:48 INFO Removed container name=clab-nautobot_workshop-East-Leaf02
04:26:48 INFO Removing host entries path=/etc/hosts
04:26:48 INFO Removing SSH config path=/etc/ssh/ssh_config.d/clab-nautobot_workshop.conf
04:26:48 INFO Removing directory path=/home/ubuntu/labs/clab-nautobot_workshop
04:26:48 INFO Creating lab directory path=/home/ubuntu/labs/clab-nautobot_workshop
04:26:49 INFO Creating container name=West-Spine02
04:26:49 INFO Creating container name=PE2
04:26:49 INFO Creating container name=East-Leaf02
04:26:49 INFO Creating container name=PE3
04:26:49 INFO Creating container name=P2
04:26:49 INFO Creating container name=RR1
04:26:49 INFO Creating container name=East-Spine01
04:26:49 INFO Creating container name=P3
04:26:49 INFO Creating container name=West-Spine01
04:26:49 INFO Creating container name=East-Leaf01
04:26:49 INFO Creating container name=West-Leaf01
04:26:49 INFO Creating container name=West-Leaf02
04:26:49 INFO Creating container name=CE2
04:26:49 INFO Creating container name=CE1
04:26:49 INFO Creating container name=P1
04:26:49 INFO Creating container name=PE1
04:26:49 INFO Creating container name=P4
04:26:49 INFO Creating container name=East-Spine02
04:26:50 INFO Running postdeploy actions for Cisco IOL 'PE2' node
04:26:50 INFO Running postdeploy actions for Cisco IOL 'CE1' node
04:26:50 INFO Created link: CE1:eth2 (Ethernet0/2) ▪┄┄▪ West-Spine01:eth7
04:26:50 INFO Running postdeploy actions for Arista cEOS 'East-Leaf02' node
04:26:51 INFO Running postdeploy actions for Arista cEOS 'West-Spine01' node
04:26:51 INFO Running postdeploy actions for Arista cEOS 'East-Leaf01' node
04:26:51 INFO Created link: West-Leaf01:eth1 ▪┄┄▪ West-Spine01:eth1
04:26:51 INFO Created link: P2:eth3 (Ethernet0/3) ▪┄┄▪ RR1:eth2 (Ethernet0/2)
04:26:51 INFO Running postdeploy actions for Cisco IOL 'RR1' node
04:26:51 INFO Running postdeploy actions for Cisco IOL 'P2' node
04:26:51 INFO Running postdeploy actions for Arista cEOS 'West-Leaf01' node
04:26:51 INFO Created link: P2:eth2 (Ethernet0/2) ▪┄┄▪ P4:eth2 (Ethernet0/2)
04:26:51 INFO Created link: P1:eth1 (Ethernet0/1) ▪┄┄▪ P2:eth1 (Ethernet0/1)
04:26:51 INFO Created link: East-Leaf01:eth2 ▪┄┄▪ East-Spine02:eth1
04:26:51 INFO Created link: P3:eth1 (Ethernet0/1) ▪┄┄▪ P4:eth1 (Ethernet0/1)
04:26:51 INFO Created link: P3:eth4 (Ethernet1/0) ▪┄┄▪ PE2:eth1 (Ethernet0/1)
04:26:51 INFO Running postdeploy actions for Cisco IOL 'P3' node
04:26:51 INFO Created link: P1:eth2 (Ethernet0/2) ▪┄┄▪ P3:eth2 (Ethernet0/2)
04:26:51 INFO Created link: West-Leaf02:eth1 ▪┄┄▪ West-Spine01:eth2
04:26:51 INFO Created link: East-Leaf02:eth2 ▪┄┄▪ East-Spine02:eth2
04:26:51 INFO Running postdeploy actions for Arista cEOS 'East-Spine02' node
04:26:51 INFO Created link: CE2:eth3 (Ethernet0/3) ▪┄┄▪ East-Spine02:eth7
04:26:51 INFO Running postdeploy actions for Cisco IOL 'CE2' node
04:26:51 INFO Created link: P4:eth3 (Ethernet0/3) ▪┄┄▪ PE2:eth2 (Ethernet0/2)
04:26:51 INFO Created link: P1:eth3 (Ethernet0/3) ▪┄┄▪ RR1:eth1 (Ethernet0/1)
04:26:51 INFO Running postdeploy actions for Arista cEOS 'West-Leaf02' node
04:26:51 INFO Created link: CE1:eth1 (Ethernet0/1) ▪┄┄▪ PE1:eth3 (Ethernet0/3)
04:26:51 INFO Running postdeploy actions for Cisco IOL 'P4' node
04:26:51 INFO Running postdeploy actions for Cisco IOL 'P1' node
04:26:51 INFO Created link: P1:eth4 (Ethernet1/0) ▪┄┄▪ PE1:eth1 (Ethernet0/1)
04:26:51 INFO Created link: P3:eth3 (Ethernet0/3) ▪┄┄▪ PE1:eth2 (Ethernet0/2)
04:26:51 INFO Running postdeploy actions for Cisco IOL 'PE1' node
04:26:52 INFO Created link: CE2:eth2 (Ethernet0/2) ▪┄┄▪ East-Spine01:eth7
04:26:52 INFO Created link: East-Leaf01:eth1 ▪┄┄▪ East-Spine01:eth1
04:26:52 INFO Created link: East-Leaf02:eth1 ▪┄┄▪ East-Spine01:eth2
04:26:52 INFO Running postdeploy actions for Arista cEOS 'East-Spine01' node
04:26:52 INFO Created link: CE2:eth1 (Ethernet0/1) ▪┄┄▪ PE3:eth3 (Ethernet0/3)
04:26:52 INFO Created link: P2:eth4 (Ethernet1/0) ▪┄┄▪ PE3:eth1 (Ethernet0/1)
04:26:52 INFO Created link: P4:eth4 (Ethernet1/0) ▪┄┄▪ PE3:eth2 (Ethernet0/2)
04:26:52 INFO Running postdeploy actions for Cisco IOL 'PE3' node
04:26:52 INFO Created link: CE1:eth3 (Ethernet0/3) ▪┄┄▪ West-Spine02:eth7
04:26:52 INFO Created link: West-Leaf01:eth2 ▪┄┄▪ West-Spine02:eth1
04:26:52 INFO Created link: West-Leaf02:eth2 ▪┄┄▪ West-Spine02:eth2
04:26:52 INFO Running postdeploy actions for Arista cEOS 'West-Spine02' node
04:28:21 INFO Adding host entries path=/etc/hosts
04:28:22 INFO Adding SSH config for nodes path=/etc/ssh/ssh_config.d/clab-nautobot_workshop.conf
╭─────────────────────────────────────┬─────────────────────────────┬─────────┬────────────────╮
│                 Name                │          Kind/Image         │  State  │ IPv4/6 Address │
├─────────────────────────────────────┼─────────────────────────────┼─────────┼────────────────┤
│ clab-nautobot_workshop-CE1          │ cisco_iol                   │ running │ 192.168.220.9  │
│                                     │ vrnetlab/cisco_iol:17.12.01 │         │ N/A            │
├─────────────────────────────────────┼─────────────────────────────┼─────────┼────────────────┤
│ clab-nautobot_workshop-CE2          │ cisco_iol                   │ running │ 192.168.220.10 │
│                                     │ vrnetlab/cisco_iol:17.12.01 │         │ N/A            │
├─────────────────────────────────────┼─────────────────────────────┼─────────┼────────────────┤
│ clab-nautobot_workshop-East-Leaf01  │ ceos                        │ running │ 192.168.220.18 │
│                                     │ ceos:4.34.0F                │         │ N/A            │
├─────────────────────────────────────┼─────────────────────────────┼─────────┼────────────────┤
│ clab-nautobot_workshop-East-Leaf02  │ ceos                        │ running │ 192.168.220.19 │
│                                     │ ceos:4.34.0F                │         │ N/A            │
├─────────────────────────────────────┼─────────────────────────────┼─────────┼────────────────┤
│ clab-nautobot_workshop-East-Spine01 │ ceos                        │ running │ 192.168.220.16 │
│                                     │ ceos:4.34.0F                │         │ N/A            │
├─────────────────────────────────────┼─────────────────────────────┼─────────┼────────────────┤
│ clab-nautobot_workshop-East-Spine02 │ ceos                        │ running │ 192.168.220.17 │
│                                     │ ceos:4.34.0F                │         │ N/A            │
├─────────────────────────────────────┼─────────────────────────────┼─────────┼────────────────┤
│ clab-nautobot_workshop-P1           │ cisco_iol                   │ running │ 192.168.220.2  │
│                                     │ vrnetlab/cisco_iol:17.12.01 │         │ N/A            │
├─────────────────────────────────────┼─────────────────────────────┼─────────┼────────────────┤
│ clab-nautobot_workshop-P2           │ cisco_iol                   │ running │ 192.168.220.3  │
│                                     │ vrnetlab/cisco_iol:17.12.01 │         │ N/A            │
├─────────────────────────────────────┼─────────────────────────────┼─────────┼────────────────┤
│ clab-nautobot_workshop-P3           │ cisco_iol                   │ running │ 192.168.220.4  │
│                                     │ vrnetlab/cisco_iol:17.12.01 │         │ N/A            │
├─────────────────────────────────────┼─────────────────────────────┼─────────┼────────────────┤
│ clab-nautobot_workshop-P4           │ cisco_iol                   │ running │ 192.168.220.5  │
│                                     │ vrnetlab/cisco_iol:17.12.01 │         │ N/A            │
├─────────────────────────────────────┼─────────────────────────────┼─────────┼────────────────┤
│ clab-nautobot_workshop-PE1          │ cisco_iol                   │ running │ 192.168.220.6  │
│                                     │ vrnetlab/cisco_iol:17.12.01 │         │ N/A            │
├─────────────────────────────────────┼─────────────────────────────┼─────────┼────────────────┤
│ clab-nautobot_workshop-PE2          │ cisco_iol                   │ running │ 192.168.220.7  │
│                                     │ vrnetlab/cisco_iol:17.12.01 │         │ N/A            │
├─────────────────────────────────────┼─────────────────────────────┼─────────┼────────────────┤
│ clab-nautobot_workshop-PE3          │ cisco_iol                   │ running │ 192.168.220.8  │
│                                     │ vrnetlab/cisco_iol:17.12.01 │         │ N/A            │
├─────────────────────────────────────┼─────────────────────────────┼─────────┼────────────────┤
│ clab-nautobot_workshop-RR1          │ cisco_iol                   │ running │ 192.168.220.11 │
│                                     │ vrnetlab/cisco_iol:17.12.01 │         │ N/A            │
├─────────────────────────────────────┼─────────────────────────────┼─────────┼────────────────┤
│ clab-nautobot_workshop-West-Leaf01  │ ceos                        │ running │ 192.168.220.14 │
│                                     │ ceos:4.34.0F                │         │ N/A            │
├─────────────────────────────────────┼─────────────────────────────┼─────────┼────────────────┤
│ clab-nautobot_workshop-West-Leaf02  │ ceos                        │ running │ 192.168.220.15 │
│                                     │ ceos:4.34.0F                │         │ N/A            │
├─────────────────────────────────────┼─────────────────────────────┼─────────┼────────────────┤
│ clab-nautobot_workshop-West-Spine01 │ ceos                        │ running │ 192.168.220.12 │
│                                     │ ceos:4.34.0F                │         │ N/A            │
├─────────────────────────────────────┼─────────────────────────────┼─────────┼────────────────┤
│ clab-nautobot_workshop-West-Spine02 │ ceos                        │ running │ 192.168.220.13 │
│                                     │ ceos:4.34.0F                │         │ N/A            │
╰─────────────────────────────────────┴─────────────────────────────┴─────────┴────────────────╯
```

You should now be able to ping the MGMT interfaces on all of you virtual routers. We used 192.168.220.x and you should be able to ping any of the assigned IPs of you virtual routers.

```bash
$ ping 192.168.220.3
PING 192.168.220.3 (192.168.220.3) 56(84) bytes of data.
64 bytes from 192.168.220.3: icmp_seq=1 ttl=253 time=7.27 ms
64 bytes from 192.168.220.3: icmp_seq=2 ttl=253 time=1.65 ms
```

## Conclusion
With Part 4 complete, we’ve successfully automated the generation of a fully connected Containerlab topology using Nautobot as the dynamic source of truth. By leveraging GraphQL, Ansible, and Jinja2, we've demonstrated how to extract structured device and interface data directly from Nautobot and translate it into a deployable lab environment—bridging the gap between inventory and infrastructure. This approach not only accelerates lab provisioning but ensures consistency and accuracy across virtual topologies. In the next post, we’ll take it a step further by using Ansible dynamic inventory to create configurations and push them to devices. Stay tuned as we continue building a production-grade automated lab workflow.
