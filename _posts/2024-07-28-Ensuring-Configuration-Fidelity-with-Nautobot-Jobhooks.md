---
title: Ensuring Configuration Fidelity with Nautobot Jobhooks
date: 2024-07-28 9:00:00 -500
categories: [100DaysOfHomeLab]
tags: [NetworkAutomation,NetworkSourceOfTruth,nautobot,AutomationPlatform,NautobotTutorials,100DaysOfHomeLab]
image:
  path: /assets/img/headers/config fidelity.webp
---

In modern network management, maintaining consistency between your source of truth and the running configuration is crucial. With network configurations often being complex and evolving, tools like Nautobot and automation frameworks such as Jobhooks can be incredibly valuable. In this blog post, we will dive into a Python script for a Nautobot Jobhook that ensures your switch interfaces are updated accurately based on changes made in Nautobot. We'll also explore why it's essential to keep your source of truth aligned with the live configuration.

## The Role of Nautobot Jobhooks

Nautobot is an open-source network source of truth and network automation platform. One of its powerful features is Jobhooks, which allows you to extend and automate operations based on changes to network data. In our case, we're focusing on a Jobhook that updates switch interface configurations using Jinja2 templates and Napalm.

## Why Maintaining Fidelity is Important
Maintaining fidelity between your source of truth and the running configuration is vital for several reasons:

1. **Consistency**: Ensures that your network configuration matches the intended design and specifications. This helps in avoiding configuration drift and misalignment.

2. **Troubleshooting**: When issues arise, having a consistent configuration makes it easier to identify and resolve problems. It also simplifies audits and compliance checks.

3. **Automation Reliability**: Accurate configurations allow automated tools to work as expected, reducing manual intervention and errors.

4. **Change Management**: Automating configuration updates based on changes in your source of truth helps manage and track changes systematically, minimizing the risk of human error.

By leveraging Nautobot Jobhooks and adhering to best practices in configuration management, you can ensure that your network remains reliable, consistent, and aligned with your organizational goals.

### The Python Code Explained

Let's break down the provided code and understand its key components:

#### 1. **Imports and Setup**

```python
import re
from django.conf import settings
from jinja2 import Template, Environment, FileSystemLoader
from nautobot.dcim.models import Device, Interface
from nautobot.extras.jobs import JobHookReceiver
from nautobot.core.celery import register_jobs
from napalm import get_network_driver
from napalm.base.exceptions import ConnectionException, CommandErrorException, ModuleImportError
import os

TEMPLATE_DIR = "/opt/nautobot/jobs/nornir/templates/ios/interfaces"
TEMPLATE_FILE = "_switch_l3_physical.j2"
DEBUG_DIR = "/opt/nautobot/jobs/debug"
```

- **Imports**: Various modules are imported, including Jinja2 for templating, Napalm for network device interaction, and Nautobot's own classes and settings.
- **Configuration Paths**: TEMPLATE_DIR and DEBUG_DIR define where template files and debug logs are stored.


#### 2. **JobHookReceiver Class**

```python
name = "Source Control Jobhooks"

class UpdateSwitchInterfaceJobHookReceiver(JobHookReceiver):
    """Job to update interface configuration based on Jinja2 template."""
    
    class Meta:
        name = "Update_Switch_Interface_Jobhook"
        description = "Update switch interfaces based on changes in Nautobot"
        commit_default = False
        approval_required = True
        has_sensitive_variables = False
```
- **name**: This provides a human-readable label for the Jobhook that will help separate this job from other jobs.
- **Meta Class**: Provides metadata about the Jobhook, such as its name, description, and whether it requires approval.

#### 3. **Generating Configuration**

```python
def generate_config(self, interface, object_change):
    """Generate configuration for the interface using Jinja2 template."""
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template(TEMPLATE_FILE)
    
    config = template.render(interface=interface, object_change_data=object_change)

    # Write the rendered config and interface_data to debug files
    config_debug_file_path = os.path.join(DEBUG_DIR, f"{interface.device.name}_config.txt")
    data_debug_file_path = os.path.join(DEBUG_DIR, f"{interface.device.name}_data.json")

    with open(config_debug_file_path, "w") as config_debug_file:
        config_debug_file.write(config)
    
    return config

```

- **Template Rendering**: Uses Jinja2 to generate a configuration file for the interface based on the changes made in Nautobot.
- **Debugging**: Writes debug information to files for troubleshooting.

