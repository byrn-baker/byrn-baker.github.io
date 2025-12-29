---
title: Nautobot Workshop Blog Series - Overview
date: 2025-05-24 15:00:00 -6
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


## Workshop Outline

### Part 1: Environment Setup - Release date 6/5
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

### Part 2: Review the Network Topology - Release date 6/12
Goal: Understand the multi-site MPLS lab you’ll be modeling in Nautobot.

- Overview of uploaded diagrams:
  - Provider topology <img src="/assets/img/nautobot_workshop/Nautobot Workshop-Backbone.webp" alt="">
  - East Data Center <img src="/assets/img/nautobot_workshop/Nautobot Workshop-East DataCenter.webp" alt="">
  - West Data Center <img src="/assets/img/nautobot_workshop/Nautobot Workshop-West DataCenter.webp" alt="">
  - In-band Management <img src="/assets/img/nautobot_workshop/Nautobot Workshop-IN-BAND MGMT.webp" alt="">
- Discuss ASN layout, IP schemes (v4/v6), and router roles (RR, PE, P, CE)
- Management overlay discussion and how it ties into automation

### Part 3: Adding Devices to Nautobot via Ansible - Release date 6/19
Goal: Automate network inventory onboarding.

- Use networktocode.nautobot Ansible collections
- Build YAML or Jinja templates for devices, interfaces, and IPs
- Write a playbook to:
  - Create Sites, Devices, Interfaces, IP Addresses, Connections
- Validate in Nautobot UI

### Part 4: Building ContainerLab topology from the Nautobot Inventory - Release date 6/26
Goal: Create a virtual topology based on the Nautobot inventory that can be used for testing and validation.

- Write GraphQL queries for device + interface inventory
- Write a Jinja2 template to create the CLAB topology YAML
- Write a Jinja2 template to create an initial configuration with MGMT reachability

### Part 5 - Nautobot Golden Configuration - Configuration Backups - Release date 7/03
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

### Part 6 - Nautobot Golden Configuration - Intended Configurations - Release date 7/10
Goal: Validate that device configurations match the intended state generated from Nautobot source-of-truth data.

  - Define what configuration compliance means in Nautobot
  - Set up a Git repo for intended configuration templates
  - Create modular Jinja2 templates by platform and role (e.g., IOS, EOS)
  - Update Golden Config Settings to point to intended config templates
  - Extend the container environment to support custom Jinja filters
  - Generate and validate intended configurations
  - Run the compliance job and view compliance status in the Nautobot UI

### Part 7 - Nautobot Ansible Dynamic Inventory - Release date 7/017
Goal: Use Nautobot as a dynamic inventory source in Ansible to generate and deploy real device configurations.

  - Configure Ansible to use Nautobot’s GraphQL API for dynamic inventory
  - Secure API access with environment variables and Ansible Vault
  - Build an Ansible role to query device data from Nautobot
  - Use Jinja2 templates to generate platform-specific configurations
  - Push configurations to Cisco devices using cisco.ios.ios_config
  - Demonstrate how source-of-truth data drives real configuration deployment

### Part 8 - Nautobot Config Context and Custom Fields - - Release date 7/24
Goal: Leverage Nautobot's Config Context and Custom Fields to drive dynamic, structured configuration generation from a Git-backed source of truth.

  - Define and store structured Config Context data in Git for centralized version control
  - Create Config Context Schemas to validate and organize data for:
    - VRF definitions
    - User account configurations
    - Global protocol settings (OSPF, MPLS, BGP)
    - Cisco HTTP server settings (e.g., `ip http server`)
    - SSH access configurations
    - Line VTY parameters
  - Assign Config Contexts to devices based on role, location, or other criteria
  - Enable context weighting to ensure fallback/default configurations
  - Create interface-level Custom Fields to track OSPF-specific metadata:
    - Interface type (point-to-point, point-to-multipoint)
    - Area assignment
  - Use this structured data in Jinja2 templates to generate context-aware, platform-specific configurations
