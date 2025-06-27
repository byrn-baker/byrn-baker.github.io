---
title: Nautobot Workshop Blog Series - Part 3.1 Using the Nautobot Design Builder App
date: 2025-06-19 09:00:00
categories: [Nautobot, Ansible, Automation]
tags: [NetworkAutomation, NetworkSourceOfTruth, nautobot, AutomationPlatform, NautobotTutorials]
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


## Using the Nautobot Design App to Seed My Workshop Demo
In [Part 3 of the Nautobot Workshop](https://blog.byrnbaker.me/posts/Nautobot-Workshop-part3/), I demonstrated how to automate Nautobot data entry using Ansible playbooks. That method worked well for an initial introduction for how to manage Nautobot with Ansible. But as your topology grows, you will want a more declarative, structured, and maintainable solution—one that can be versioned as a “design spec.”

Enter the Nautobot Design App.

In this post, I’ll walk through how I used the Design App to seed my lab with devices, IPs, VRFs, interfaces, and cables—replacing the previous imperative-style playbooks with a fully declarative data model.

## 🧱 From Playbooks to Designs
While Ansible offered flexibility, it required multiple roles and templates to manage things like:
- Device creation
- Interface assignment
- IPAM prefix planning
- Cable mappings
- Protocol tagging (MPLS, OSPF)

The Design App allowed me to consolidate all of that into:
1. A YAML context file (initial_data.yml)
2. A single Jinja2 design template (0001_design.yaml.j2)
3. A Python job (InitialDesign) that renders and commits it into Nautobot

This transition gave me:
- A true source-of-truth file (initial_data.yml)
- Declarative infrastructure-as-data
- Easier debugging with preview mode (/tmp/rendered_yaml.txt)
- Reusability across labs, demos, and training

## 🛠️ Why I Switched

| **Feature**            | **Ansible Playbooks**             | **Nautobot Design App**              |
|-------------------------|-----------------------------------|--------------------------------------|
| **Imperative vs Declarative** | Procedural tasks                 | YAML-driven rendering               |
| **Version Control**     | Variables + Tasks                | Full designs in one YAML file       |
| **Extensibility**       | Roles and templates              | Jinja macros with looped YAML sections |
| **Debuggability**       | Limited to task output           | Full YAML rendered to file          |
| **Reproducibility**     | Role and var-dependent           | One job = full topology             |

The Design App feels like a natural evolution of my Ansible workflow—less about task orchestration, more about design expression.

## 🧱 Overview of the Design App Architecture
The Design App lets you render data-driven templates into fully populated Nautobot models. My workflow consists of three key components:
1. initial_data.yml – Contains raw, structured data for the entire lab.
.2 0001_design.yaml.j2 – A Jinja2 template that renders valid Nautobot YAML from that data.
3. InitialDesign – A Python class that wraps the design into a runnable job inside Nautobot.

Together, they allow me to go from idea to fully built Nautobot inventory with a single job run.

### 📄 The Design Template – 0001_design.yaml.j2
This Jinja2 template is the heart of the system. It transforms the structured YAML context into Nautobot-native YAML DSL syntax, using !create_or_update, !ref, and !get tags.

**Highlights from the Template:**
- Custom Fields:
  
```jinja
- "!create_or_update:key": {{ field.key }}
  label: {{ field.name }}
  ...
```

- VRFs and Prefixes:
  
```jinja
- "!create_or_update:name": {{ vrf.name }}
  namespace: "!ref:{{ vrf.namespace }}_namespace"
  rd: {{ vrf.rd }}
```

- Device Configuration via Macro:
  
```jinja
{% raw %}
{% macro device(device_data, site_ref) %}
- "!create_or_update:name": {{ device_data.name }}
  interfaces:
  {% for intf in device_data.interfaces %}
  ...
  {% endfor %}
{% endmacro %}
{% endraw %}
```

- Cable Auto-Generation (based on lexical ordering):
  
```jinja
{% raw %}
- "!create_or_update:label": "{{ device_data.name }} ↔ {{ intf.z_device }} ({{ intf.name }})"
  termination_a: "!ref:..._{{ intf.name }}"
  termination_b: "!ref:..._{{ intf.z_interface }}"
{% endraw %}
```

This level of abstraction lets me focus on declaring what the network should look like, not how to click around Nautobot to build it.

### 📥 The Data Context – initial_data.yml
This YAML file defines all the inputs the template expects:

- List of devices, with attributes like platform, role, type, and interfaces
- IPAM data (prefixes, VRFs, namespaces)
- Platform metadata (manufacturer, software version)
- Site structure (locations, roles, location types)
- Custom fields and their content type targets
- Interface-level attributes (e.g., OSPF, MPLS, VRF)

Example snippet:

```yaml
devices:
  - name: East-Spine01
    role: Datacenter Spine
    device_type: ceos
    platform: EOS
    location: East Side Data Center
    software_version: 4.34.0F
    interfaces:
      - name: Ethernet1
        type: 1000base-t
        ipv4_address: 100.1.1.1/30
        ospf_area: 0.0.0.0
```

### ⚙️ The Python Job – InitialDesign
Registered via:

```python
class InitialDesign(DesignJob):
    ...
    class Meta:
        design_file = "designs/0001_design.yaml.j2"
        context_class = InitialDesignContext
```

It uses a small override to log the rendered template to /tmp/rendered_yaml.txt before committing, which is great for debugging or auditing.

### 🔧 What Gets Built
Running this one job creates:

- 3 Sites: East, West, Backbone
- 10+ Devices: Leafs, Spines, PEs, P routers, CE routers
- Dozens of Interfaces: With LAGs, IPs, and OSPF/MPLS attributes
- IPAM Objects: Namespaces, VRFs, Prefixes
- Structured Cabling: Fully mapped with automatic cable rendering
- Custom Fields: For enabling protocol-specific tagging (OSPF area, MPLS, etc.)

Everything is interlinked using !ref statements, which the Design App resolves to actual Nautobot objects during rendering.

### 💡 Why This Is Awesome
- **Repeatable** – Destroy/rebuild labs in seconds.
- **Declarative** – Describe intent, not steps.
- **Debuggable** – Rendered output is saved for inspection.
- **Extensible** – Add BGP, services, etc., as new design files.
- **Automatable** – Ties directly into Ansible/CI workflows.

## 🚀 What's Next?
This design serves as the foundation for everything else in the workshop:

- ContainerLab topology generation
- Jinja2 configuration rendering
- Dynamic inventory for Ansible
- Golden Config compliance