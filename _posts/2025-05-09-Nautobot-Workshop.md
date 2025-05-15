---
title: Nautobot Workshop Blog Series - Overview
date: 2025-05-09 9:00:00 -500
categories: [Nautobot,Ansible,Automtation]
tags: [NetworkAutomation,NetworkSourceOfTruth,nautobot,AutomationPlatform,NautobotTutorials]
image:
  path: /assets/img/nautobot_workshop/light_title_image-50.webp
---

# Nautobot Workshop Blog Series
"Nautobot Workshop" is a blog series that guides you through building a fully automated network lab using Nautobot, Containerlab, and Docker. Starting from environment setup on Ubuntu, each post will walk through deploying Nautobot with nautobot-docker-compose, modeling network topologies with Containerlab and vrnetlab-based routers, and populating Nautobot with real device data using Ansible. You'll also learn how to use Nautobot’s GraphQL API for dynamic inventory, generate device configurations with Jinja2 templates, and enforce configuration compliance using the Golden Config plugin. This series is ideal for network engineers looking to integrate source of truth, automation, and lab simulation into a streamlined workflow.

## Workshop Outline

### Part 1: Environment Setup
Goal: Build a repeatable automation lab foundation using Ubuntu, Containerlab, Nautobot, and vrnetlab.

- Install and prepare Ubuntu 24.04 LTS
- Install dependencies:

    - Docker
    - Containerlab
    - vrnetlab (for IOL)
    - nautobot-docker-compose
- Clone and configure:
    - containerlab-topology
    - nautobot-docker-compose

- Validate working environment:
    - Spin up Nautobot stack
    - Verify IOL devices launch via containerlab

### Part 2: Review the Network Topology
Goal: Understand the multi-site MPLS lab you’ll be modeling in Nautobot.

- Overview of uploaded diagrams:
  - Provider topology <img src="/assets/img/nautobot_workshop/Nautobot Workshop-Backbone.webp" alt="">
  - East Data Center <img src="/assets/img/nautobot_workshop/Nautobot Workshop-East DataCenter.webp" alt="">
  - West Data Center <img src="/assets/img/nautobot_workshop/Nautobot Workshop-West DataCenter.webp" alt="">
  - In-band Management <img src="/assets/img/nautobot_workshop/Nautobot Workshop-IN-BAND MGMT.webp" alt="">
- Discuss ASN layout, IP schemes (v4/v6), and router roles (RR, PE, P, CE)
- Management overlay discussion and how it ties into automation

### Part 3: Adding Devices to Nautobot via Ansible
Goal: Automate network inventory onboarding.

- Use networktocode.nautobot Ansible collections
- Build YAML or Jinja templates for devices, interfaces, and IPs
- Write a playbook to:
  - Create Sites, Devices, Interfaces, IP Addresses, Connections
- Validate in Nautobot UI

### Part 4: Building ContainerLab topology from the Nautobot Inventory
Goal: Create a virtual topology based on the Nautobot inventory that can be used for testing and validation.

- Write GraphQL queries for device + interface inventory
- Write a Jinja2 template to create the CLAB topology YAML
- Write a Jinja2 template to create an initial configuration with MGMT reachability

### Part 5 - Nautobot Golden Configuration - Configuration Backups
Goal: Enable automated configuration backups from network devices to a Git repository using the Nautobot Golden Configuration app.

  - Configure GitHub secret in Nautobot Secrets
  - Create a Secrets Group for GitHub token access
  - Add and sync a Git repository to store backups
  - Prepare Git repo with jobs/ and backup-configs/ folders
  - Create a GraphQL query for SOT Aggregation
  - Update Golden Config Settings to:
  - Define backup paths
  - Associate SOT Aggregation Query
  - Enable required Golden Config Jobs
  - Execute Backup Configurations Job for EOS and IOS devices
  - Confirm backups stored in Git under backup-configs/