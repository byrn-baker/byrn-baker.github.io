---
title: Unleashing the Power of Nautobot Dynamic Inventory for Ansible
date: 2024-04-27 12:00:00 -500
categories: [100DaysOfHomeLab]
tags: [NetworkAutomation,NetworkSourceOfTruth,nautobot,AutomationPlatform,NautobotTutorials,100DaysOfHomeLab]
lab_vps_banner: true
image:
  path: /assets/img/headers/source_of_truth-gif.gif
---
## Unleashing the Power of Nautobot Dynamic Inventory for Ansible
I mentioned the [Nautobot Ansible module](https://github.com/nautobot/nautobot-ansible) briefly in the previous post, explaining how it can be utilized to manage data within Nautobot or even add new or update existing data. Additionally, it can serve as a dynamic inventory for Ansible. This is where the GraphQL part of Nautobot becomes extremely powerful.

## Nautobot Dynamic Inventory
Install the ansible collection
```bash
ansible-galaxy collection install networktocode.nautobot
```

Create an inventory file using the nautobot.gql_inventory module. In this inventory file we need to include a few things
- plugin: This tells the Ansible dynamic inventory how to interact with Nautobot
- api_endpoint: Where to interact with Nautobot
- token: How to authorize the interaction
- query: This is how we request what is required from Nautobot, in our case we just need the device, device_id, role, and platform.
- group_by: This is used to group the hosts

```yaml
---
plugin: networktocode.nautobot.gql_inventory
api_endpoint: https://nautobot.example.com
token: "API-TOKEN"
query:
  devices:
    role: name
    id:
group_by:
  - role.name
```

If you test this with ```ansible-inventory -v --list --yaml -i inventory/inventory.yml``` you should see output like a typical static inventory. 
Two important thing to remember:
- you must set the primary ipv4 for each device in Nautobot if you need the IP address in the ansible_host key.
  - **After testing with just a primary ipv6 that the module only places an IPv4 address in the ansible_host key**.
- You must set the token as an environmental variable named 'NAUTOBOT_TOKEN' if you want to leave your token out of the inventory file.

```yaml
all:
  children:
    backbone_core_router:
      hosts:
        bbr01:
          ansible_host: 192.168.18.101
          ansible_network_os: cisco.ios.ios
          id: 089377b0-5555-4ff4-8fc1-e690fb6595f2
          name: bbr01
          platform:
            napalm_driver: ios
          primary_ip4:
            host: 192.168.18.101
          role:
            name: backbone_core_router
        bbr02:
          ansible_host: 192.168.18.102
          ansible_network_os: cisco.ios.ios
          id: 77b1110e-cb6a-4674-b131-016837ac15d5
          name: bbr02
          platform:
            napalm_driver: ios
          primary_ip4:
            host: 192.168.18.102
          role:
            name: backbone_core_router
        bbr03:
          ansible_host: 192.168.18.103
          ansible_network_os: cisco.ios.ios
          id: dedf2eab-01c4-48a0-949f-e9d0b0f39ad7
          name: bbr03
          platform:
            napalm_driver: ios
          primary_ip4:
            host: 192.168.18.103
          role:
            name: backbone_core_router
        bbr04:
          ansible_host: 192.168.18.104
          ansible_network_os: cisco.ios.ios
          id: f0012d1c-c42c-43b1-937b-975dce8c50fa
          name: bbr04
          platform:
            napalm_driver: ios
          primary_ip4:
            host: 192.168.18.104
          role:
            name: backbone_core_router
    backbone_datacenter_router:
      hosts:
        bdr01-east:
          ansible_host: 192.168.18.106
          ansible_network_os: cisco.ios.ios
          id: 3ef918b0-cfbc-4686-a6dc-18a6ea3e0127
          name: bdr01-east
          platform:
            napalm_driver: ios
          primary_ip4:
            host: 192.168.18.106
          role:
            name: backbone_datacenter_router
        bdr01-west:
          ansible_host: 192.168.18.105
          ansible_network_os: cisco.ios.ios
          id: 40e23137-8ec4-4c98-99c9-cb49cd728d2a
          name: bdr01-west
          platform:
            napalm_driver: ios
          primary_ip4:
            host: 192.168.18.105
          role:
            name: backbone_datacenter_router
    datacenter_router:
      hosts:
        dc-east-rtr01:
          ansible_host: 192.168.18.113
          ansible_network_os: cisco.ios.ios
          id: 8e2a4a9e-34ed-416c-8f5e-727d8e3977c8
          name: dc-east-rtr01
          platform:
            napalm_driver: ios
          primary_ip4:
            host: 192.168.18.113
          role:
            name: datacenter_router
        dc-west-rtr01:
          ansible_host: 192.168.18.111
          ansible_network_os: cisco.ios.ios
          id: b3390317-8f50-4a9a-9070-1bb30e6db9a7
          name: dc-west-rtr01
          platform:
            napalm_driver: ios
          primary_ip4:
            host: 192.168.18.111
          role:
            name: datacenter_router
    datacenter_spine:
      hosts:
        dc-east-spine01:
          ansible_host: 192.168.18.114
          ansible_network_os: cisco.ios.ios
          id: 2cfa8266-d66c-4133-a438-75b7bb5df722
          name: dc-east-spine01
          platform:
            napalm_driver: ios
          primary_ip4:
            host: 192.168.18.114
          role:
            name: datacenter_spine
        dc-west-spine01:
          ansible_host: 192.168.18.112
          ansible_network_os: cisco.ios.ios
          id: 8776944a-53ee-4850-9bbf-73ade94f951c
          name: dc-west-spine01
          platform:
            napalm_driver: ios
          primary_ip4:
            host: 192.168.18.112
          role:
            name: datacenter_spine
    market_core_router:
      hosts:
        market-router01:
          ansible_host: 192.168.18.109
          ansible_network_os: cisco.ios.ios
          id: 1c577231-b9b0-44bf-bfae-3625c553063e
          name: market-router01
          platform:
            napalm_driver: ios
          primary_ip4:
            host: 192.168.18.109
          role:
            name: market_core_router
        market-router02:
          ansible_host: 192.168.18.110
          ansible_network_os: cisco.ios.ios
          id: 460f8f18-7199-4b52-b1f4-c1b64839b0c9
          name: market-router02
          platform:
            napalm_driver: ios
          primary_ip4:
            host: 192.168.18.110
          role:
            name: market_core_router
    master:
      hosts:
        lab-k3s01:
          ansible_host: 172.16.221.38
          id: 890325f6-1383-4e0d-9838-ff8714bfe8f1
          name: lab-k3s01
          primary_ip4:
            host: 172.16.221.38
          role:
            name: master
        lab-k3s02:
          ansible_host: 172.16.221.39
          id: 8185e66b-34e9-4861-a039-c21cf867761d
          name: lab-k3s02
          primary_ip4:
            host: 172.16.221.39
          role:
            name: master
        lab-k3s03:
          ansible_host: 172.16.221.40
          id: 6d7905e1-ee2a-4488-b19e-6759b19bf9df
          name: lab-k3s03
          primary_ip4:
            host: 172.16.221.40
          role:
            name: master
    node:
      hosts:
        east-lab-k3s01:
          ansible_host: 172.16.223.42
          id: 630fa57b-deed-42a5-9e43-907c0cb3141c
          name: east-lab-k3s01
          primary_ip4:
            host: 172.16.223.42
          role:
            name: node
        west-lab-k3s01:
          ansible_host: 172.16.222.41
          id: 19264960-0049-4b37-8f42-920111c6d337
          name: west-lab-k3s01
          primary_ip4:
            host: 172.16.222.41
          role:
            name: node
    region_core_router:
      hosts:
        region-router01:
          ansible_host: 192.168.18.107
          ansible_network_os: cisco.ios.ios
          id: cea0cc0b-1dc0-4d6f-975f-f0c6bd84d4c4
          name: region-router01
          platform:
            napalm_driver: ios
          primary_ip4:
            host: 192.168.18.107
          role:
            name: region_core_router
        region-router02:
          ansible_host: 192.168.18.108
          ansible_network_os: cisco.ios.ios
          id: c0f6a4cf-c882-47dd-af14-23ff1d67b95b
          name: region-router02
          platform:
            napalm_driver: ios
          primary_ip4:
            host: 192.168.18.108
          role:
            name: region_core_router
```

## Configuration Template Role
Now that we have the inventory sorted, lets start with the playbook, I will be using roles to organize the Ansible tasks, the first will build the configurations into a file and then push that file as a full configuration to the router.

```yaml
---
- name: Build Router Configurations
  hosts: bbr01
  gather_facts: false
  connection: network_cli

  roles:
    - role: generate_configs
```

The role folder structure should look like this
```
role
├── tasks
│   └── main.yml
├── templates
│   ├── cisco_ios.j2
│   └── ios
└── vars
    └── main.yml
```
## Configuration Template Role Task
In the tasks/main.yml we need to query Nautbot for the device information, make sure the router_configs directory exists, and if not create it, build the router config and store it the router_configs folder.
```yaml
---
- name: Get data from Nautobot
  networktocode.nautobot.query_graphql:
    url: "{{ nb_url }}"
    token: "{{ nb_token }}"
    query: "{{ query_string }}"
  register: "nb_device"
  delegate_to: localhost

- name: Ensure router_configs directory exists
  file:
    path: "./router_configs"
    state: directory
  delegate_to: localhost

- name: Build Cisco Configurations
  template:
    src: cisco_ios.j2
    dest: "./router_configs/{{ inventory_hostname }}.cfg"
  delegate_to: localhost
```
## Configuration Template Role Vars
In the vars/main.yml I have stored the Nautobot query as a string. I use this to get absolutely everything I might ever need, because its fast so you might as well just get it all while I am there.
```yaml
query_string: |
  {
    device(id:"{{ hostvars[inventory_hostname]['id'] }}") {
      config_context
      name
      vrf_assignments {
        name
      }
      primary_ip4 {
        address
      }
      primary_ip6 {
        address
      }
      role {
        name
      }
      platform {
        name
        manufacturer {
          name
        }
        network_driver
      }
      location {
        name
        vlans {
          id
          name
          vid
        }
        vlan_groups {
          id
        }
      }
      interfaces {
        description
        mac_address
        enabled
        vrf {
          name
        }
        name
        mode
        cf_ospf_area
        cf_ospf_cost
        cf_ospf_network
        cf_ospf_priority
        ip_addresses {
          address
        }
        connected_circuit_termination {
          circuit {
            cid
            commit_rate
            provider {
              name
            }
          }
        }
        tagged_vlans {
          vid
        }
        untagged_vlan {
          vid
        }
        cable {
          termination_a_type
          status {
            name
          }
          color
        }
        tagged_vlans {
          locations {
            name
          }
          id
        }
        tags {
          id
        }
      }
    }
  }
```

<img src="/assets/img/2024-04-28/folder structure.png" alt="">

## Configuration Template Role Templates
Next we need to start building the Jinja templates that will be used to generate the router configurations. I organize these templates based on the device platform, this way it keeps everything organized and you keep more than one device template here. 

In templates/cisco_ios.j2 I check the platform name and the role of the device so that I can make specific templates for each. I re-use what I can, but often I find it easier to separate out the templates so that they do not become to large to manage and understand.

Each platform template could be placed inside the ios folder in platform_templates. At this time I only have a single platform, but this can easily grow as needed.

```jinja
{%raw%}
#jinja2: lstrip_blocks: "True", trim_blocks: "True"
{% set device = nb_device["data"]["device"] %}
{% if device['platform']['name'] == 'Cisco IOS' %}
{% if device["role"]["name"] == "backbone_core_router" %}
{% include "./ios/platform_templates/ios_router.j2"%}
{% elif device["role"]["name"] == "backbone_datacenter_router" %}
{% include "./ios/platform_templates/ios_router.j2"%}
{% elif device["role"]["name"] == "region_core_router" %}
{% include "./ios/platform_templates/ios_router.j2"%}
{% elif device["role"]["name"] == "market_core_router" %}
{% include "./ios/platform_templates/ios_router.j2"%}
{% elif device["role"]["name"] == "datacenter_router" %}
{% include "./ios/platform_templates/ios_router.j2"%}
{% elif device["role"]["name"] == "datacenter_spine" %}
{% include "./ios/platform_templates/ios_router.j2"%}
{% elif device["role"]["name"] == "datacenter_switch" %}
{% include "./ios/platform_templates/ios_router.j2"%}
{% endif %}
{% endif %}
{%endraw%}
```

In the platform_templates/ios_router.j2, this will look similar to what you would expect to see on a cisco router after performing a '''show run''' command. I replace the sections of the configuration with additional templates as needed, again to help keep the template from growing to large and readable.

```jinja
{% raw %}
version 15.4
service timestamps debug datetime msec
service timestamps log datetime msec
no service password-encryption
!
!
{% include './ios/hostname.j2' %}

!
boot-start-marker
boot-end-marker
!
aqm-register-fnf
!
{% include './ios/dns.j2' %}

!
{% if device['config_context']['ntp'] is defined %}
{% include './ios/ntp.j2' %}
{% endif %}
!
{% if device['config_context']['snmp'] is defined %}
{% include './ios/snmp.j2' %}
{% endif %}

{% include './ios/aaa.j2' %}

!
mmi polling-interval 60
no mmi auto-configure
no mmi pvc
mmi snmp-timeout 180
!
{% if device['vrf_assignments'] is not none %}
{% for vrf in device['vrf_assignments'] %}
vrf definition {{ vrf['name'] }}
 !
 address-family ipv4
 exit-address-family
!
{% endfor %}
!
!
{% endif %}

{% include './ios/local_user.j2' %}

!
redundancy
!
!
ip ssh source-interface Ethernet0/3
ip ssh version 2
ip scp server enable
! 
!
!
!
!
!         
!
!
!
!
ipv6 unicast-routing
!
!
!
!
{% include './ios/interfaces.j2' %}

!
ip forward-protocol nd
!
!
no ip http server
no ip http secure-server
!         
!
!
!
control-plane
!
!
!
!
!
!
!
!
{% if device['config_context']["routes"] is defined %}
{% if device['config_context']["routes"]["static"] is defined %}
{% for static in device['config_context']["routes"]["static"] %}
{{ static }}
{% endfor %}
{% endif %}
{% endif %}
!
!
{% if device['config_context']['prefix_lists'] is defined %}
{% include './ios/prefix_list.j2'%}
{% endif %}

!
{% if device['config_context']['route_maps'] is defined %}
{% include './ios/route_map.j2'%}
{% endif %}

!
{% if device['config_context']["bgp"] is defined %}
{% include './ios/bgp.j2' %}
{% endif %}
!
{% if device['config_context']["ospf"] is defined %}
{% include './ios/ospf.j2' %}
{% endif %}

!
{% include './ios/services.j2' %}

!
end
{% endraw %}
```

Some of these templates are short while others are a little more complicated as you will see. From the top the first template is ios/hostname.j2

```jinja
{% raw %}
hostname {{ device['name'].split('.')[0] }}

{% endraw %}
```

ios/dns.j2 - some of these for now just have simple text as a placeholder, but this could easily be stored in Nauotbot as a config Context.
```jinja2
ip domain-name example.com
```

ios/ntp.j2
```jinja
{% raw %}
{% for server in device['config_context']['ntp'] %}
{% if server['prefer'] %}
ntp server {{ server['ip'] }} prefer
{% else %}
ntp server {{ server['ip'] }}
{% endif %}
{% endfor %}

{% endraw %}
```

ios/snmp.j2
```jinja
{% raw %}
{% for community in device['config_context']["snmp"]["community"] %}
snmp-server community {{ community["name"] }} {{ community["role"] }}
{% endfor %}
snmp-server location {{ config_context["snmp"]["location"] }}
snmp-server contact {{ config_context["snmp"]["contact"] }}
{% for host in device['config_context']["snmp"]["host"] %}
snmp-server host {{ host["ip"] }} version {{ host["version"] }} {{ host["community"] }}
{% endfor %}
{% endraw %}
```

ios/aaa.j2
```jinja
aaa authorization exec default local
!
no aaa root
```

ios/local_user.j2
```jinja
username cisco privilege 15 password 0 cisco

```
ios/interfaces.j2 - Here I use the same method to separate out the interface to keep this from becoming to big and hard to read.
```jinja
{%raw%}
{% for interface in device['interfaces'] %}
interface {{ interface["name"] }}
{% if interface["description"] is defined and interface["description"] != "" %}
   description {{ interface["description"] }}
{% endif %}
{% if 'lan' in interface["name"] %}
{% include "./ios/_svi.j2" %}
{% elif 'thernet' in interface["name"] %}
{% include "./ios/_physical.j2" %}
{% elif 'Loop' in interface["name"] %}
{% include "./ios/_loopback.j2" %}
{% elif 'anagement' in interface["name"] %}
{% include "./ios/_mgmt.j2" %}
{% endif %}
{% endfor %}

{%endraw%}
```
ios/_svi.j2
```jinja
{%raw%}
{% if interface["ip_addresses"] | length > 0 %}
{% for addr in interface["ip_addresses"] %}
{% if addr["address"] is defined and '.' in addr["address"] %}
   ip address {{ addr["address"] }}
{% elif addr["address"] is defined and ':' in addr["address"] %}
   ipv6 address {{ addr["address"] }}
{% endif %}
{% endfor %}
{% else %}
   no ip address
{% endif %}
{% if interface["enabled"] == true %}
   no shutdown
{% endif %}


{%endraw%}
```

ios/_physical.j2 - Here you an see that I can pull ACLs type information from the config context of the device, and then I am checking the device interface data for specifics on how to configure each interface. 
```jinja
{%raw%}
{% if device['config_context']["acl"] is defined %}
   {% if device['config_context']["acl"]["interfaces"] is defined %}
      {% if device['config_context']["acl"]["interfaces"][interface["name"]] is defined %}
   ip access-group {{ device['config_context']["acl"]["interfaces"][interface["name"]]["acl"] }} {{ device['config_context']["acl"]["interfaces"][interface["name"]]["direction"] }}
      {% endif %}
   {% endif %}
{% endif %}
{% if interface["mode"] == 'ACCESS' %}
   switchport mode access
   switchport access vlan {{ interface["untagged_vlan"]['vid'] }}
   no shutdown
{% elif interface["mode"] == 'TAGGED_ALL' %}
   switchport mode trunk
   no shutdown
{% elif interface["ip_addresses"] | length > 0 %}
   {% if interface['vrf']['name'] is defined %}
   vrf forwarding {{ interface['vrf']['name']}}
   {% endif %}
   no shutdown
   {% if interface["mac_address"] != none %}
   mac-address {{ interface["mac_address"] }}
   {% endif %}
   {% if interface["ip_addresses"] | length > 0 %}
      {% for addr in interface["ip_addresses"] %}
         {% if addr["address"] is defined and '.' in addr["address"]%}
   ip address {{ addr["address"] | ipaddr('address') }} {{ addr["address"] | ipaddr('netmask') }}
            {% if interface['cf_ospf_area'] is not none %}
   ip ospf {{ device['config_context']['ospf']['process_id'] }} area {{ interface['cf_ospf_area'] }}
              {% if interface['cf_ospf_cost'] is not none %}
   ip ospf cost {{ interface['cf_ospf_cost'] }}
              {% endif %}
              {% if interface['cf_ospf_network'] is not none %}
   ip ospf network {{ interface['cf_ospf_network'] }}
              {% endif %}
            {% endif %}
         {% elif addr["address"] is defined and ':' in addr["address"]%}
   ipv6 address {{ addr["address"] }}
            {% if interface['cf_ospf_area'] is not none %}
   ospfv3 {{ device['config_context']['ospf']['process_id'] }} ipv6 area {{ interface['cf_ospf_area'] }}
              {% if interface['cf_ospf_cost'] is not none %}
   ospfv3 cost {{ interface['cf_ospf_cost'] }}
              {% endif %}
              {% if interface['cf_ospf_network'] is not none %}
   ospfv3 network {{ interface['cf_ospf_network'] }}
              {% endif %}
            {% endif %}
         {% endif %}
      {% endfor %}
   {% endif %}
{% endif %}
{% if interface["enabled"] == false %}
   shutdown
{% endif %}
{%endraw%}
```

ios/_mgmt.j2
```jinja
{%raw%}
{% if interface["description"] | length > 1 %}
   description {{ interface["description"] }}
{% endif %}
   vrf MGMT
{% if interface["ip_addresses"] | length > 0 %}
{% for addr in interface["ip_addresses"] %}
{% if addr["address"] is defined %}
   ip address {{ addr["address"] | ipaddr('address') }} {{ addr["address"] | ipaddr('netmask') }}
{% endif %}
{% endfor %}
{% else %}
   no ip address
{% endif %}
{% if interface["enabled"] == false %}
   shutdown
{% endif %}


{%endraw%}
```

ios/_loopback.j2
```jinja
{%raw%}
{% if interface["ip_addresses"] | length > 0 %}
{% for addr in interface["ip_addresses"] %}
{% if addr["address"] is defined and '.' in addr["address"]%}
   ip address {{ addr["address"] | ipaddr('address') }} {{ addr["address"] | ipaddr('netmask') }}
{% if interface['cf_ospf_area'] is not none %}
   ip ospf {{ device['config_context']['ospf']['process_id'] }} area {{ interface['cf_ospf_area'] }}
{% endif %}
{% elif addr["address"] is defined and ':' in addr["address"]%}
   ipv6 address {{ addr["address"] }}
{% if interface['cf_ospf_area'] is not none %}
   ospfv3 {{ device['config_context']['ospf']['process_id'] }} ipv6 area {{ interface['cf_ospf_area'] }}
{% endif %}
{% endif %}
{% endfor %}
{% else %}
   no ip address
{% endif %}
{% if interface["enabled"] == false %}
   no shutdown
{% endif %}
{%endraw%}
```

ios/prefix_list.j2
```jinja
{%raw%}
{% for prefix in device['config_context']['prefix_lists'] %}
  {% for ip in prefix['prefixes'] %}
ip prefix-list {{ prefix['name'] }} seq {{ loop.index0 * 10 + 10 }} {{ ip['action']}} {{ ip['ip']}}
  {% endfor %}
{% endfor %}
{%endraw%}
```

ios/route_map.j2
```jinja
{%raw%}
{% for map in device['config_context']['route_maps'] %}
  {% for match in map['match'] %}
route-map {{ map['name'] }} {{map['action'] }} 10
    {% if match['prefix_list'] is defined %}
   match ip address prefix-list {{ match['prefix_list'] }}
    {% endif %}
  {% endfor %}
{% endfor %}
{%endraw%}
```

ios/bgp.j2
```jinja
{%raw%}
router bgp {{ device['config_context']["bgp"]["asn"] }}
{% for interface in device["interfaces"] %}
  {% if 'Loop' in interface["name"] %}
    {% for addr in interface.ip_addresses %}
      {% if addr.address is defined and '.' in addr.address %}
      {% set rid = addr.address | ipaddr('address') %}
   bgp router-id {{ rid }}
      {% endif %}
    {% endfor %}
  {% endif %}
{% endfor %}
{% for group in device['config_context']["bgp"]['peer_groups'] %}
   neighbor {{ group['group'] }}-ipv4 peer-group
   neighbor {{ group['group'] }}-ipv4 remote-as {{ group['remote_as'] }}
   neighbor {{ group['group'] }}-ipv4 update-source {{ group['update_source'] }}
   neighbor {{ group['group'] }}-ipv4 next-hop-self
{% endfor %}
{% for group in device['config_context']["bgp"]['peer_groups'] %}
   neighbor {{ group['group'] }}-ipv6 peer-group
   neighbor {{ group['group'] }}-ipv6 remote-as {{ group['remote_as'] }}
   neighbor {{ group['group'] }}-ipv6 update-source {{ group['update_source'] }}
{% endfor %}
{% for neighbor in device['config_context']["bgp"]["neighbors"] %}
  {% if neighbor["peer_group"] is defined and '.' in neighbor["peer"] %}
   neighbor {{ neighbor["peer"] }} peer-group {{ neighbor["peer_group"] }}-ipv4
  {% elif neighbor["peer_group"] is defined and ':' in neighbor["peer"] %}
   neighbor {{ neighbor["peer"] }} peer-group {{ neighbor["peer_group"] }}-ipv6
  {% elif neighbor["peer_group"] is not defined and '.' in neighbor["peer"] %}
   neighbor {{ neighbor["peer"] }} remote-as {{ neighbor["remote_as"] }}
  {% endif %}
{% endfor %}
   address-family ipv4 unicast
{% for neighbor in device['config_context']["bgp"]["neighbors"] %}
  {% if neighbor["peer_group"] is defined and '.' in neighbor["peer"] %}
   neighbor {{ neighbor["peer"] }} activate
  {% elif neighbor["peer_group"] is defined and ':' in neighbor["peer"] %}
   no neighbor {{ neighbor["peer"] }} activate
  {% elif neighbor["peer_group"] is not defined %}
   neighbor {{ neighbor["peer"] }} activate
  {% endif %}
{% endfor %}
{% if device['config_context']["bgp"]["redistribute"] is defined and device['config_context']["bgp"]["redistribute"] | length > 0 %}
  {% for type in device['config_context']["bgp"]["redistribute"] if type['route_map'] is defined %}
   redistribute {{ type["type"] }} route-map {{ type['route_map'] }}
  {% else %}
   redistribute {{ type["type"] }}
  {% endfor %}
{% endif %}
   address-family ipv6 unicast
{% for group in device['config_context']["bgp"]['peer_groups'] %}
   neighbor {{ group['group'] }}-ipv6 next-hop-self
{% endfor %}
{% for neighbor in device['config_context']["bgp"]["neighbors"] %}
  {% if neighbor["peer_group"] is defined and ':' in neighbor["peer"] %}
   neighbor {{ neighbor["peer"] }} activate
  {% elif neighbor["peer_group"] is not defined and ':' in neighbor["peer"] %}
   neighbor {{ neighbor["peer"] }} activate
  {% endif %}
{% endfor %}
{% if device['config_context']["bgp"]["redistribute"] is defined and device['config_context']["bgp"]["redistribute"] | length > 0 %}
  {% for type in device['config_context']["bgp"]["redistribute"] if type['route_map'] is defined %}
   redistribute {{ type["type"] }} route-map {{ type['route_map'] }}
  {% else %}
   redistribute {{ type["type"] }}
  {% endfor %}
{% endif %}
{%endraw%}
```

ios/ospf.j2
```jinja
{%raw%}
router ospf {{ device['config_context']["ospf"]['process_id'] }}
{% for interface in device["interfaces"] %}
{% if 'Loop' in interface["name"] %}
{% for addr in interface.ip_addresses %}
{% if addr.address is defined and '.' in addr.address %}
{% set rid = addr.address | ipaddr('address') %}
   router-id {{ rid }}
{% endif %}
{% endfor %}
{% endif %}
{% endfor %}
{% for passive_interface in device['config_context']["ospf"]['passive_interfaces'] %}
   passive-interface {{ passive_interface}}
{% endfor %}
   max-lsa {{ device['config_context']["ospf"]['max_lsa'] }}
!
{% if device['config_context']['ospfv3'] is defined %}
router ospfv3 {{ device['config_context']["ospf"]['process_id'] }}
{% for interface in device["interfaces"] %}
{% if 'Loop' in interface["name"] %}
{% for addr in interface.ip_addresses %}
{% if addr.address is defined and '.' in addr.address %}
{% set rid = addr.address | ipaddr('address') %}
   router-id {{ rid }}
{% endif %}
{% endfor %}
{% endif %}
{% endfor %}
   !
{% for address_family in device['config_context']['ospfv3']['address_families'] %}
   address-family {{ address_family}}
{% endfor %}
{% endif %}
!
{%endraw%}
```

ios/services.j2
```jinja
{%raw%}
line con 0
 logging synchronous
line aux 0
line vty 0 4
 privilege level 15
 login local
 transport preferred ssh
 transport input all
 transport output telnet ssh
!
! 

{%endraw%}
```
## Building the router Configuration results
After all of these files have been created we can now run the playbook and create the full configuration

```bash
$ ansible-playbook pb.build_router_configs.yml --ask-vault-pass
Vault password: 

PLAY [Build Router Configurations] *******************************************************************************************************************************************************************************************************************

TASK [generate_configs : Get data from Nautobot] *****************************************************************************************************************************************************************************************************
ok: [bbr01 -> localhost]

TASK [generate_configs : Ensure router_configs directory exists] *************************************************************************************************************************************************************************************
ok: [bbr01 -> localhost]

TASK [generate_configs : Build Cisco Configurations] *************************************************************************************************************************************************************************************************
[DEPRECATION WARNING]: Use 'ansible.utils.ipaddr' module instead. This feature will be removed from ansible.netcommon in a release after 2024-01-01. Deprecation warnings can be disabled by setting deprecation_warnings=False in ansible.cfg.
changed: [bbr01 -> localhost]

PLAY RECAP *******************************************************************************************************************************************************************************************************************************************
bbr01                      : ok=3    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

And the final product in the router_configs folder

```bash
version 15.4
service timestamps debug datetime msec
service timestamps log datetime msec
no service password-encryption
!
!
hostname bbr01
!
boot-start-marker
boot-end-marker
!
aqm-register-fnf
!
ip domain-name example.com
!
!

no aaa new-model
!
mmi polling-interval 60
no mmi auto-configure
no mmi pvc
mmi snmp-timeout 180
!
vrf definition MGMT
 !
 address-family ipv4
 exit-address-family
!
!
!

username cisco privilege 15 password 0 cisco
!
redundancy
!
!
ip ssh source-interface Ethernet0/3
ip ssh version 2
ip scp server enable
! 
!
!
!
!
!         
!
!
!
!
ipv6 unicast-routing
!
!
!
!
interface Ethernet0/0
   no shutdown
   ip address 172.16.100.0 255.255.255.254
   ip ospf 1 area 0
   ip ospf cost 100
   ip ospf network point-to-point
   ipv6 address 2601:100:c800:100::/127
   ospfv3 1 ipv6 area 0
   ospfv3 cost 100
   ospfv3 network point-to-point
interface Ethernet0/1
   no shutdown
   ip address 172.16.100.2 255.255.255.254
   ip ospf 1 area 0
   ip ospf cost 100
   ip ospf network point-to-point
   ipv6 address 2601:100:c800:100::2/127
   ospfv3 1 ipv6 area 0
   ospfv3 cost 100
   ospfv3 network point-to-point
interface Ethernet0/2
   no shutdown
   ip address 172.16.100.4 255.255.255.254
   ip ospf 1 area 0
   ip ospf cost 100
   ip ospf network point-to-point
   ipv6 address 2601:100:c800:100::4/127
   ospfv3 1 ipv6 area 0
   ospfv3 cost 100
   ospfv3 network point-to-point
interface Ethernet0/3
   vrf forwarding MGMT
   no shutdown
   ip address 192.168.18.101 255.255.255.0
interface Loopback0
   ip address 172.16.100.128 255.255.255.255
   ip ospf 1 area 0
   ipv6 address 2601:100:c800:100::128/128
   ospfv3 1 ipv6 area 0

!
ip forward-protocol nd
!
!
no ip http server
no ip http secure-server
!         
!
!
!
control-plane
!
!
!
!
!
!
!
!
!
!

!

!
router bgp 100
   bgp router-id 172.16.100.128
   neighbor backbone-ipv4 peer-group
   neighbor backbone-ipv4 remote-as 100
   neighbor backbone-ipv4 update-source Loopback0
   neighbor backbone-ipv4 next-hop-self
   neighbor backbone-ipv6 peer-group
   neighbor backbone-ipv6 remote-as 100
   neighbor backbone-ipv6 update-source Loopback0
   neighbor 172.16.100.129 peer-group backbone-ipv4
   neighbor 172.16.100.130 peer-group backbone-ipv4
   neighbor 172.16.100.131 peer-group backbone-ipv4
   neighbor 172.16.100.132 peer-group backbone-ipv4
   neighbor 172.16.100.133 peer-group backbone-ipv4
   neighbor 2601:100:c800:100::129 peer-group backbone-ipv6
   neighbor 2601:100:c800:100::130 peer-group backbone-ipv6
   neighbor 2601:100:c800:100::131 peer-group backbone-ipv6
   neighbor 2601:100:c800:100::132 peer-group backbone-ipv6
   neighbor 2601:100:c800:100::133 peer-group backbone-ipv6
   address-family ipv4 unicast
   neighbor 172.16.100.129 activate
   neighbor 172.16.100.130 activate
   neighbor 172.16.100.131 activate
   neighbor 172.16.100.132 activate
   neighbor 172.16.100.133 activate
   no neighbor 2601:100:c800:100::129 activate
   no neighbor 2601:100:c800:100::130 activate
   no neighbor 2601:100:c800:100::131 activate
   no neighbor 2601:100:c800:100::132 activate
   no neighbor 2601:100:c800:100::133 activate
   address-family ipv6 unicast
   neighbor backbone-ipv6 next-hop-self
   neighbor 2601:100:c800:100::129 activate
   neighbor 2601:100:c800:100::130 activate
   neighbor 2601:100:c800:100::131 activate
   neighbor 2601:100:c800:100::132 activate
   neighbor 2601:100:c800:100::133 activate
!
router ospf 1
   router-id 172.16.100.128
   passive-interface Loopback0
   max-lsa 12000
!
router ospfv3 1
   router-id 172.16.100.128
   !
   address-family ipv6
!
!
line con 0
 logging synchronous
line aux 0
line vty 0 4
 privilege level 15
 login local
 transport preferred ssh
 transport input all
 transport output telnet ssh
!
! 
!
end
```
## Putting it all together
Now lets update our original playbook to add a new role that will push the configuration to the bbr01 router. Create a folder under the roles folder called push_configs.

```yaml
---
- name: Build Router Configurations
  hosts: bbr01
  gather_facts: false
  connection: network_cli
  vars_files:
    - vault.yml

  roles:
    - role: generate_configs
    - role: push_configs
```

in the roles/push_configs/tasks/main.yml we just need a single task. ios_config allows for you to push a full configuration to the router, and it should only replace only the configuration line that has changed. For this to work your full configuration has to look exactly like the show run command output, otherwise even if nothing is actually changed, I believe you will see a yellow changed on the ansible output.

```yaml
- name: Push configs to Cisco Routers and Switches
  cisco.ios.ios_config:
    src: ./router_configs/{{inventory_hostname}}.cfg
    replace: line
    save_when: modified
```

Now lets re-run the playbook
```bash
$ ansible-playbook pb.build_router_configs.yml --ask-vault-pass
Vault password: 

PLAY [Build Router Configurations] **************************************************************************************************************************************************************************************************

TASK [generate_configs : Get data from Nautobot] ************************************************************************************************************************************************************************************
ok: [bbr01 -> localhost]

TASK [generate_configs : Ensure router_configs directory exists] ********************************************************************************************************************************************************************
ok: [bbr01 -> localhost]

TASK [generate_configs : Build Cisco Configurations] ********************************************************************************************************************************************************************************
[DEPRECATION WARNING]: Use 'ansible.utils.ipaddr' module instead. This feature will be removed from ansible.netcommon in a release after 2024-01-01. Deprecation warnings can be disabled by setting deprecation_warnings=False in 
ansible.cfg.
changed: [bbr01 -> localhost]

TASK [push_configs : Push configs to Cisco Routers and Switches] ********************************************************************************************************************************************************************
[WARNING]: To ensure idempotency and correct diff the input configuration lines should be similar to how they appear if present in the running configuration on device including the indentation
changed: [bbr01]

PLAY RECAP **************************************************************************************************************************************************************************************************************************
bbr01                      : ok=4    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```
Ok that worked, excellent, and here is output from the router after the configuration was pushed.

```bash
bbr01#sh run
Building configuration...

Current configuration : 3898 bytes
!
! Last configuration change at 03:36:41 UTC Sun Apr 28 2024 by bbaker4
!
version 15.4
service timestamps debug datetime msec
service timestamps log datetime msec
no service password-encryption
!
hostname bbr01
!
boot-start-marker
boot-end-marker
!
aqm-register-fnf
!
vrf definition MGMT
 !
 address-family ipv4
 exit-address-family
!
!
no aaa new-model
mmi polling-interval 60
no mmi auto-configure
no mmi pvc
mmi snmp-timeout 180
!
!
!
!
!
!
!
!


!
!
!
!
no ip domain lookup
ip domain name example.com
ip cef
ipv6 unicast-routing
ipv6 cef  
!
multilink bundle-name authenticated
!
!
!
!
!
!
!
!
username cisco privilege 15 password 0 cisco
!
redundancy
!
!
ip ssh source-interface Ethernet0/3
ip ssh version 2
ip scp server enable
! 
!
!
!
!         
!
!
!
!
!
!
!
!
interface Loopback0
 ip address 172.16.100.128 255.255.255.255
 ip ospf 1 area 0
 ipv6 address 2601:100:C800:100::128/128
 ospfv3 network point-to-point
 ospfv3 1 ipv6 area 0
!
interface Ethernet0/0
 ip address 172.16.100.0 255.255.255.254
 ip ospf network point-to-point
 ip ospf 1 area 0
 ip ospf cost 100
 ipv6 address 2601:100:C800:100::/127
 ospfv3 network point-to-point
 ospfv3 cost 100
 ospfv3 1 ipv6 area 0
!
interface Ethernet0/1
 ip address 172.16.100.2 255.255.255.254
 ip ospf network point-to-point
 ip ospf 1 area 0
 ip ospf cost 100
 ipv6 address 2601:100:C800:100::2/127
 ospfv3 network point-to-point
 ospfv3 cost 100
 ospfv3 1 ipv6 area 0
!
interface Ethernet0/2
 ip address 172.16.100.4 255.255.255.254
 ip ospf network point-to-point
 ip ospf 1 area 0
 ip ospf cost 100
 ipv6 address 2601:100:C800:100::4/127
 ospfv3 network point-to-point
 ospfv3 cost 100
 ospfv3 1 ipv6 area 0
!
interface Ethernet0/3
 description MGMT-INTERFAC
 vrf forwarding MGMT
 ip address 192.168.18.101 255.255.255.0
!
router ospfv3 1
 router-id 172.16.100.128
 !
 address-family ipv6 unicast
 exit-address-family
!
router ospf 1
 router-id 172.16.100.128
 max-lsa 12000
 passive-interface Loopback0
!
router bgp 100
 bgp router-id 172.16.100.128
 bgp log-neighbor-changes
 neighbor backbone-ipv4 peer-group
 neighbor backbone-ipv4 remote-as 100
 neighbor backbone-ipv4 update-source Loopback0
 neighbor backbone-ipv6 peer-group
 neighbor backbone-ipv6 remote-as 100
 neighbor backbone-ipv6 update-source Loopback0
 neighbor 2601:100:C800:100::129 peer-group backbone-ipv6
 neighbor 2601:100:C800:100::130 peer-group backbone-ipv6
 neighbor 2601:100:C800:100::131 peer-group backbone-ipv6
 neighbor 2601:100:C800:100::132 peer-group backbone-ipv6
 neighbor 2601:100:C800:100::133 peer-group backbone-ipv6
 neighbor 172.16.100.129 peer-group backbone-ipv4
 neighbor 172.16.100.130 peer-group backbone-ipv4
 neighbor 172.16.100.131 peer-group backbone-ipv4
 neighbor 172.16.100.132 peer-group backbone-ipv4
 neighbor 172.16.100.133 peer-group backbone-ipv4
 !
 address-family ipv4
  neighbor backbone-ipv4 next-hop-self
  no neighbor 2601:100:C800:100::129 activate
  no neighbor 2601:100:C800:100::130 activate
  no neighbor 2601:100:C800:100::131 activate
  no neighbor 2601:100:C800:100::132 activate
  no neighbor 2601:100:C800:100::133 activate
  neighbor 172.16.100.129 activate
  neighbor 172.16.100.130 activate
  neighbor 172.16.100.131 activate
  neighbor 172.16.100.132 activate
  neighbor 172.16.100.133 activate
 exit-address-family
 !
 address-family ipv6
  neighbor backbone-ipv6 next-hop-self
  neighbor 2601:100:C800:100::129 activate
  neighbor 2601:100:C800:100::130 activate
  neighbor 2601:100:C800:100::131 activate
  neighbor 2601:100:C800:100::132 activate
  neighbor 2601:100:C800:100::133 activate
 exit-address-family
!
ip forward-protocol nd
!
!
no ip http server
no ip http secure-server
!
!
!
!
control-plane
!         
!
!
!
!
!
!
!
line con 0
 logging synchronous
line aux 0
line vty 0 4
 privilege level 15
 login local
 transport preferred ssh
 transport input all
 transport output telnet ssh
!
!
end

bbr01# 
bbr01#
bbr01#
bbr01#sh ip bgp sum
BGP router identifier 172.16.100.128, local AS number 100
BGP table version is 112, main routing table version 112
11 network entries using 1540 bytes of memory
19 path entries using 1520 bytes of memory
3/3 BGP path/bestpath attribute entries using 432 bytes of memory
3 BGP AS-PATH entries using 72 bytes of memory
0 BGP route-map cache entries using 0 bytes of memory
0 BGP filter-list cache entries using 0 bytes of memory
BGP using 3564 total bytes of memory
BGP activity 45/34 prefixes, 84/65 paths, scan interval 60 secs

Neighbor        V           AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
172.16.100.129  4          100   14191   14209      112    0    0 1w1d            0
172.16.100.130  4          100   13398   13388      112    0    0 1w1d            7
172.16.100.131  4          100   13403   13373      112    0    0 1w1d            7
172.16.100.132  4          100   13372   13373      112    0    0 1w1d            2
172.16.100.133  4          100   13386   13382      112    0    0 1w1d            3
bbr01#sh  bgp ipv6 uni sum
bbr01#sh  bgp ipv6 uni summary 
BGP router identifier 172.16.100.128, local AS number 100
BGP table version is 1, main routing table version 1

Neighbor        V           AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
2601:100:C800:100::129
                4          100       2       2        1    0    0 00:00:38        0
2601:100:C800:100::130
                4          100       2       2        1    0    0 00:00:38        0
2601:100:C800:100::131
                4          100       2       2        1    0    0 00:00:38        0
2601:100:C800:100::132
                4          100       2       2        1    0    0 00:00:38        0
2601:100:C800:100::133
                4          100       2       2        1    0    0 00:00:37        0
bbr01#sh ip os
bbr01#sh ip ospf n
bbr01#sh ip ospf ne
bbr01#sh ip ospf neighbor 

Neighbor ID     Pri   State           Dead Time   Address         Interface
172.16.100.132    0   FULL/  -        00:00:35    172.16.100.5    Ethernet0/2
172.16.100.129    0   FULL/  -        00:00:39    172.16.100.3    Ethernet0/1
172.16.100.130    0   FULL/  -        00:00:35    172.16.100.1    Ethernet0/0
bbr01#sh os
bbr01#sh ospfv3 nei
bbr01#sh ospfv3 neighbor 

          OSPFv3 1 address-family ipv6 (router-id 172.16.100.128)

Neighbor ID     Pri   State           Dead Time   Interface ID    Interface
172.16.100.132    0   FULL/  -        00:00:33    3               Ethernet0/2
172.16.100.129    0   FULL/  -        00:00:38    4               Ethernet0/1
172.16.100.130    0   FULL/  -        00:00:38    3               Ethernet0/0
bbr01#sh ip route
Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area 
       N1 - OSPF NSSA external type 1, N2 - OSPF NSSA external type 2
       E1 - OSPF external type 1, E2 - OSPF external type 2
       i - IS-IS, su - IS-IS summary, L1 - IS-IS level-1, L2 - IS-IS level-2
       ia - IS-IS inter area, * - candidate default, U - per-user static route
       o - ODR, P - periodic downloaded static route, H - NHRP, l - LISP
       a - application route
       + - replicated route, % - next hop override

Gateway of last resort is 172.16.100.132 to network 0.0.0.0

B*    0.0.0.0/0 [200/0] via 172.16.100.132, 1w1d
      172.16.0.0/16 is variably subnetted, 38 subnets, 3 masks
O IA     172.16.30.0/31 [110/300] via 172.16.100.1, 1w1d, Ethernet0/0
O IA     172.16.30.2/31 [110/300] via 172.16.100.1, 1w1d, Ethernet0/0
O IA     172.16.30.4/31 [110/400] via 172.16.100.1, 1w1d, Ethernet0/0
O IA     172.16.30.6/31 [110/300] via 172.16.100.1, 1w1d, Ethernet0/0
O IA     172.16.30.8/31 [110/400] via 172.16.100.1, 1w1d, Ethernet0/0
O IA     172.16.30.128/32 [110/201] via 172.16.100.1, 1w1d, Ethernet0/0
O IA     172.16.30.129/32 [110/301] via 172.16.100.1, 1w1d, Ethernet0/0
O IA     172.16.30.130/32 [110/301] via 172.16.100.1, 1w1d, Ethernet0/0
O IA     172.16.30.131/32 [110/301] via 172.16.100.1, 1w1d, Ethernet0/0
C        172.16.100.0/31 is directly connected, Ethernet0/0
L        172.16.100.0/32 is directly connected, Ethernet0/0
C        172.16.100.2/31 is directly connected, Ethernet0/1
L        172.16.100.2/32 is directly connected, Ethernet0/1
C        172.16.100.4/31 is directly connected, Ethernet0/2
L        172.16.100.4/32 is directly connected, Ethernet0/2
O        172.16.100.6/31 [110/200] via 172.16.100.3, 1w1d, Ethernet0/1
O        172.16.100.8/31 [110/200] via 172.16.100.3, 1w1d, Ethernet0/1
O        172.16.100.10/31 [110/200] via 172.16.100.1, 1w1d, Ethernet0/0
O IA     172.16.100.12/31 [110/200] via 172.16.100.1, 1w1d, Ethernet0/0
O IA     172.16.100.14/31 [110/300] via 172.16.100.1, 1w1d, Ethernet0/0
O        172.16.100.16/31 [110/200] via 172.16.100.5, 1w1d, Ethernet0/2
O        172.16.100.18/31 [110/300] via 172.16.100.3, 1w1d, Ethernet0/1
C        172.16.100.128/32 is directly connected, Loopback0
O        172.16.100.129/32 [110/101] via 172.16.100.3, 1w1d, Ethernet0/1
O        172.16.100.130/32 [110/101] via 172.16.100.1, 1w1d, Ethernet0/0
O        172.16.100.131/32 [110/201] via 172.16.100.1, 1w1d, Ethernet0/0
O        172.16.100.132/32 [110/101] via 172.16.100.5, 1w1d, Ethernet0/2
O        172.16.100.133/32 [110/201] via 172.16.100.3, 1w1d, Ethernet0/1
B        172.16.220.0/24 [200/0] via 172.16.100.132, 1w1d
B        172.16.221.0/24 [200/0] via 172.16.100.133, 2d07h
B        172.16.222.0/24 [200/0] via 172.16.100.130, 2d07h
B        172.16.223.0/24 [200/0] via 172.16.100.130, 2d07h
B        172.16.224.0/24 [200/0] via 172.16.100.133, 2d07h
B        172.16.225.0/24 [200/0] via 172.16.100.130, 2d07h
B        172.16.226.0/24 [200/0] via 172.16.100.130, 2d07h
B        172.16.227.0/24 [200/0] via 172.16.100.130, 2d07h
B        172.16.229.0/24 [200/0] via 172.16.100.130, 2d07h
B        172.16.230.0/24 [200/0] via 172.16.100.130, 2d00h
bbr01# 
```

Utilizing Nautobot as an inventory in Ansible and subsequently generating router configurations based on the data as a Source of Truth is a sophisticated approach to managing and deploying network infrastructure. By leveraging this methodology, one can ensure consistency and accuracy in the configuration process. 

In the upcoming post, we will explore the process of setting up Proxmox virtual machines using the same Nautobot Dynamic inventory, taking advantage of Ansible's automation capabilities. This will enable users to create and manage virtual machines in a more efficient and streamlined manner.