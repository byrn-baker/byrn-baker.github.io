---
title: Nautobot Workshop Blog Series - Review
date: 2025-07-24 9:00:00
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


## Nautobot Workshop Review: From Zero to Network Source of Truth
Over the last few months, I’ve walked through building an end-to-end, declarative, source-of-truth-driven network automation lab using [Nautobot](https://networktocode.com/nautobot/), [Containerlab](https://containerlab.dev/), [Ansible](https://docs.ansible.com/?extIdCarryOver=true&intcmp=7015Y000003t7aWQAQ&sc_cid=701f2000001OH6fAAG), and a handful of supporting tools. This post recaps everything we’ve covered so far—setting the stage for what comes next in the Nautobot Workshop.

Whether you're just joining or need a quick refresher, this post brings it all together.

### 🧱 Part 1: Foundation – Building the Lab Environment
We began with setting up a lab environment on Ubuntu 24.04 with:
- Containerlab to define topologies.
- vrnetlab to emulate Cisco IOS IOL and XRv9k.
- Nautobot deployed via nautobot-docker-compose for structured, extensible inventory management.
> The goal: build a flexible, multi-vendor emulated lab with Nautobot as the authoritative source of truth.

We imported core config elements as Config Contexts into Nautobot, such as:
- VRF definitions
- Interface metadata
- Line/VTY settings
- HTTP/SSH configuration

These JSON-based contexts were later rendered into real device configurations via Jinja2 templates.

### 🌐 Part 2: Designing the Network Topology
The lab topology was intentionally overbuilt to simulate service provider use cases:
- Cisco IOL routers form the core MPLS backbone using OSPF, LDP, and MP-BGP.
- Arista EOS nodes provide a VXLAN-based data center fabric using eBGP.
- Loopbacks and IPAM follow a consistent schema across both IPv4 and IPv6.
- VRFs and L3VPNs connect CEs to the core and to each other, making for a fully routed, virtualized environment.

This topology was defined using YAML and stored alongside configuration templates and design data.

### 🧩 Part 3: Populating Nautobot with Ansible
Next, I used Ansible + Pynautobot to populate Nautobot with structured data:
- Sites, device types, platforms, and roles.
- Devices, interfaces, and IP addresses.
- Prefixes and VLANs.

These playbooks pulled data from structured YAML inputs, making it easy to track, version, and update. I also added config context templates for things like VRFs and SNMP, allowing us to render device configurations directly from Nautobot’s inventory.

### ✍️ Part 3.1: Design Builder – Declarative Input, Repeatable Output
Then came a major leap: I used the [Nautobot Design Builder App](https://github.com/nautobot/nautobot-app-design-builder).
Instead of having imperative playbooks and scripts, I defined initial_data.yml:

```yaml
devices:       
  - name: P1
    role: Provider Router
    location: Backbone
    device_type: iol
    platform: IOS
    software_version: 17.12.01
    primary_ip4: 192.168.220.2/24
    interfaces:
      - name: Ethernet0/1
        type: 1000base-t
        ipv4_address: 100.0.12.1/24
        ipv6_address: 2001:db8:100:12::1/64
        ospf_area: 0
        ospf_network_type: point-to-point
        mpls_enabled: true
        z_device: P2
        z_interface: Ethernet0/1
```

This design file was fed into a Nautobot Job that:
- Created all devices, interfaces, cables, VRFs, and IP addresses.
- Created routing instances and associated protocols like OSPF and BGP.
- Allowed previewing the input data before committing.

This shift from imperative to declarative made the entire workflow testable, portable, and reusable.

### 🧠 Part 3.2: Smarter BGP Modeling
To support more advanced use cases, I extended the [Nautobot Design Builder App](https://github.com/nautobot/nautobot-app-design-builder) with support for the following existing BGP Modeling Fields:
- peer-group
- description
- local interface
- local IP

The goal was to give full parity with endpoint model in the [Nautobot BGP Modeling App](https://github.com/nautobot/nautobot-app-bgp-models).

### 🧪 Part 4: Building the Containerlab Topology from Nautobot
Once the design was in Nautobot, I used a Jinja2 template to generate a clab.yml topology file:
- Auto-selected node images (Arista EOS, IOS IOL, XRv9k).
- Set unique IPv4/IPv6 management addresses.
- Built all links and interfaces from Nautobot’s cable and interface data.
- Added delay for devices like XRv9k during boot.

This made Nautobot the single source of truth for both network configuration and the lab topology itself.

### 📦 Part 5: Ansible Dynamic Inventory via GraphQL
To connect configuration automation, I used Nautobots dynamic inventory module that:
- Queried Nautobot using its GraphQL API.
- Returned a usable Ansible inventory, grouped by device role, site, and platform.
- Pulled in config contexts, IP addresses, and host vars.

Now Ansible has live access to Nautobot inventory—no more static INI files or YAML inventories.

### 🧬 Part 6: Extending Nautobot’s Data Model
Finally, I explored how to extend Nautobot with:
- Custom Fields: simple key-value fields attached to devices, interfaces, or sites.
- Computed Fields: fields automatically generated from other data (e.g., interface count, interface descriptions).
- Relationships and custom statuses, enabling flexible object modeling without needing new plugins.

This paves the way for future use cases: golden config auditing, compliance checks, visualization, and more.

## 🚀 What’s Next?
The foundation is now fully laid. In future posts, I plan to explore:
- Golden Config plugin: ensure live configs match expected templates.
- Validation: use Compliance-as-Code principles to enforce policy.
- Service modeling: represent L3VPN, EVPN, or application chains as Nautobot-native objects.
- CI/CD pipelines to sync, validate, deploy network changes across labs or production environments.

## 💡 Final Thoughts
This workshop series is built around a simple idea: **design once, automate everywhere**. With Nautobot at the center, every layer — topology, configuration, state — is driven by data.
By investing upfront in modeling and structure, I now have a lab that:
- Launches in seconds via containerlab deploy
- Configures itself using Ansible
- Tracks its design state in Nautobot
- Evolves cleanly and repeatably as the network grows

Stay tuned—the fun is just getting started.