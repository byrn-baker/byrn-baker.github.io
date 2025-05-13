---
title: Nautobot Workshop Blog Series - Part 4 Building ContainerLab topology from the Nautobot Inventory
date: 2025-05-13 9:00:00 -500
categories: [Nautobot,Ansible,Automtation]
tags: [NetworkAutomation,NetworkSourceOfTruth,nautobot,AutomationPlatform,NautobotTutorials]
image:
  path: /assets/img/nautobot_workshop/light_title_image-50.webp
---

# Nautobot Workshop Blog Series
"Nautobot Workshop" is a blog series that guides you through building a fully automated network lab using Nautobot, Containerlab, and Docker. Starting from environment setup on Ubuntu, each post will walk through deploying Nautobot with nautobot-docker-compose, modeling network topologies with Containerlab and vrnetlab-based routers, and populating Nautobot with real device data using Ansible. You'll also learn how to use Nautobot’s GraphQL API for dynamic inventory, generate device configurations with Jinja2 templates, and enforce configuration compliance using the Golden Config plugin. This series is ideal for network engineers looking to integrate source of truth, automation, and lab simulation into a streamlined workflow.

## Part 4: Building ContainerLab topology from the Nautobot Inventory

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

In our ```main.yml``` under the tasks folder we will build the tasks to perform the GraphQL query and then template the output into a new YAML file called ```containerlab-topology.yml```. Beisdes the device name and interfaces, the model, platform and software version, and connected interfaces are important because we will use those variable in our Jinja template that builds the topology.

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
        devices  {
          name
          device_type{
            model
            manufacturer {
            name
          }
            }
          platform {
            name
          }
          software_version {
            version
          }
          interfaces {
            name
            ip_addresses {
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

- name: Render Containerlab topology
  template:
    src: "containerlab_topology.j2"
    dest: "~/Nautobot-Workshop/clabs/containerlab-topology.yml"
```

Update the ```templates/containerlab_topology.j2``` file with the following

```jinja
{%raw%}
#jinja2: lstrip_blocks: True, trim_blocks: True
{% set delay_targets = ["vrnetlab/vr-xrv9k", "vrnetlab/n9kv"] %}
{% set global_delay = [0] %}

name: nautobot_workshop

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
      {% if image_base is defined and image_base in delay_targets %}
      startup-delay: {{ global_delay[0] * 30 }}
      {% set _ = global_delay.append(global_delay.pop() + 1) %}
      {% endif %}
      env:
        HOSTNAME: {{ device.name }}
  {% endif %}
  {% if device.name == "clabbr220" %}
    clabbr220:
      kind: bridge
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

This Jinja2 template dynamically generates the Containerlab topology file based on device data retrieved from Nautobot via GraphQL. It filters out any devices that are missing a software_version or platform, ensuring only complete and deployable nodes are included. For each eligible device, it sets the appropriate kind and image based on the device type and software version—using a custom image naming convention for standard nodes and a simplified image tag for cEOS nodes. Devices that match specific image types (like vr-xrv9k or n9kv) receive a calculated startup-delay to avoid startup conflicts. Special logic is included for a device named clabbr220, which is designated as a bridge node rather than a container, enabling external host interface mapping for connectivity testing or hybrid topologies. The links section builds connections between interfaces by inspecting mutual connections and ensures each link is only declared once using a deduplication mechanism. The result is a topology that accurately reflects the modeled lab environment while supporting external L2 integration and startup timing for complex images.

I am using a trunked port for my container lab deployment and so I can add additional vlans to my Ubuntu host operating system. I am going to use this method to create a new interface that uses vlan 220 for the mgmt of my virtual devices. In my netplan config I've added a new interface with the vlan id and no IP addressing. I've also added a bridge called clabbr220 included my new tagged interface. I can then reference the name of this bridge in my containerlab topology file and connect a virtualized nodes interface to it. We will assign our management addressing to these interfaces in our intitial configurations which the virtualized nodes will use on boot.

```yaml
network:
    
    vlans:
        bond0.220:
            id: 220
            link: bond0
            dhcp4: false
            dhcp6: false
    bridges:
      clabbr220:
        interfaces: [bond0.220]
        parameters:
          stp: false
          forward-delay: 0
        dhcp4: no
```

