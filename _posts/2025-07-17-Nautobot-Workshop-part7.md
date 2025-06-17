---
title: Nautobot Workshop Blog Series - Part 7 - Nautobot Ansible Dynamic Inventory
date: 2025-07-17 9:00:00 -6
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


## Part 7 - Nautobot Ansible Dynamic Inventory
In this section we will redirect our focus back over to Ansible and using Nautobot as our source of truth to generate and deploy router configurations.

### Setting up the Dynamic inventory
Under the inventory folder create a new file name ```inventory.yml```. This will hold our dynamic inventory configurations. You will also want to store your API token as an environmental variable. I am also going to use ansible-vault to store my secrets, which includes the api token and router login.

> You will need to install netutils, ansible-pylibssh and paramiko via pip in your virtual env before using the dynamic inventory.
{: .prompt-tip }

We will create a query to pull all of the variables we need to build the configuration. We will want the UUID and the network driver for sure, other variables I will leave up to you, but you can pull the interfaces among a host of other device data if you wish. The network driver will be used with Ansible to correctly set the connection type, and the device UUID we will use in a graphql query as another task before templating the configurations to a file.

[inventory.yml](https://github.com/byrn-baker/Nautobot-Workshop/blob/main/ansible-lab/inventory/inventory.yml)

### Creating configuration templating role
If we go back to our ansible-lab folder where we created the playbooks to load nautobot and build the lab topology, create a new folder under the roles called ```build_lab_config/``` We will be creating the below tree

```bash
(.ansible) ubuntu@containerlabs:~/Nautobot-Workshop/ansible-lab$ tree
└── roles
    ├── build_lab_config
    │   ├── tasks
    │   │   └── main.yml
    │   ├── templates
    │   │   ├── cisco_ios.j2
    │   │   └── ios
    │   │       ├── interfaces
    │   │       │   ├── _loopback.j2
    │   │       │   ├── _router_physical.j2
    │   │       │   ├── _switch_l2_physical.j2
    │   │       │   ├── _switch_l3_physical.j2
    │   │       │   └── _switch_l3_virtial.j2
    │   │       ├── interfaces.j2
    │   │       └── platform_templates
    │   │           └── provider_router.j2
    │   └── vars
    │       └── main.yml
```

Create a new playbook referencing this new role above:

[pb.build-and-deploy.yml](https://github.com/byrn-baker/Nautobot-Workshop/blob/main/ansible-lab/pb.build-and-deploy.yml)

In the [tasks/main.yml](https://github.com/byrn-baker/Nautobot-Workshop/blob/main/ansible-lab/roles/build_lab_config/tasks/main.yml) under the ```roles/build_lab_config/tasks/``` folder start by adding a task to query nautobot for all of the information we will need to generate a configuration. We will use Jinja templates to create each configuration in a very similar way as we used in the Nautobot Golden configuration app. There is an option in the query_graphql module that will set all of the data from the query in the devices hostvars. This way you can easily access the data with ```device.hostname```. You will also notice we are using delegate_to so that these tasks are run locally on our Ansible host and not the routers.


Make sure the graphql query string is placed in the [vars/main.yml](https://github.com/byrn-baker/Nautobot-Workshop/blob/main/ansible-lab/roles/build_lab_config/vars/main.yml) file, the query above will reference this.


Next you need to get the templates built out following this tree.

```bash
├── templates
    │   │   ├── cisco_ios.j2
    │   │   └── ios
    │   │       ├── interfaces
    │   │       │   ├── _loopback.j2
    │   │       │   ├── _router_physical.j2
    │   │       │   ├── _switch_l2_physical.j2
    │   │       │   ├── _switch_l3_physical.j2
    │   │       │   └── _switch_l3_virtial.j2
    │   │       ├── interfaces.j2
    │   │       └── platform_templates
    │   │           └── provider_router.j2
```

We can use the templates from the previous Config intent section with some small modifications. Because the variables will be store in hostvars we will need to place "device" in front to correctly access the key values.

In the [/templates/cisco_ios.j2](https://github.com/byrn-baker/Nautobot-Workshop/blob/main/ansible-lab/roles/build_lab_config/templates/cisco_ios.j2) its similar to the template in the intended section except device is placed in front of the role.name so that it can properly access that key value. You will need to ensure you are always access the key values under device in the rest of your templates.

### Deploy the configurations - Cisco
Now that we have a skeleton of our configurations creates, (interface descriptions and IPs) lets create another role to push these configurations to the router. We will start with the cisco platform, but the Arista will be very similar.

For this task we will use the cisco.ios.ios_config module to push the entire configuration to the cisco router.

[/roles/deploy_lab_configs/tasks/main.yml](https://github.com/byrn-baker/Nautobot-Workshop/blob/main/ansible-lab/roles/deploy_lab_configs/tasks/main.yml)

In our lab right P1 should have a configuration that looks something like this if we just focus on the interfaces

```bash
P1#
P1#
P1#sh run
Building configuration...

Current configuration : 1494 bytes
!
version 17.12
service timestamps debug datetime msec
service timestamps log datetime msec
!
hostname P1
!
boot-start-marker
boot-end-marker
!
!
vrf definition clab-mgmt
 description clab-mgmt
 !
 address-family ipv4
 exit-address-family
 !
 address-family ipv6
 exit-address-family
!
no aaa new-model
!
interface Ethernet0/0
 description clab-mgmt
 vrf forwarding clab-mgmt
 ip address 192.168.220.2 255.255.255.0
!
interface Ethernet0/1
 no ip address
 shutdown
!
interface Ethernet0/2
 no ip address
 shutdown
!
interface Ethernet0/3
 no ip address
 shutdown
!
interface Ethernet1/0
 no ip address
 shutdown
!
interface Ethernet1/1
 no ip address
 shutdown
!
interface Ethernet1/2
 no ip address
 shutdown
!
interface Ethernet1/3
 no ip address
 shutdown
!
ip forward-protocol nd
!
!
ip http server
ip http secure-server
ip route vrf clab-mgmt 0.0.0.0 0.0.0.0 Ethernet0/0 192.168.220.1
ip ssh bulk-mode 131072
!
ipv6 route vrf clab-mgmt ::/0 Ethernet0/0
!
!
!
!
control-plane
!
!
!
line con 0
 logging synchronous
line aux 0
line vty 0 4
 login local
 transport input ssh
!
!
!
!
end

P1# 
```

After we push the configs it should now look like this

```bash
P1#
P1#
P1#
P1#sh run
Building configuration...

Current configuration : 2065 bytes
!
! Last configuration change at 03:03:55 UTC Thu May 22 2025 by admin
!
version 17.12
service timestamps debug datetime msec
service timestamps log datetime msec
!
hostname P1
!
boot-start-marker
boot-end-marker
!
!
vrf definition clab-mgmt
 description clab-mgmt
 !
 address-family ipv4
 exit-address-family
 !
 address-family ipv6
 exit-address-family
!
no aaa new-model
!
!
interface Loopback0
 description Protocol Loopback
 ip address 100.0.254.1 255.255.255.255
 ipv6 address 2001:DB8:100:254::1/128
!
interface Ethernet0/0
 description MGMT ONLY INTERFACE
 vrf forwarding clab-mgmt
 ip address 192.168.220.2 255.255.255.0
 no cdp enable
!
interface Ethernet0/1
 description To P2-Ethernet0/1
 ip address 100.0.12.1 255.255.255.0
 ipv6 address 2001:DB8:100:12::1/64
!
interface Ethernet0/2
 description To P3-Ethernet0/2
 ip address 100.0.13.1 255.255.255.0
 ipv6 address 2001:DB8:100:13::1/64
!
interface Ethernet0/3
 description NOT IN USE
 no ip address
 shutdown
!
interface Ethernet1/0
 description To RR1-Ethernet0/1
 ip address 100.0.101.1 255.255.255.0
 ipv6 address 2001:DB8:100:101::1/64
!
interface Ethernet1/1
 description To PE1-Ethernet0/1
 ip address 100.0.11.1 255.255.255.0
 ipv6 address 2001:DB8:100:11::1/64
!
interface Ethernet1/2
 no ip address
 shutdown
!
interface Ethernet1/3
 no ip address
 shutdown
!
ip forward-protocol nd
!
!
ip http server
ip http secure-server
ip route vrf clab-mgmt 0.0.0.0 0.0.0.0 Ethernet0/0 192.168.220.1
ip ssh bulk-mode 131072
!
ipv6 route vrf clab-mgmt ::/0 Ethernet0/0
!
!
!
!
control-plane
!
!
!
line con 0
 logging synchronous
line aux 0
line vty 0 4
 login local
 transport input ssh
!
!
!
!         
end

P1#
P1#ping 100.0.12.2  
Type escape sequence to abort.
Sending 5, 100-byte ICMP Echos to 100.0.12.2, timeout is 2 seconds:
.!!!!
Success rate is 80 percent (4/5), round-trip min/avg/max = 1/1/2 ms
```

## Conclusion
In this part of the Nautobot Workshop series, we’ve successfully bridged the gap between Nautobot as a Source of Truth and Ansible as our automation engine. By building a dynamic inventory from Nautobot’s GraphQL API, templating device configurations with Jinja2, and deploying them directly to routers using Ansible modules, we've brought full-circle automation into our lab workflow.

This setup not only reflects real-world practices for managing network infrastructure as code, but also lays a strong foundation for scaling and enforcing consistency across a multi-vendor environment. Whether you're simulating a service provider core, validating designs, or testing automation playbooks, this kind of workflow empowers you to iterate faster and with confidence.