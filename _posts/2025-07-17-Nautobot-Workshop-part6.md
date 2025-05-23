---
title: Nautobot Workshop Blog Series - Part 6 - Nautobot Golden Configuration - Intended Configurations
date: 2025-07-17 9:00:00 -500
categories: [Nautobot,Ansible,Automtation]
tags: [NetworkAutomation,NetworkSourceOfTruth,nautobot,AutomationPlatform,NautobotTutorials]
image:
  path: /assets/img/nautobot_workshop/light_title_image-50.webp
---

# Nautobot Workshop Blog Series
"Nautobot Workshop" is a blog series that guides you through building a fully automated network lab using Nautobot, Containerlab, and Docker. Starting from environment setup on Ubuntu, each post will walk through deploying Nautobot with nautobot-docker-compose, modeling network topologies with Containerlab and vrnetlab-based routers, and populating Nautobot with real device data using Ansible. You'll also learn how to use Nautobot’s GraphQL API for dynamic inventory, generate device configurations with Jinja2 templates, and enforce configuration compliance using the Golden Config plugin. This series is ideal for network engineers looking to integrate source of truth, automation, and lab simulation into a streamlined workflow.

## Part 6 - Nautobot Golden Configuration - Intended Configurations
Let’s clear up what is meant by configuration compliance. A config is considered compliant when the generated config (what is called the "intended configuration"—usually built from source-of-truth data and a Jinja2 template) exactly matches the config pulled from the device backup. And when I say exact, I mean character-for-character. So even though most engineers would treat int g0/0 and interface GigabitEthernet0/0 as the same, the compliance check doesn’t, it’s a mismatch, period.

There are a few common reasons a device might show up as non-compliant:
    - Missing config on the device
    - Extra config on the device
    - Incorrect data in the source-of-truth, leading to a false positive
    - Issues in the Jinja2 template generating the wrong config
    - Parsing problems when pulling the backup config

There’s no magic here. You still need to define what “good” config looks like, and the tool just does a straight comparison. It doesn’t try to guess what you meant—only what you built. So if something’s missing from your intended config because the data or template was off, the tool flags it, even if the device itself is technically fine from an operational perspective.