#### 4. **Jinja Templating**
I am using a jinja2 template to help render the configurations I want pushed to my switch. I use Jinja templates because it is an easy way to maintain standards while maintaining a programmatic approach. 

The Jinja template approach is also reusable and we could use this same template with ansible without any changes at all. Its actually where this template has been used before.

```
{%raw%}
{% if interface.mode == "access" and interface.enabled and 'GigabitEthernet' in interface.name or interface.mode == "access" and interface.enabled and 'Port-Channel' in interface.name %}
interface {{ interface.name }}
    {% if interface.description %}
 description {{ interface.description }}
    {% endif %}
 switchport mode access
 switchport access vlan {{ interface.untagged_vlan.vid }}
 spanning-tree portfast
 no cdp enable
 no shut
!
{% elif interface.mode == 'TAGGED' or interface.mode == 'TAGGED_ALL' and interface.enabled and 'GigabitEthernet' in interface.name %}
interface {{ interface.name }}
    {% if interface.description %}
 description {{ interface.description }}
    {% endif %}
    {% if interface.untagged_vlan %}
 switchport trunk native vlan {{ interface.untagged_vlan.vid }}
    {% endif %}
    {% if interface.tagged_vlans %}
 switch trunk allowed vlan {{ interface.tagged_vlans | map(attribute='vid') | join(',') }}
    {% endif %}
 switchport mode trunk
 spanning-tree portfast trunk
    {% if interface.lag %}
 channel-group {{ interface.lag.name | replace('Port-Channel', '') }} mode active
    {% endif %}
 no shut
!
{% elif interface.mode == 'TAGGED' or interface.mode == 'TAGGED_ALL' and interface.enabled and 'Port-Channel' in interface.name %}
interface {{ interface.name }}
    {% if interface.description %}
 description {{ interface.description }}
    {% endif %}
    {% if interface.untagged_vlan %}
 switchport trunk native vlan {{ interface.untagged_vlan.vid }}
    {% endif %}
    {% if interface.tagged_vlans %}
 switch trunk allowed vlan {{ interface.tagged_vlans | map(attribute='vid') | join(',') }}
    {% endif %}
 switchport mode trunk
 spanning-tree portfast trunk
 no shut
!
{% elif interface.mode is none and interface.enabled and 'GigabitEthernet' in interface.name %}
interface {{ interface.name.split('.')[0] }}
    {% if interface.description %}
 description {{ interface.description }}
    {% endif %}
 no switchport
    {% if interface.vrf %}
 vrf forwarding {{ interface.vrf.name }}
    {% endif %}
    {% if interface.ip_addresses %}
        {% for addr in interface.ip_addresses %}
            {% if addr.address %}
 ip address {{ addr.address | ipaddr('address') }} {{ addr.address | ipaddr('netmask') }}
                {% for tag in addr.tags %}
                    {% if tag.slug %}
                        {% if 'ospf' in tag.slug %}
 ip ospf {{ devices[0].config_context.ospf.id }} area {{ tag.slug | replace('ospf_area_', '') }}
                        {% elif 'p2p' in tag.slug %}
 ip ospf network point-to-point
                        {% endif %}
                    {% endif %}
                {% endfor %}
            {% endif %}
        {% endfor %}
    {% endif %}
    {% if devices[0].config_context.acl and interface.name in devices[0].config_context.acl.interfaces %}
 ip access-group {{ devices[0].config_context.acl.interfaces[interface.name].acl }} {{ devices[0].config_context.acl.interfaces[interface.name].direction }}
    {% endif %}
    {% if interface.dhcp_helper %}
 ip helper-address {{ interface.dhcp_helper }}
    {% endif %}
    {% if interface.vrrp_group %}
 vrrp {{ interface.vrrp_group }} ip {{ interface.vrrp_primary_ip }}
 vrrp {{ interface.vrrp_group }} description {{ interface.vrrp_description }}
 vrrp {{ interface.vrrp_group }} priority {{ interface.vrrp_priority }}
 vrrp {{ interface.vrrp_group }} timers learn
    {% endif %}
 no shut
!
{% elif interface.mode is none and interface.enabled and 'Vlan' in interface.name %}
interface {{ interface.name.split('.')[0] }}
    {% if interface.description %}
 description {{ interface.description }}
    {% endif %}
    {% if interface.vrf %}
 vrf forwarding {{ interface.vrf.name }}
    {% endif %}
    {% if interface.ip_addresses %}
        {% for addr in interface.ip_addresses %}
            {% if addr.address and '.' in addr.address and loop.index == 1 %}
 ip address {{ addr.address | ipaddr('address') }} {{ addr.address | ipaddr('netmask') }}
            {% elif addr.address and '.' in addr.address and loop.index != 1 %}
 ip address {{ addr.address | ipaddr('address') }} {{ addr.address | ipaddr('netmask') }} secondary
            {% elif addr.address and ':' in addr.address %}
 ipv6 address {{ addr.address }}
            {% endif %}
        {% endfor %}
    {% endif %}
    {% if devices[0].config_context.acl and interface.name in devices[0].config_context.acl.interfaces %}
 ip access-group {{ devices[0].config_context.acl.interfaces[interface.name].acl }} {{ devices[0].config_context.acl.interfaces[interface.name].direction }}
    {% endif %}
    {% if interface.dhcp_helper %}
 ip helper-address {{ interface.dhcp_helper }}
    {% endif %}
    {% if interface.vrrp_group %}
 vrrp {{ interface.vrrp_group }} ip {{ interface.vrrp_primary_ip }}
 vrrp {{ interface.vrrp_group }} description {{ interface.vrrp_description }}
 vrrp {{ interface.vrrp_group }} priority {{ interface.vrrp_priority }}
 vrrp {{ interface.vrrp_group }} timers learn
    {% endif %}
 no shut
!
{% elif interface.label == "mgmt" %}
interface {{ interface.name }}
    {% if interface.description %}
 description {{ interface.description }}
    {% endif %}
 no switchport
 vrf forwarding MGMT
    {% if interface.ip_addresses %}
        {% for addr in interface.ip_addresses %}
            {% if addr.address %}
 ip address {{ addr.address | ipaddr('address') }} {{ addr.address | ipaddr('netmask') }}
 negotiation auto
 no cdp enable
 no shutdown
!
            {% endif %}
        {% endfor %}
    {% endif %}
{% else %}
interface {{ interface.name }}
 description "NOT IN USE"
 shutdown
!
{% endif %}
end
!
{%endraw%}
```

