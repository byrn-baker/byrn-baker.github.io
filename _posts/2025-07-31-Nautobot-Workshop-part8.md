---
title: Nautobot Workshop Blog Series - Part 8 - Nautobot Config Context and Custom Fields
date: 2025-07-31 9:00:00 -500
categories: [Nautobot,Ansible,Automtation]
tags: [NetworkAutomation,NetworkSourceOfTruth,nautobot,AutomationPlatform,NautobotTutorials]
image:
  path: /assets/img/nautobot_workshop/light_title_image-50.webp
---

# Nautobot Workshop Blog Series
"Nautobot Workshop" is a blog series that guides you through building a fully automated network lab using Nautobot, Containerlab, and Docker. Starting from environment setup on Ubuntu, each post will walk through deploying Nautobot with nautobot-docker-compose, modeling network topologies with Containerlab and vrnetlab-based routers, and populating Nautobot with real device data using Ansible. You'll also learn how to use Nautobot’s GraphQL API for dynamic inventory, generate device configurations with Jinja2 templates, and enforce configuration compliance using the Golden Config plugin. This series is ideal for network engineers looking to integrate source of truth, automation, and lab simulation into a streamlined workflow.

## Part 8 - Nautobot Config Context and Custom Fields

While the Jinja templates are now in place, many elements within them remain static. Several configuration details—such as those based on a device’s **location** or **role**—need to be dynamic. To achieve this, we should incorporate logic into the templates to ensure that each router receives the appropriate configuration.

Nautobot provides a powerful feature called **Config Context**, which allows us to attach structured data (in JSON format) to devices. This data can be applied based on various criteria including location, role, platform, device type, or even specific device names. For example, we can define NTP servers for all devices in a specific site or assign SNMP community strings based on device role.

Config Contexts also support **weighting**, which enables the definition of default values. When multiple contexts match a device, the one with the highest weight takes precedence—ensuring that there is always a fallback configuration if no specific match is found.

Additionally, Nautobot supports storing Config Context data in a **Git repository**. This enables version control and aligns the management of configuration data with modern **CI/CD workflows**, allowing changes to be tracked, reviewed, and deployed systematically—outside of the Nautobot web UI.

### 