### Updating Golden Configuration Settings
Create another repository for the Jinja templates or you can fork [mine](https://github.com/byrn-baker/nautobot_workshop_golden_config_templates.git). Use the above to setup this repository and only select the "jinja templates" under the provides section.
<img src="/assets/img/nautobot_workshop/2-git-repos.webp" alt="">

Go back to the Golden Config Settings and update the default setting we used in the last section. We want to include a folder location for the Intended Configuration. We will save the intended configurations in the intended-config folder.

<img src="/assets/img/nautobot_workshop/golden_config_settings_intended_templates.webp" alt="">

### Creating the Jinja2 Templates
Lets get our templates started, the Jinja2 templates will use the platform network_driver to determine what template is being used. So in our example we have IOS and a EOS drivers, so our template names in the folder would be ```cisco_ios.j2``` and ```arista_eos.j2```. This needs to exactly match how this is displayed in Nautobot. Make sure you have a folder called ```nautobot_workshop_golden_config_templates``` after cloning it to your working directory. 

Inside your ```nautobot_workshop_golden_config_templates``` folder create the below files:
```bash
ubuntu@containerlabs:~/Nautobot-Workshop$ touch nautobot_workshop_golden_config_templates/cisco_ios.j2
ubuntu@containerlabs:~/Nautobot-Workshop$ touch nautobot_workshop_golden_config_templates/arista_eos.j2
ubuntu@containerlabs:~/Nautobot-Workshop$ cd nautobot_workshop_golden_config_templates/
ubuntu@containerlabs:~/nautobot_workshop_golden_config_templates$ tree
.
├── arista_eos.j2
└── cisco_ios.j2

1 directory, 2 files
```
As stated above we want to make sure from a compliance standpoint your templates should exactly match how the running configuration on the device looks.

Lets start with the cisco_ios.j2 template, we will make slightly different templates for each role, this way you have a structure that can work with routers and switches if you want later. We will use folders to separate out those different templates, but all will start with this first cisco_ios.j2 template.

[cisco_ios.j2](https://github.com/byrn-baker/nautobot_workshop_golden_config_templates/blob/main/cisco_ios.j2)

We are looking at the device_role name and matching that to an existing device role for a cisco router, then pointing it to a folder and another jinja template. Make sure in your nautobot_workshop_golden_config_templates folder you now have these folders and jinja templates.

```bash
ubuntu@containerlabs:~/nautobot_workshop_golden_config_templates$ mkdir -p ios/platform_templates
ubuntu@containerlabs:~/nautobot_workshop_golden_config_templates$ mkdir -p ios/interfaces
ubuntu@containerlabs:~/nautobot_workshop_golden_config_templates$ touch ios/platform_templates/provider_router.j2
ubuntu@containerlabs:~/nautobot_workshop_golden_config_templates$ touch ios/platform_templates/provider_edge_router.j2
ubuntu@containerlabs:~/nautobot_workshop_golden_config_templates$ touch ios/platform_templates/customer_edge_router.j2
ubuntu@containerlabs:~/nautobot_workshop_golden_config_templates$ touch ios/interfaces.j2
ubuntu@containerlabs:~/nautobot_workshop_golden_config_templates$ touch ios/interfaces/_loopback.j2
ubuntu@containerlabs:~/nautobot_workshop_golden_config_templates$ touch ios/interfaces/_router_physical.j2
ubuntu@containerlabs:~/nautobot_workshop_golden_config_templates$ touch ios/interfaces/_switch_l2_physical.j2
ubuntu@containerlabs:~/nautobot_workshop_golden_config_templates$ touch ios/interfaces/_switch_l3_physical.j2
ubuntu@containerlabs:~/nautobot_workshop_golden_config_templates$ touch ios/_switch_l3_virtial.j2
ubuntu@containerlabs:~/nautobot_workshop_golden_config_templates$ tree
.
├── arista_eos.j2
├── cisco_ios.j2
└── ios
    ├── interfaces
    │   ├── _loopback.j2
    │   ├── _router_physical.j2
    │   ├── _switch_l2_physical.j2
    │   ├── _switch_l3_physical.j2
    │   └── _switch_l3_virtial.j2
    ├── interfaces.j2
    └── platform_templates
        ├── customer_edge_router.j2
        ├── provider_edge_router.j2
        └── provider_router.j2

4 directories, 11 files
```

This format allow us to keep the templates as modular as possible, so for example the interfaces in our lab, we can reuse the same format for all three devices roles and simply reference those templates using the include statements. This should help cut down on how many different files you are attempting to manage and help maintain a standard configuration template as you build out your templates.

Lets start with the provider_router template, we can pretty much just take one of our backups and past it into this template. With the correct structure in place you can start to adjust the sections of the configuration to insert the variables from our SoT, Nautobot.

> Remember that for the compliance piece your intended configurations should match exactly to your backup configurations. This means when naming interfaces in Nautobot use the interface nomenclature that is in the running configuration, not the short form.
{: .prompt-tip }

If you take a copy of one of the backup configs for a provider_router we can make just two changes, include a variable for the hostname and then replace the interfaces with an include to the interfaces template. In the interfaces template it will loop through all the device interfaces and check for different names and/or device roles or device types, I will leave that up to you. However you decide to proceed make sure your saved graphhQL query includes those things you want to use in the template. For example if there is a specific configuration for all MGMT interfaces then make sure in the query you include the mgmt_only field.

[interfaces.j2](https://github.com/byrn-baker/nautobot_workshop_golden_config_templates/blob/main/ios/interfaces.j2)

[_loopback.j2](https://github.com/byrn-baker/nautobot_workshop_golden_config_templates/blob/main/ios/interfaces/_loopback.j2)

[_router_physical.j2](https://github.com/byrn-baker/nautobot_workshop_golden_config_templates/blob/main/ios/interfaces/_router_physical.j2)

[provider_router.j2](https://github.com/byrn-baker/nautobot_workshop_golden_config_templates/blob/main/ios/platform_templates/provider_router.j2)

### Updating the container deployment
> Before our Jinja templates will function correctly we need to make a change and add a file to our nautobot-docker-compose deployment. Under the nautobot-docker-compose folder create a new folder called ```custom_jinja_filters``` and place a file in this folder called ```config_templates.py```. 
{: .prompt-tip }

config_templates.py:
```python
from netaddr import IPNetwork
from django_jinja import library


@library.filter
def ipv4_address(value):
    return str(IPNetwork(value).ip)


@library.filter
def netmask(value):
    return str(IPNetwork(value).netmask)

```
You will need to update the nautobot_config.py to ensure this works with django_jinja
```python
"""Nautobot development configuration file."""

# pylint: disable=invalid-envvar-default
import os
import sys

from nautobot.core.settings import *  # noqa: F403  # pylint: disable=wildcard-import,unused-wildcard-import
from nautobot.core.settings_funcs import is_truthy, parse_redis_connection
from custom_jinja_filters import netaddr_filters  # noqa: F401
```

Then you will need to also update the ```nautobot-docker-compose/environments/docker-compose.local.yml``` file and add the new folder to the volumes under the nautobot and celery_worker configs
```yaml
---
services:
  nautobot:
    command: "nautobot-server runserver 0.0.0.0:8080"
    ports:
      - "8080:8080"
    volumes:
      - "../config/nautobot_config.py:/opt/nautobot/nautobot_config.py"
      - "../jobs:/opt/nautobot/jobs"
      - "../custom_jinja_filters:/opt/nautobot/custom_jinja_filters"
    healthcheck:
      interval: "30s"
      timeout: "10s"
      start_period: "60s"
      retries: 3
      test: ["CMD", "true"]  # Due to layering, disable: true won't work. Instead, change the test
  celery_worker:
    volumes:
      - "../config/nautobot_config.py:/opt/nautobot/nautobot_config.py"
      - "../jobs:/opt/nautobot/jobs"
      - "../custom_jinja_filters:/opt/nautobot/custom_jinja_filters"

```

Then stop the container, rebuild it and restart it. 

### Running the Golden Config compliance job
Once the containers are back up and running, navigate over to Golden Configuration menu, and Tools and click the Generate Intended Config link. We can use this tool to test our intended configuration templates above. This is a great tool and a great way to ensure there are no issues with each template, and if you watching your docker logs it will tell you which file and which line an issue might exists. This provides a decent way to debug as you go.

<img src="/assets/img/nautobot_workshop/generate_intedend_configs.webp" alt="">

Now navigate over to the Golden Config Overview and click the play button for the P1 router.
<img src="/assets/img/nautobot_workshop/config-overview.webp" alt="">

Then click the Run Job Now button
<img src="/assets/img/nautobot_workshop/intended-config-job.webp" alt="">

You should see a results page similar to this. You will see a failure for the Configuration Rule as we have not set this up yet. 
<img src="/assets/img/nautobot_workshop/intended-config-job-results.webp" alt="">

What you should notice now is a new configuration file under your intended_configs folder and in your overview page that router should now have a backbup, intended configuration, and compliance detail icon on the right side of the page. You should also have a date of the intended status as well.

### Conclusion
With our intended configuration templates in place and the environment updated to support custom Jinja filters, we now have everything we need to perform full configuration compliance checks in Nautobot. By structuring our templates around roles and platforms, and keeping the interface logic modular, we can maintain clean, reusable config templates that scale as the lab grows. Once intended configurations are generated, Nautobot does what it does best—compare them byte-for-byte against the actual configs. If it matches, you're good. If not, it’s on you to track down whether the issue is with the data, the template, or the device itself. Either way, you’ve now got visibility, versioning, and validation—all backed by source-of-truth automation.