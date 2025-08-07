---
title: Nautobot Workshop Blog Series - Part 8 - Nautobot Golden Configuration - Intended Configurations
date: 2025-08-07 9:00:00
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


## Part 7 - Nautobot Golden Configuration - Intended Configurations
Let’s clear up what is meant by configuration compliance. A config is considered compliant when the generated config (what is called the "intended configuration"—usually built from source-of-truth data and a Jinja2 template) exactly matches the config pulled from the device backup. And when I say exact, I mean character-for-character. So even though most engineers would treat int g0/0 and interface GigabitEthernet0/0 as the same, the compliance check doesn’t, it’s a mismatch, period.

There are a few common reasons a device might show up as non-compliant:
    - Missing config on the device
    - Extra config on the device
    - Incorrect data in the source-of-truth, leading to a false positive
    - Issues in the Jinja2 template generating the wrong config
    - Parsing problems when pulling the backup config

There’s no magic here. You still need to define what “good” config looks like, and the tool just does a straight comparison. It doesn’t try to guess what you meant—only what you built. So if something’s missing from your intended config because the data or template was off, the tool flags it, even if the device itself is technically fine from an operational perspective.

### Updating Golden Configuration Settings
Make sure you have created three repositories, one for each, Jinja templates, intended configs, and backup configs, or you can fork mine [tempaltes](https://github.com/byrn-baker/nautobot_workshop_golden_config_templates.git), [intended-configs](https://github.com/byrn-baker/nautobot_workshop_golden_config_intended_configs), [backup-configs](https://github.com/byrn-baker/nautobot_workshop_golden_config_backup_configs). Select the appropriate provides for each one.
<img src="/assets/img/nautobot_workshop/2-git-repos.webp" alt="">

Go back to the Golden Config Settings and update the default setting we used in the last section. We want to include a location for the Intended Configuration, save the intended configurations in the intended-config repo, and for the Templates Configuration use the Jinja Templates repo. Use jinja to setup how the folders and file will be created, for example on the Intended Configs we will store them in a folder based on the location name and the file name will be the device name ```{{obj.location.name|slugify}}/{{obj.name}}.cfg```. We will point the Jinja Templates at a file named after the network driver of each device ```{{obj.platform.network_driver}}.j2```.

<img src="/assets/img/nautobot_workshop/golden_config_settings_intended_templates.webp" alt="">

### Creating the Jinja2 Templates
Lets get our templates started, the Jinja2 templates will use the platform network_driver to determine what template is being used. So in our example we have IOS and a EOS drivers, so our template names in the folder would be ```cisco_ios.j2``` and ```arista_eos.j2```. This needs to exactly match how this is displayed in Nautobot. These files should exist inside your [Jinja Template repository](https://github.com/byrn-baker/nautobot_workshop_golden_config_templates). Most of this work has already been completed in the Ansible section, we can simply copy paste those files and folders right into this repository, with some necessary changes of course.

> Any Ansible Filters used will need to be updated, we are using a custom filter to mimic these, but we have to remove the ```ansible.utils.```.
> For example this section of code below
{: .prompt-tip }

{% raw %}
```jinja
{# --- VRRP Configuration --- #}
{% if interface.cf_vrrp_group_id is defined and interface.cf_vrrp_group_id is not none %}
{% for addr in valid_addrs %}
{% if '.' in addr["address"] %}
{% set gateway4 = addr["address"] | ansible.utils.ipaddr('1') %}
    vrrp {{ interface.cf_vrrp_group_id }} ipv4 {{ gateway4 | ansible.utils.ipv4('address') }}
{% endif %}
{% endfor %}
{% for addr in valid_addrs %}
{% if ':' in addr["address"] %}
{% set gateway6 = addr["address"] | ansible.utils.ipaddr('1') %}
    vrrp {{ interface.cf_vrrp_group_id }} ipv6 {{ gateway6 | ansible.utils.ipv6('address') }}
{% endif %}
{% endfor %}
```
{% endraw %}

> will need to look like this section of code
{: .prompt-tip }

{% raw %}
```jinja
{# --- VRRP Configuration --- #}
{% if interface.cf_vrrp_group_id is defined and interface.cf_vrrp_group_id is not none %}
{% for addr in valid_addrs %}
{% if '.' in addr["address"] %}
{% set gateway4 = addr["address"] | ipaddr('1') %}
    vrrp {{ interface.cf_vrrp_group_id }} ipv4 {{ gateway4 | ipaddr('address') }}
{% endif %}
{% endfor %}
{% for addr in valid_addrs %}
{% if ':' in addr["address"] %}
{% set gateway6 = addr["address"] | ipaddr('1') %}
    vrrp {{ interface.cf_vrrp_group_id }} ipv6 {{ gateway6 | ipaddr('address') }}
{% endif %}
{% endfor %}
```
{% endraw %}

> Notice instead of ansible.utils.ipv4 we are simply using ipaddr, my thinking here was to make it easier to find replace. Other things to avoid in your templates are "do" statements as these will also fail. They are not supported with Nornirs Jinja and I have to figured out a way to import the functionality. 
> I also made adjustments to the BGP template under the ios folder. In our ansible template we used the do statement a few times, so I had to come up with another way to perform the same task.
{: .prompt-tip }

If you take one of the backup configs for a provider_router, as an example, we can validate that the running configuration is matching our templates in terms of spacing and formatting. You might need to do some editing of our templates to get them to match perfectly. 

> Remember that for the compliance piece your intended configurations should match exactly to your backup configurations. This means when naming interfaces in Nautobot use the interface nomenclature that is in the running configuration, not the short form. The entire point of these templates are not to create the configurations for the route, but to validate that the running configuration is matching your intended configuration. To do that you first need a template of what the intended configuration should look like.
{: .prompt-tip }

> You will have noticed this warning when pushing configurations to a cisco node from ansible - **To ensure idempotency and correct diff the input configuration lines should be similar to how they appear if present in the running configuration on device including the indentation** - the same principle stands for compliance through the Golden Config App.
{: .prompt-tip }

### Updating the container deployment
> Before our Jinja templates will function correctly we need to make a change and add a file to our nautobot-docker-compose deployment. Under the nautobot-docker-compose folder create a new folder called ```custom_jinja_filters``` and place a file in this folder called ```netaddr_filters.py```. 
{: .prompt-tip }

netaddr_filters.py:
```python
from netaddr import IPNetwork, IPAddress
from netaddr.core import AddrFormatError
from django_jinja import library

@library.filter
def ipaddr(value, operation=None):
    """Mimic Ansible's ipaddr filter, including IP address validation."""
    # Handle IP address validation (ansible.utils.ipaddr('1') or no operation)
    if operation == '1' or operation is None:
        try:
            # Try to parse as CIDR first to handle inputs like '192.168.1.1/24'
            try:
                ip_network = IPNetwork(value)
                ip = ip_network.ip  # Extract the IP address part
            except Exception:
                ip = value  # If not CIDR, try as plain IP
            # Validate as IP address
            ip_addr = IPAddress(ip)
            return str(ip_addr)  # Return the IP address as a string if valid
        except AddrFormatError:
            return False  # Return False if not a valid IP address

    # Existing logic for CIDR-based operations
    try:
        ip = IPNetwork(value)
    except Exception:
        return value  # Fail gracefully if it's not CIDR

    if operation == "address":
        return str(ip.ip)
    elif operation == "netmask":
        return str(ip.netmask)
    elif operation == "prefix":
        return str(ip.prefixlen)
    elif operation == "network":
        return str(ip.network)
    elif operation == "broadcast":
        return str(ip.broadcast)
    elif operation == "hostmask":
        return str(ip.hostmask)
    else:
        return str(ip)  # Fallback to full CIDR notation
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
Once the containers are back up and running, navigate over to Golden Configuration menu, and Tools and click the Generate Intended Config link. We can use this tool to test our intended configuration templates above. This is a great tool and a great way to ensure there are no issues with each template, and if you are watching your docker logs it will tell you which file and in which line an issue might exist. This provides a decent way to debug as you go.

<img src="/assets/img/nautobot_workshop/generate_intedend_configs.webp" alt="">

Now navigate over to the Golden Config Overview and click the play button for the P1 router.
<img src="/assets/img/nautobot_workshop/config-overview.webp" alt="">

Then click the Run Job Now button
<img src="/assets/img/nautobot_workshop/intended-config-job.webp" alt="">

You should see a results page similar to this. You will see a failure for the Configuration Rule as we have not set this up yet. 
<img src="/assets/img/nautobot_workshop/intended-config-job-results.webp" alt="">

What you should notice now is a new configuration file under your intended_configs folder and in your overview page that router should now have a backbup, intended configuration, and compliance detail icon on the right side of the page. You should also have a date of the intended status as well.

### Conclusion
With our intended configuration templates in place and the environment updated to support custom Jinja filters, we have all the components necessary to perform comprehensive configuration compliance checks in Nautobot. By structuring templates around roles and platforms while keeping interface logic modular, we ensure clean, reusable configuration templates that scale as the lab expands. Once the intended configurations are generated, Nautobot excels at comparing them byte-for-byte against the actual device configurations. If they match, you're compliant. If not, you must investigate whether the discrepancy stems from the data, the template, or the device itself. Regardless, you now have visibility, versioning, and validation, all underpinned by source-of-truth automation.

In Part 9, we will explore configuration compliance, compliance features, and compliance rules within the Nautobot Golden Config App.