#### 4. **Pushing Configuration**

```python
def push_config(self, device, config):
    """Push the generated configuration to the device using Napalm."""
    try:
        driver_name = device.platform.network_driver_mappings.get("napalm")
        if not driver_name:
            self.logger.error(f"No Napalm driver found for platform '{device.platform.name}'.")
            raise Exception(f"No Napalm driver found for platform '{device.platform.name}'.")
        driver = get_network_driver(driver_name)
    except (AttributeError, ModuleImportError) as e:
        self.logger.error(f"Cannot import Napalm driver for platform '{device.platform.name}'. Is the library installed?")
        raise

    napalm_device = driver(
        hostname=str(device.primary_ip.address.ip),
        username=settings.NAPALM_USERNAME,
        password=settings.NAPALM_PASSWORD,
    )

    try:
        napalm_device.open()
        napalm_device.load_merge_candidate(config=config)
        napalm_device.commit_config()
        self.logger.info(f"Configuration pushed successfully to {device.name}.")
    except (ConnectionException, CommandErrorException) as e:
        self.logger.error(f"Failed to push configuration to {device.name}: {str(e)}")
        raise
    finally:
        napalm_device.close()
```

- **Napalm Interaction**: Connects to the network device and applies the configuration using Napalm. Handles exceptions if anything goes wrong.
### ** What is Napalm and why use it?**
 Napalm (Network Automation and Programmability Abstraction Layer with Multivendor support) is a powerful library used for automating network device management across various vendors. Here's why Napalm is an excellent choice for network automation:
1. Its already included with Nautobot
2. Vendor Agnostic: Napalm supports multiple network device vendors, allowing you to use a unified API to interact with different hardware. This reduces the complexity of managing various vendor-specific configurations.
3. Consistency: Provides a consistent way to manage network configurations and states, regardless of the underlying vendor, which simplifies automation tasks and improves reliability.
4. Rich Functionality: Napalm offers features such as loading configurations, validating them, and committing changes. This comprehensive functionality covers a wide range of network management tasks.
5. Error Handling: Built-in exception handling and logging make it easier to debug issues and maintain robust automation workflows. Will role back a configuration if it receives an error when deploying
6. Community and Support: Napalm is an open-source project with active community support, which means ongoing improvements and access to a wealth of shared knowledge.

