---
title: Nautobot Workshop Blog Series - Part 6 - Nautobot Config Context and Custom Fields
date: 2025-07-10 9:00:00
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


## Part 6 - Nautobot Config Context and Custom Fields

While the Jinja templates are now in place, many elements within them remain static. Several configuration details—such as those based on a device’s **location** or **role**—need to be dynamic. To achieve this, we should incorporate logic into the templates to ensure that each router receives the appropriate configuration.

Nautobot provides a powerful feature called **Config Context**, which allows us to attach structured data (in JSON format) to devices. This data can be applied based on various criteria including location, role, platform, device type, or even specific device names. For example, we can define NTP servers for all devices in a specific site or assign SNMP community strings based on device role.

Config Contexts also support **weighting**, which enables the definition of default values. When multiple contexts match a device, the one with the highest weight takes precedence—ensuring that there is always a fallback configuration if no specific match is found.

Additionally, Nautobot supports storing Config Context data in a **Git repository**. This enables version control and aligns the management of configuration data with modern **CI/CD workflows**, allowing changes to be tracked, reviewed, and deployed systematically—outside of the Nautobot web UI.

### 