#### 5. **Running the Job**
```python
def run(self, object_change):
    """Run method for executing the job."""
    self.logger.info(f"ObjectChange details: {object_change}")

    if not isinstance(object_change.changed_object, Interface):
        self.logger.error("The object change is not related to an Interface.")
        raise Exception("The object change is not related to an Interface.")
    
    interface = object_change.changed_object
    device = interface.device

    self.logger.info(f"Interface: {interface}")
    self.logger.info(f"Device: {device}")
    
    if not device.primary_ip:
        self.logger.error(f"Device {device.name} is missing Primary IP")
        raise Exception(f"Device {device.name} is missing Primary IP")

    if not device.platform:
        self.logger.error(f"Device {device.name} platform not set.")
        raise Exception(f"Device {device.name} platform not set.")

    config = self.generate_config(interface, object_change)
    self.push_config(device, config)
```

- **Job Execution**: Checks that the object change relates to an interface, generates the configuration, and applies it to the device.

#### 6. **Registering the Job**
```python
register_jobs(UpdateSwitchInterfaceJobHookReceiver)
```
- **Job Registration**: Registers the Jobhook with Nautobot, making it available for execution.

#### 7. **Where to place the code and how to get it working**
The Python code should be stored in the jobs folder of your nautobot root. Jobs can be placed there or synced using git. Once the file is in place you will want to run ```nautobot-server post_upgrade```. This will pickup the python code in your jobs folder and if there are no issue with the code register it as a Nautobot Job. 

Once the Job has been registered you will need to enable the Job so that it can be scheduled to run
<img src="/assets/img/2024-7-28/jobs-list.webp" alt="">
<img src="/assets/img/2024-7-28/enable-job.webp" alt="">

After the Job has been enabled we need to add a new Jobhook with our newly enabled Job.
<img src="/assets/img/2024-7-28/jobhook.webp" alt="">

Make sure you select the correct Content Type, in our case we want to watch for the dcim.interface. We also only want to run this when an existing interface is being updated.



## The Results
Below is a output from one of my switches interface descriptions. Lets assume I want to add a new connection to port Gi1/0/17, normally I would need to update Nautobot and then perform a few commands on the switch as well.
```
HomeSwitch02#show int description 
Interface                      Status         Protocol Description
Gi1/0/17                       admin down     down     "NOT IN USE"
Gi1/0/18                       admin down     down     "NOT IN USE"
```

With the Nauotbot JobHook when I make an update to the interface of a device, the Jobhook will detect the change and then deploy this configuration to the switch.

<img src="/assets/img/2024-7-28/before-interface-nb.webp" alt="">

Updating the interface in Nautobot
<img src="/assets/img/2024-7-28/updating-interface-nb.webp" alt="">

Job Results output
<img src="/assets/img/2024-7-28/nb-job-results.webp" alt="">

Switch results
```
HomeSwitch02#
*Jul 29 01:28:54.163: %SEC_LOGIN-5-LOGIN_SUCCESS: Login Success [user: cisco] [Source: 192.168.17.3] [localport: 22] at 18:28:54 MST Sun Jul 28 2024
*Jul 29 01:28:55.298: %SEC_LOGIN-5-LOGIN_SUCCESS: Login Success [user: cisco] [Source: 192.168.17.3] [localport: 22] at 18:28:55 MST Sun Jul 28 2024
*Jul 29 01:28:57.941: %SYS-5-CONFIG_I: Configured from console by cisco on vty1 (192.168.17.3)
*Jul 29 01:29:01.750: %SYS-5-CONFIG_P: Configured programmatically by process SSH Process from console as cisco on vty1 (192.168.17.3)
*Jul 29 01:29:01.753: %SYS-5-CONFIG_C: Running-config file is Modified 
*Jul 29 01:29:03.736: %LINK-3-UPDOWN: Interface GigabitEthernet1/0/17, changed state to down
*Jul 29 01:29:04.512: %SYS-5-CONFIG_I: Configured from console by cisco on vty1 (192.168.17.3)
*Jul 29 01:29:04.547: %SYS-6-LOGOUT: User cisco has exited tty session 3(192.168.17.3)sh run int gi1/0/17
Building configuration...

Current configuration : 167 bytes
!
interface GigabitEthernet1/0/17
 description TESTING NAUTOBOT JobHook
 switchport access vlan 14
 switchport mode access
 no cdp enable
 spanning-tree portfast
end

HomeSwitch02#show int description
Gi1/0/17                       down           down     TESTING NAUTOBOT JobHook
Gi1/0/18                       admin down     down     "NOT IN USE"
```
