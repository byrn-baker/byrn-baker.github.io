---
title: Nautobot Workshop Blog Series - Part 3 Adding Devices to Nautobot via Ansible
date: 2025-05-12 9:00:00 -500
categories: [Nautobot,Ansible,Automtation]
tags: [NetworkAutomation,NetworkSourceOfTruth,nautobot,AutomationPlatform,NautobotTutorials]
image:
  path: /assets/img/nautobot_workshop/light_title_image-50.webp
---

# Nautobot Workshop Blog Series
"Nautobot Workshop" is a blog series that guides you through building a fully automated network lab using Nautobot, Containerlab, and Docker. Starting from environment setup on Ubuntu, each post will walk through deploying Nautobot with nautobot-docker-compose, modeling network topologies with Containerlab and vrnetlab-based routers, and populating Nautobot with real device data using Ansible. You'll also learn how to use Nautobot’s GraphQL API for dynamic inventory, generate device configurations with Jinja2 templates, and enforce configuration compliance using the Golden Config plugin. This series is ideal for network engineers looking to integrate source of truth, automation, and lab simulation into a streamlined workflow.

## Part 3: Adding Devices to Nautobot via Ansible
Today we will accomplish the following:
1. Create a python virtual environment to manage our Ansible playbooks. 
2. Create a file that contains all of the necessary elements for our Nautobot Source of Truth (NSoT).
3. Create a playbook and tasks that will populate our NSoT.

### Creating python environment
In your Nautobot-Workshop folder begin by create a new folder ```ansible-lab```.
```bash
ubuntu@containerlabs:~$ cd Nautobot-Workshop
ubuntu@containerlabs:~/Nautobot-Workshop/$ mkdir ansible-lab
ubuntu@containerlabs:~/Nautobot-Workshop/ansible-lab$ sudo apt update
ubuntu@containerlabs:~/Nautobot-Workshop/ansible-lab$ sudo apt install -y python3-venv
ubuntu@containerlabs:~/Nautobot-Workshop/ansible-lab$ source .ansible/bin/activate
(.ansible) ubuntu@containerlabs:~/Nautobot-Workshop/ansible-lab$ 
```

Once you are in your new virtual environment install both Ansible and Pynautobot using PIP, create an ansible.cfg file
```bash
(.ansible) ubuntu@containerlabs:~/Nautobot-Workshop/ansible-lab$ pip3 install ansible pynautobot
(.ansible) ubuntu@containerlabs:~/Nautobot-Workshop/ansible-lab$ touch ansible.cfg
```

In the ```ansible.cfg``` populate it with the following:
```bash
[defaults]
inventory = inventory/inventory.yml
# hash_behaviour = merge
host_key_checking = False
host_key_auto_add = True
retry_files_enabled = False # for the sake of everything good, stop creating these uesless files
forks = 15
callbacks_enabled = timer, profile_tasks, profile_roles
gathering = smart
fact_caching_connection = /tmp
stdout_callback = yaml
library = ./files/ansible/library
ansible_debug = True
timeout = 60
interpreter_python = ./.venv/bin/python3
nocows = 1

COLLECTIONS_PATHS = ./ansible_collections

[persistent_connection]
command_timeout = 45
```

then install the nautobot-ansible module using galaxy
```bash
(.ansible) ubuntu@containerlabs:~/Nautobot-Workshop/ansible-lab$ ansible-galaxy collection install networktocode.nautobot
(.ansible) ubuntu@containerlabs:~/Nautobot-Workshop/ansible-lab$ tree
.
├── ansible.cfg
├── ansible_collections
│   ├── networktocode
│   │   └── nautobot
│   │       ├── ansible.cfg
│   │       ├── build
│   │       ├── CHANGELOG.md
│   │       ├── changelogs
│   │       │   ├── changelog.yaml
│   │       │   ├── config.yaml
│   │       │   └── fragments
│   │       ├── changes
│   │       │   └── towncrier_template.j2
│   │       ├── CODE_OF_CONDUCT
│   │       ├── docker-compose.yml
│   │       ├── Dockerfile
│   │       ├── docs
│   │       │   ├── assets
│   │       │   │   ├── extra.css
│   │       │   │   ├── favicon.ico
│   │       │   │   ├── nautobot_logo.png
│   │       │   │   ├── nautobot_logo.svg
│   │       │   │   ├── networktocode_bw.png
│   │       │   │   └── overrides
│   │       │   │       └── partials
│   │       │   │           └── copyright.html
│   │       │   ├── getting_started
│   │       │   │   ├── contributing
│   │       │   │   │   ├── changelog_fragments.md
│   │       │   │   │   ├── debugging.md
│   │       │   │   │   ├── modules
│   │       │   │   │   │   ├── architecture.md
│   │       │   │   │   │   ├── media
│   │       │   │   │   │   │   ├── post_rt.png
│   │       │   │   │   │   │   └── vrf_options.png
│   │       │   │   │   │   ├── new_module.md
│   │       │   │   │   │   └── update_module.md
│   │       │   │   │   ├── release.md
│   │       │   │   │   ├── testing_locally.md
│   │       │   │   │   └── testing_with_gha.md
│   │       │   │   ├── how-to-use
│   │       │   │   │   ├── advanced.md
│   │       │   │   │   ├── inventory.md
│   │       │   │   │   ├── media
│   │       │   │   │   │   ├── advanced_dict.png
│   │       │   │   │   │   ├── advanced_dns_name.png
│   │       │   │   │   │   └── api_device_post.png
│   │       │   │   │   └── modules.md
│   │       │   │   ├── index.md
│   │       │   │   └── installation.md
│   │       │   ├── images
│   │       │   │   └── icon-nautobot-dev-example.png
│   │       │   ├── index.md
│   │       │   ├── release_notes.md
│   │       │   ├── requirements.txt
│   │       │   └── requirements.yaml
│   │       ├── extensions
│   │       │   └── eda
│   │       │       ├── plugins
│   │       │       │   └── event_source
│   │       │       │       ├── __init__.py
│   │       │       │       ├── nautobot_changelog.py
│   │       │       │       └── README.md
│   │       │       └── rulebooks
│   │       │           └── demo_nautobot_rulebook.yml
│   │       ├── FILES.json
│   │       ├── invoke.yml.example
│   │       ├── LICENSE
│   │       ├── MANIFEST.json
│   │       ├── meta
│   │       │   ├── extensions.yml
│   │       │   └── runtime.yml
│   │       ├── nautobot-ansible.code-workspace.example
│   │       ├── NOTICE
│   │       ├── plugins
│   │       │   ├── action
│   │       │   │   ├── __init__.py
│   │       │   │   └── query_graphql.py
│   │       │   ├── doc_fragments
│   │       │   │   └── fragments.py
│   │       │   ├── filter
│   │       │   │   └── graphql.py
│   │       │   ├── inventory
│   │       │   │   ├── gql_inventory.py
│   │       │   │   └── inventory.py
│   │       │   ├── lookup
│   │       │   │   ├── __init__.py
│   │       │   │   ├── lookup_graphql.py
│   │       │   │   └── lookup.py
│   │       │   ├── modules
│   │       │   │   ├── admin_group.py
│   │       │   │   ├── admin_permission.py
│   │       │   │   ├── admin_user.py
│   │       │   │   ├── cable.py
│   │       │   │   ├── circuit.py
│   │       │   │   ├── circuit_termination.py
│   │       │   │   ├── circuit_type.py
│   │       │   │   ├── cloud_account.py
│   │       │   │   ├── cloud_network_prefix_assignment.py
│   │       │   │   ├── cloud_network.py
│   │       │   │   ├── cloud_resource_type.py
│   │       │   │   ├── cloud_service_network_assignment.py
│   │       │   │   ├── cloud_service.py
│   │       │   │   ├── cluster_group.py
│   │       │   │   ├── cluster.py
│   │       │   │   ├── cluster_type.py
│   │       │   │   ├── console_port.py
│   │       │   │   ├── console_port_template.py
│   │       │   │   ├── console_server_port.py
│   │       │   │   ├── console_server_port_template.py
│   │       │   │   ├── contact.py
│   │       │   │   ├── controller_managed_device_group.py
│   │       │   │   ├── controller.py
│   │       │   │   ├── custom_field_choice.py
│   │       │   │   ├── custom_field.py
│   │       │   │   ├── device_bay.py
│   │       │   │   ├── device_bay_template.py
│   │       │   │   ├── device_interface.py
│   │       │   │   ├── device_interface_template.py
│   │       │   │   ├── device.py
│   │       │   │   ├── device_redundancy_group.py
│   │       │   │   ├── device_type.py
│   │       │   │   ├── dynamic_group.py
│   │       │   │   ├── front_port.py
│   │       │   │   ├── front_port_template.py
│   │       │   │   ├── __init__.py
│   │       │   │   ├── inventory_item.py
│   │       │   │   ├── ip_address.py
│   │       │   │   ├── ip_address_to_interface.py
│   │       │   │   ├── job_button.py
│   │       │   │   ├── location.py
│   │       │   │   ├── location_type.py
│   │       │   │   ├── manufacturer.py
│   │       │   │   ├── metadata_choice.py
│   │       │   │   ├── metadata_type.py
│   │       │   │   ├── module_bay.py
│   │       │   │   ├── module_bay_template.py
│   │       │   │   ├── module.py
│   │       │   │   ├── module_type.py
│   │       │   │   ├── namespace.py
│   │       │   │   ├── nautobot_server.py
│   │       │   │   ├── object_metadata.py
│   │       │   │   ├── platform.py
│   │       │   │   ├── plugin.py
│   │       │   │   ├── power_feed.py
│   │       │   │   ├── power_outlet.py
│   │       │   │   ├── power_outlet_template.py
│   │       │   │   ├── power_panel.py
│   │       │   │   ├── power_port.py
│   │       │   │   ├── power_port_template.py
│   │       │   │   ├── prefix_location.py
│   │       │   │   ├── prefix.py
│   │       │   │   ├── provider.py
│   │       │   │   ├── query_graphql.py
│   │       │   │   ├── rack_group.py
│   │       │   │   ├── rack.py
│   │       │   │   ├── rear_port.py
│   │       │   │   ├── rear_port_template.py
│   │       │   │   ├── relationship_association.py
│   │       │   │   ├── rir.py
│   │       │   │   ├── role.py
│   │       │   │   ├── route_target.py
│   │       │   │   ├── secret.py
│   │       │   │   ├── secrets_group.py
│   │       │   │   ├── secrets_groups_association.py
│   │       │   │   ├── service.py
│   │       │   │   ├── software_version.py
│   │       │   │   ├── static_group_association.py
│   │       │   │   ├── status.py
│   │       │   │   ├── tag.py
│   │       │   │   ├── team.py
│   │       │   │   ├── tenant_group.py
│   │       │   │   ├── tenant.py
│   │       │   │   ├── virtual_chassis.py
│   │       │   │   ├── virtual_machine.py
│   │       │   │   ├── vlan_group.py
│   │       │   │   ├── vlan_location.py
│   │       │   │   ├── vlan.py
│   │       │   │   ├── vm_interface.py
│   │       │   │   └── vrf.py
│   │       │   └── module_utils
│   │       │       ├── circuits.py
│   │       │       ├── cloud.py
│   │       │       ├── dcim.py
│   │       │       ├── extras.py
│   │       │       ├── __init__.py
│   │       │       ├── ipam.py
│   │       │       ├── plugins.py
│   │       │       ├── tenancy.py
│   │       │       ├── users.py
│   │       │       ├── utils.py
│   │       │       └── virtualization.py
│   │       ├── README.md
│   │       └── tests
│   │           ├── config.yml
│   │           ├── integration
│   │           │   ├── entrypoint.sh
│   │           │   ├── integration.cfg
│   │           │   ├── integration_config.tmpl.yml
│   │           │   ├── nautobot-populate.py
│   │           │   ├── render_config.sh
│   │           │   └── targets
│   │           │       ├── inventory
│   │           │       │   ├── aliases
│   │           │       │   ├── compare_inventory_json.py
│   │           │       │   ├── files
│   │           │       │   │   ├── test_2.2-2.3.json
│   │           │       │   │   ├── test_2.2-2.3_options_flatten.json
│   │           │       │   │   ├── test_2.2-2.3_options_flatten.yml
│   │           │       │   │   ├── test_2.2-2.3_plurals.json
│   │           │       │   │   ├── test_2.2-2.3_plurals.yml
│   │           │       │   │   ├── test_2.2-2.3.yml
│   │           │       │   │   ├── test_2-2.2.json
│   │           │       │   │   ├── test_2-2.2_legacy.json
│   │           │       │   │   ├── test_2-2.2_legacy.yml
│   │           │       │   │   ├── test_2-2.2_options_flatten.json
│   │           │       │   │   ├── test_2-2.2_options_flatten.yml
│   │           │       │   │   ├── test_2-2.2_options.json
│   │           │       │   │   ├── test_2-2.2_options.yml
│   │           │       │   │   ├── test_2-2.2_plurals_flatten.json
│   │           │       │   │   ├── test_2-2.2_plurals_flatten.yml
│   │           │       │   │   ├── test_2-2.2_plurals.json
│   │           │       │   │   ├── test_2-2.2_plurals.yml
│   │           │       │   │   ├── test_2-2.2.yml
│   │           │       │   │   ├── test_2.2-3_legacy.json
│   │           │       │   │   ├── test_2.2-3_legacy.yml
│   │           │       │   │   ├── test_2.2-3_options.json
│   │           │       │   │   ├── test_2.2-3_options.yml
│   │           │       │   │   ├── test_2.2-3_plurals_flatten.json
│   │           │       │   │   ├── test_2.2-3_plurals_flatten.yml
│   │           │       │   │   ├── test_2.3-2.4.json
│   │           │       │   │   ├── test_2.3-2.4_options_flatten.json
│   │           │       │   │   ├── test_2.3-2.4_options_flatten.yml
│   │           │       │   │   ├── test_2.3-2.4_plurals.json
│   │           │       │   │   ├── test_2.3-2.4_plurals.yml
│   │           │       │   │   ├── test_2.3-2.4.yml
│   │           │       │   │   ├── test_2-3_gql_groupby.json
│   │           │       │   │   ├── test_2-3_gql_groupby.yml
│   │           │       │   │   ├── test_2-3_gql.json
│   │           │       │   │   ├── test_2-3_gql.yml
│   │           │       │   │   ├── test_2.4-3.json
│   │           │       │   │   ├── test_2.4-3_options_flatten.json
│   │           │       │   │   ├── test_2.4-3_options_flatten.yml
│   │           │       │   │   ├── test_2.4-3_plurals.json
│   │           │       │   │   ├── test_2.4-3_plurals.yml
│   │           │       │   │   └── test_2.4-3.yml
│   │           │       │   ├── README.md
│   │           │       │   ├── runme_config.template
│   │           │       │   └── runme.sh
│   │           │       ├── latest
│   │           │       │   └── tasks
│   │           │       │       ├── admin_group.yml
│   │           │       │       ├── admin_permission.yml
│   │           │       │       ├── admin_user.yml
│   │           │       │       ├── cable.yml
│   │           │       │       ├── circuit_termination.yml
│   │           │       │       ├── circuit_type.yml
│   │           │       │       ├── circuit.yml
│   │           │       │       ├── cloud_account.yml
│   │           │       │       ├── cloud_network_prefix_assignment.yml
│   │           │       │       ├── cloud_network.yml
│   │           │       │       ├── cloud_resource_type.yml
│   │           │       │       ├── cloud_service_network_assignment.yml
│   │           │       │       ├── cloud_service.yml
│   │           │       │       ├── cluster_group.yml
│   │           │       │       ├── cluster_type.yml
│   │           │       │       ├── cluster.yml
│   │           │       │       ├── console_port_template.yml
│   │           │       │       ├── console_port.yml
│   │           │       │       ├── console_server_port_template.yml
│   │           │       │       ├── console_server_port.yml
│   │           │       │       ├── contact.yml
│   │           │       │       ├── controller_managed_device_group.yml
│   │           │       │       ├── controller.yml
│   │           │       │       ├── custom_field_choice.yml
│   │           │       │       ├── custom_field.yml
│   │           │       │       ├── device_bay_template.yml
│   │           │       │       ├── device_bay.yml
│   │           │       │       ├── device_interface_template.yml
│   │           │       │       ├── device_interface.yml
│   │           │       │       ├── device_redundancy_group.yml
│   │           │       │       ├── device_type.yml
│   │           │       │       ├── device.yml
│   │           │       │       ├── dynamic_group.yml
│   │           │       │       ├── front_port_template.yml
│   │           │       │       ├── front_port.yml
│   │           │       │       ├── inventory_item.yml
│   │           │       │       ├── ip_address_to_interface.yml
│   │           │       │       ├── ip_address.yml
│   │           │       │       ├── job_button.yml
│   │           │       │       ├── location_type.yml
│   │           │       │       ├── location.yml
│   │           │       │       ├── lookup.yml
│   │           │       │       ├── main.yml
│   │           │       │       ├── manufacturer.yml
│   │           │       │       ├── metadata_choice.yml
│   │           │       │       ├── metadata_type.yml
│   │           │       │       ├── module_bay_template.yml
│   │           │       │       ├── module_bay.yml
│   │           │       │       ├── module_type.yml
│   │           │       │       ├── module.yml
│   │           │       │       ├── namespace.yml
│   │           │       │       ├── object_metadata.yml
│   │           │       │       ├── platform.yml
│   │           │       │       ├── plugin_bgp_asn.yml
│   │           │       │       ├── power_feed.yml
│   │           │       │       ├── power_outlet_template.yml
│   │           │       │       ├── power_outlet.yml
│   │           │       │       ├── power_panel.yml
│   │           │       │       ├── power_port_template.yml
│   │           │       │       ├── power_port.yml
│   │           │       │       ├── prefix_location.yml
│   │           │       │       ├── prefix.yml
│   │           │       │       ├── provider.yml
│   │           │       │       ├── rack_group.yml
│   │           │       │       ├── rack.yml
│   │           │       │       ├── rear_port_template.yml
│   │           │       │       ├── rear_port.yml
│   │           │       │       ├── relationship_association.yml
│   │           │       │       ├── rir.yml
│   │           │       │       ├── role.yml
│   │           │       │       ├── route_target.yml
│   │           │       │       ├── secrets_groups_association.yml
│   │           │       │       ├── secrets_group.yml
│   │           │       │       ├── secret.yml
│   │           │       │       ├── service.yml
│   │           │       │       ├── software_version.yml
│   │           │       │       ├── static_group_association.yml
│   │           │       │       ├── tag.yml
│   │           │       │       ├── team.yml
│   │           │       │       ├── tenant_group.yml
│   │           │       │       ├── tenant.yml
│   │           │       │       ├── virtual_chassis.yml
│   │           │       │       ├── virtual_machine.yml
│   │           │       │       ├── vlan_group.yml
│   │           │       │       ├── vlan_location.yml
│   │           │       │       ├── vlan.yml
│   │           │       │       ├── vm_interface.yml
│   │           │       │       └── vrf.yml
│   │           │       └── regression-latest
│   │           │           └── tasks
│   │           │               └── main.yml
│   │           ├── test_data.py
│   │           └── unit
│   │               ├── action
│   │               │   ├── __init__.py
│   │               │   └── test_graphql_query.py
│   │               ├── conftest.py
│   │               ├── event_source
│   │               │   ├── __init__.py
│   │               │   └── test_nautobot_changelog.py
│   │               ├── filter
│   │               │   ├── __init__.py
│   │               │   ├── test_data
│   │               │   │   └── graphql_string.json
│   │               │   └── test_graphql.py
│   │               ├── inventory
│   │               │   ├── __init__.py
│   │               │   ├── test_data
│   │               │   │   ├── filter_query_parameters
│   │               │   │   │   └── data.json
│   │               │   │   ├── get_resource_list_chunked
│   │               │   │   │   └── data.json
│   │               │   │   ├── graphql_groups
│   │               │   │   │   └── device_data.json
│   │               │   │   ├── graphql_paginate
│   │               │   │   │   └── device_data.json
│   │               │   │   ├── group_extractors
│   │               │   │   │   └── data.json
│   │               │   │   ├── refresh_url
│   │               │   │   │   └── data.json
│   │               │   │   └── validate_query_parameter
│   │               │   │       └── data.json
│   │               │   ├── test_graphql.py
│   │               │   └── test_nb_inventory.py
│   │               ├── lookup
│   │               │   ├── __init__.py
│   │               │   ├── test_lookup_graphql.py
│   │               │   └── test_lookup.py
│   │               ├── modules
│   │               │   ├── __init__.py
│   │               │   └── test_nautobot_server.py
│   │               └── module_utils
│   │                   ├── fixtures
│   │                   │   └── choices
│   │                   │       ├── circuits.json
│   │                   │       ├── devices.json
│   │                   │       ├── device_types.json
│   │                   │       ├── interfaces.json
│   │                   │       ├── prefixes.json
│   │                   │       ├── racks.json
│   │                   │       ├── services.json
│   │                   │       ├── sites.json
│   │                   │       ├── virtual_machines.json
│   │                   │       └── vlans.json
│   │                   ├── __init__.py
│   │                   ├── test_data
│   │                   │   ├── arg_spec_default
│   │                   │   │   └── data.json
│   │                   │   ├── build_query_params_child
│   │                   │   │   └── data.json
│   │                   │   ├── build_query_params_no_child
│   │                   │   │   └── data.json
│   │                   │   ├── build_query_params_user_query_params
│   │                   │   │   └── data.json
│   │                   │   ├── choices_id
│   │                   │   │   └── data.json
│   │                   │   ├── find_app
│   │                   │   │   └── data.json
│   │                   │   └── normalize_data
│   │                   │       └── data.json
│   │                   ├── test_graphql_utils.py
│   │                   ├── test_nautobot_base_class.py
│   │                   └── test_utils.py
│   └── networktocode.nautobot-5.11.0.info
│       └── GALAXY.yml
├── inventory
│   └── group_vars
│       └── all.yml
├── nautobot_data.yml
├── pb.build-lab.yml
└── roles
    └── load_nautobot
        └── tasks
            └── main.yml

75 directories, 351 files
```

> Having the Nautobot-Ansible collection in your project folder helps with portability and when you need to look at an example for the module you are using they exist in the ```Nautobot-Workshop/ansible-lab/ansible_collections/networktocode/nautobot/plugins/modules``` folder.
{: .prompt-tip }

From a seperate terminal window/tab if you have not already done so, startup you Nautobot Docker instance.
```bash
(nautobot-docker-compose-py3.12) ubuntu@containerlabs:~/Nautobot-Workshop/nautobot-docker-compose$ invoke debug
```

> Using a Python virtual environment (venv) helps you isolate your project’s dependencies, so you don’t accidentally break system packages or conflict with other projects. It ensures your Nautobot or automation toolchain runs with only the required versions of libraries, making your environment reproducible, portable, and safer to upgrade.
{: .prompt-tip }

### Creating Ansible playbook and tasks to load Nautobot
Next create a file ```pb.build-lab.yml``. This will be our Ansible playbook for loading Nautobot and generating the CLAB topology. We will use a ROLE structure for manage our Ansible tasks

```bash
(.ansible) ubuntu@containerlabs:~/Nautobot-Workshop/ansible-lab$ touch inventory/group_vars/all.yml
(.ansible) ubuntu@containerlabs:~/Nautobot-Workshop/ansible-lab$ touch pb.build-lab.yml
```

In these files populate it with the following
all.yml:
```yaml
nb_url: "<your-url-here>"
nb_token: "<your-token-here>"
```

> To create an API key in Nautobot navigate to the admin panel and click the "profile" link. In the profile page you will see a API Tokens link where you can generate a token for your username.
{: .prompt-tip }

pb.build-lab.yml:
```yaml
---
- name: Populate Nautobot & Generate Containerlab topology from Nautobot
  hosts: localhost
  gather_facts: false

  roles:
    - load_nautobot
```

Now create a new folder for the ```load_nautobot``` role, and our tasks will reside in ```roles/load_nautobot/tasks/main.yml```

```bash
(.ansible) ubuntu@containerlabs:~/Nautobot-Workshop/ansible-lab$ mkdir -p roles/load_nautobot/tasks
(.ansible) ubuntu@containerlabs:~/Nautobot-Workshop/ansible-lab$ touch roles/load_nautobot/tasks/main.yml
(.ansible) ubuntu@containerlabs:~/Nautobot-Workshop/ansible-lab$ tree
.
├── pb.build-lab.yml
└── roles
    └── load_nautobot
        └── tasks
            └── main.yml

4 directories, 2 files
```

### Creating the nautobot data files
Now lets create three YAML files in our project root called ```origanization_data.yml```, ```ipam_data.yml```, ```nautobot_devices.yml```.  These files will contain everything needed to get us started in populating Nautobot and building our topology in CLAB. 

| Section                                      | Nautobot Functionality Unlocked                               |
| -------------------------------------------- | ------------------------------------------------------------- |
| `location_types` + `locations`               | Physical/logical hierarchy, mapping, and grouping             |
| `roles`                                      | Automation, compliance, and filtering by function             |
| `manufacturers`, `device_types`, `platforms` | Inventory modeling, config templating, plugin filtering       |
| `software_versions`                          | OS version tracking, Nornir group matching                    |
| `prefixes`, `ip_addresses`                   | IPAM, interface mapping, VRF/subnet usage                     |
| `devices`, `interfaces`                      | Topology, inventory, config generation, connection validation |

origanization_data.yml:
```yaml
location_types:
  - name: HomeLab
    content_type:
      - dcim.device
      - dcim.rack
      - ipam.prefix
      - ipam.vlan
      - dcim.controller
      - circuits.circuittermination
      - dcim.powerpanel
      - dcim.rackgroup
      - ipam.vlangroup
      - ipam.namespace
      - virtualization.cluster

locations:
  - name: Nautobot Workshop
    location_type: HomeLab
  - name: East Side Data Center
    description: "Data Center on the East side of the drawing"
    location_type: HomeLab
    parent: Nautobot Workshop
  - name: West Side Data Center
    description: "Data Center on the West side of the drawing"
    location_type: HomeLab
    parent: Nautobot Workshop
  - name: Backbone
    description: "Backbone between the East and West Data Centers"
    location_type: HomeLab
    parent: Nautobot Workshop

roles:
  - name: Customer Edge Router
    color: 6c5734
    content_types:
      - dcim.device
      - virtualization.virtualmachine
  - name: Datacenter Leaf
    color: ac766f
    content_types:
      - dcim.device
      - virtualization.virtualmachine
  - name: Datacenter Spine
    color: 77e2f7
    content_types:
      - dcim.device
      - virtualization.virtualmachine
  - name: Provider Edge Router
    color: d0530e
    content_types:
      - dcim.device
      - virtualization.virtualmachine
  - name: Provider Route Reflector
    color: '391e91'
    content_types:
      - dcim.device
      - virtualization.virtualmachine
  - name: Provider Router
    color: dfd52f
    content_types:
      - dcim.device
      - virtualization.virtualmachine
  - name: mgmt_switch
    color: 9e9e9e
    content_types:
      - dcim.device
      - virtualization.virtualmachine
```

ipam_data.yml
```yaml
namespaces:
  - name: clabbr220
    description: "Containerlab namespace for the in-band MGMT"
    status: Active

vrfs:
  - name: clabbr220
    namespace: clabbr220
    description: "in-band MGMT"
    rd: "65000:1"

prefixes:
  - prefix: 100.0.11.0/24
  - prefix: 100.0.12.0/24
  - prefix: 100.0.13.0/24
  - prefix: 100.0.22.0/24
  - prefix: 100.0.24.0/24
  - prefix: 100.0.31.0/24
  - prefix: 100.0.33.0/24
  - prefix: 100.0.34.0/24
  - prefix: 100.0.42.0/24
  - prefix: 100.0.43.0/24
  - prefix: 100.0.101.0/24
  - prefix: 100.0.102.0/24
  - prefix: 100.0.111.0/24
  - prefix: 100.0.222.0/24
  - prefix: 100.0.254.0/24
  - prefix: 100.1.11.0/24
  - prefix: 100.1.12.0/24
  - prefix: 100.1.101.0/24
  - prefix: 100.1.102.0/24
  - prefix: 100.1.201.0/24
  - prefix: 100.1.202.0/24
  - prefix: 100.1.222.0/24
  - prefix: 100.1.253.0/24
  - prefix: 100.1.254.0/24
  - prefix: 100.2.11.0/24
  - prefix: 100.2.12.0/24
  - prefix: 100.2.101.0/24
  - prefix: 100.2.102.0/24
  - prefix: 100.2.201.0/24
  - prefix: 100.2.202.0/24
  - prefix: 100.2.253.0/24
  - prefix: 100.2.254.0/24
  - prefix: 2001:db8:100:11::/64
  - prefix: 2001:db8:100:12::/64
  - prefix: 2001:db8:100:13::/64
  - prefix: 2001:db8:100:22::/64
  - prefix: 2001:db8:100:24::/64
  - prefix: 2001:db8:100:31::/64
  - prefix: 2001:db8:100:33::/64
  - prefix: 2001:db8:100:34::/64
  - prefix: 2001:db8:100:42::/64
  - prefix: 2001:db8:100:43::/64
  - prefix: 2001:db8:100:101::/64
  - prefix: 2001:db8:100:102::/64
  - prefix: 2001:db8:100:111::/64
  - prefix: 2001:db8:100:222::/64
  - prefix: 2001:db8:100:254::/64
  - prefix: 2001:db8:101:11::/64
  - prefix: 2001:db8:101:12::/64
  - prefix: 2001:db8:101:253::/64
  - prefix: 2001:db8:101:254::/64
  - prefix: 2001:db8:102:11::/64
  - prefix: 2001:db8:102:12::/64
  - prefix: 2001:db8:102:101::/64
  - prefix: 2001:db8:102:102::/64
  - prefix: 2001:db8:102:201::/64
  - prefix: 2001:db8:102:202::/64
  - prefix: 2001:db8:102:253::/64
  - prefix: 2001:db8:102:254::/64
  - prefix: 192.168.220.0/24
    namespace: clabbr220
    vrf: 0clabbr220

ip_addresses:
  - address: 100.0.11.1/24
  - address: 100.0.11.11/24
  - address: 100.0.12.1/24
  - address: 100.0.12.2/24
  - address: 100.0.13.1/24
  - address: 100.0.13.3/24
  - address: 100.0.22.2/24
  - address: 100.0.22.12/24
  - address: 100.0.24.2/24
  - address: 100.0.24.4/24
  - address: 100.0.31.3/24
  - address: 100.0.31.11/24
  - address: 100.0.33.3/24
  - address: 100.0.33.33/24
  - address: 100.0.34.3/24
  - address: 100.0.34.4/24
  - address: 100.0.42.4/24
  - address: 100.0.42.12/24
  - address: 100.0.43.4/24
  - address: 100.0.43.43/24
  - address: 100.0.101.1/24
  - address: 100.0.101.101/24
  - address: 100.0.102.2/24
  - address: 100.0.102.101/24
  - address: 100.0.111.11/24
  - address: 100.0.111.101/24
  - address: 100.0.222.22/24
  - address: 100.0.254.1/32
  - address: 100.0.254.2/32
  - address: 100.0.254.3/32
  - address: 100.0.254.4/32
  - address: 100.0.254.5/32
  - address: 100.0.254.11/32
  - address: 100.0.254.12/32
  - address: 100.0.254.13/32
  - address: 100.0.254.111/32
  - address: 100.0.254.112/32
  - address: 100.1.11.2/24
  - address: 100.1.11.11/24
  - address: 100.1.12.1/24
  - address: 100.1.12.12/24
  - address: 100.1.101.1/24
  - address: 100.1.101.2/24
  - address: 100.1.102.1/24
  - address: 100.1.102.12/24
  - address: 100.1.201.2/24
  - address: 100.1.201.21/24
  - address: 100.1.202.2/24
  - address: 100.1.202.22/24
  - address: 100.1.222.22/24
  - address: 100.1.253.1/24
  - address: 100.1.253.2/24
  - address: 100.1.253.4/24
  - address: 100.1.253.5/24
  - address: 100.1.253.6/24
  - address: 100.1.253.7/24
  - address: 100.1.254.1/32
  - address: 100.1.254.2/32
  - address: 100.1.254.3/32
  - address: 100.1.254.4/32
  - address: 100.2.11.1/24
  - address: 100.2.11.11/24
  - address: 100.2.12.1/24
  - address: 100.2.12.12/24
  - address: 100.2.101.1/24
  - address: 100.2.101.2/24
  - address: 100.2.102.1/24
  - address: 100.2.102.12/24
  - address: 100.2.201.2/24
  - address: 100.2.201.21/24
  - address: 100.2.202.2/24
  - address: 100.2.202.22/24
  - address: 100.2.253.1/24
  - address: 100.2.253.2/24
  - address: 100.2.253.4/24
  - address: 100.2.253.5/24
  - address: 100.2.253.6/24
  - address: 100.2.253.7/24
  - address: 100.2.254.1/32
  - address: 100.2.254.2/32
  - address: 100.2.254.3/32
  - address: 100.2.254.4/32
  - address: 192.168.220.2/24
    namespace: clabbr220
  - address: 192.168.220.3/24
    namespace: clabbr220
  - address: 192.168.220.4/24
    namespace: clabbr220
  - address: 192.168.220.5/24
    namespace: clabbr220
  - address: 192.168.220.6/24
    namespace: clabbr220
  - address: 192.168.220.7/24
    namespace: clabbr220
  - address: 192.168.220.8/24
    namespace: clabbr220
  - address: 192.168.220.9/24
    namespace: clabbr220
  - address: 192.168.220.10/24
    namespace: clabbr220
  - address: 192.168.220.11/24
    namespace: clabbr220
  - address: 192.168.220.12/24
    namespace: clabbr220
  - address: 192.168.220.13/24
    namespace: clabbr220
  - address: 192.168.220.14/24
    namespace: clabbr220
  - address: 192.168.220.15/24
    namespace: clabbr220
  - address: 192.168.220.16/24
    namespace: clabbr220
  - address: 192.168.220.17/24
    namespace: clabbr220
  - address: 192.168.220.18/24
    namespace: clabbr220
  - address: 192.168.220.19/24
    namespace: clabbr220
  - address: 2001:db8:100:11::1/64
  - address: 2001:db8:100:11::11/64
  - address: 2001:db8:100:12::1/64
  - address: 2001:db8:100:12::2/64
  - address: 2001:db8:100:13::1/64
  - address: 2001:db8:100:13::3/64
  - address: 2001:db8:100:22::2/64
  - address: 2001:db8:100:22::12/64
  - address: 2001:db8:100:24::2/64
  - address: 2001:db8:100:24::4/64
  - address: 2001:db8:100:31::3/64
  - address: 2001:db8:100:31::11/64
  - address: 2001:db8:100:33::3/64
  - address: 2001:db8:100:33::33/64
  - address: 2001:db8:100:34::3/64
  - address: 2001:db8:100:34::4/64
  - address: 2001:db8:100:42::4/64
  - address: 2001:db8:100:42::12/64
  - address: 2001:db8:100:43::4/64
  - address: 2001:db8:100:43::43/64
  - address: 2001:db8:100:101::1/64
  - address: 2001:db8:100:101::101/64
  - address: 2001:db8:100:102::2/64
  - address: 2001:db8:100:102::101/64
  - address: 2001:db8:100:111::11/64
  - address: 2001:db8:100:111::101/64
  - address: 2001:db8:100:222::22/64
  - address: 2001:db8:100:254::1/128
  - address: 2001:db8:100:254::2/128
  - address: 2001:db8:100:254::3/128
  - address: 2001:db8:100:254::4/128
  - address: 2001:db8:100:254::5/128
  - address: 2001:db8:100:254::11/128
  - address: 2001:db8:100:254::12/128
  - address: 2001:db8:100:254::13/128
  - address: 2001:db8:100:254::111/128
  - address: 2001:db8:100:254::112/128
  - address: 2001:db8:101:11::2/64
  - address: 2001:db8:101:12::1/64
  - address: 2001:db8:101:253::1/64
  - address: 2001:db8:101:253::2/64
  - address: 2001:db8:101:253::4/64
  - address: 2001:db8:101:253::5/64
  - address: 2001:db8:101:253::6/64
  - address: 2001:db8:101:253::7/64
  - address: 2001:db8:101:254::1/128
  - address: 2001:db8:101:254::2/128
  - address: 2001:db8:101:254::3/128
  - address: 2001:db8:101:254::4/128
  - address: 2001:db8:102:11::1/64
  - address: 2001:db8:102:11::11/64
  - address: 2001:db8:102:12::1/64
  - address: 2001:db8:102:12::12/64
  - address: 2001:db8:102:101::1/64
  - address: 2001:db8:102:101::2/64
  - address: 2001:db8:102:102::1/64
  - address: 2001:db8:102:102::12/64
  - address: 2001:db8:102:201::2/64
  - address: 2001:db8:102:201::21/64
  - address: 2001:db8:102:202::2/64
  - address: 2001:db8:102:202::22/64
  - address: 2001:db8:102:253::1/64
  - address: 2001:db8:102:253::2/64
  - address: 2001:db8:102:253::4/64
  - address: 2001:db8:102:253::5/64
  - address: 2001:db8:102:253::6/64
  - address: 2001:db8:102:253::7/64
  - address: 2001:db8:102:254::1/128
  - address: 2001:db8:102:254::2/128
  - address: 2001:db8:102:254::3/128
  - address: 2001:db8:102:254::4/128
```

nautobot_devices.yml:
```yaml
manufacturers:
  - name: Arista
  - name: Cisco
  - name: docker

device_types:
  - model: ceos
    u_height: 1
    manufacturer: Arista
  - model: iol
    u_height: 1
    manufacturer: Cisco
  - model: network
    u_height: 1
    manufacturer: docker

platforms:
  - name: EOS
    network_driver: arista_eos
    manufacturer: Arista
  - name: IOS
    network_driver: cisco_ios
    manufacturer: Cisco

software_versions:
  - version: 4.34.0F
    platform: EOS
  - version: 17.12.01
    platform: IOS

devices:
  - name: CE1
    role: Customer Edge Router
    location: West Side Data Center
    device_type: iol
    platform: IOS
    software_version: 17.12.01
    primary_ip4: 192.168.220.9/24
    interfaces:
      - name: Ethernet0/1
        type: 1000base-t
        ipv4_address: 100.0.111.101/24
        ipv6_address: 2001:db8:100:111::101/64
        z_device: PE1
        z_interface: Ethernet0/3
      - name: Ethernet0/2
        type: 1000base-t
        ipv4_address: 100.2.11.1/24
        ipv6_address: 2001:db8:102:11::1/64
        z_device: West-Leaf01
        z_interface: eth7
      - name: Ethernet0/3
        type: 1000base-t
        ipv4_address: 100.2.12.1/24
        ipv6_address: 2001:db8:102:12::1/64
        z_device: West-Spine02
        z_interface: eth7
      - name: Ethernet0/0
        type: 1000base-t
        vrf: clab-mgmt
        ipv4_address: 192.168.220.9/24
      - name: Loopback0
        type: VIRTUAL
        ipv4_address: 100.0.254.111/32
        ipv6_address: 2001:db8:100:254::111/128
  - name: CE2
    role: Customer Edge Router
    location: East Side Data Center
    device_type: iol
    platform: IOS
    software_version: 17.12.01
    primary_ip4: 192.168.220.10/24
    interfaces:
      - name: Ethernet0/1
        type: 1000base-t
        ipv4_address: 100.1.222.22/24
        ipv6_address: 2001:db8:100:222::22/64
        z_device: PE2
        z_interface: Ethernet0/3
      - name: Ethernet0/2
        type: 1000base-t
        ipv4_address: 100.1.11.2/24
        ipv6_address: 2001:db8:101:11::2/64
        z_device: East-Spine01
        z_interface: eth7
      - name: Ethernet0/3
        type: 1000base-t
        ipv4_address: 100.1.12.1/24
        ipv6_address: 2001:db8:101:12::1/64
        z_device: East-Spine02
        z_interface: eth7
      - name: Ethernet0/0
        type: 1000base-t
        vrf: clab-mgmt
        ipv4_address: 192.168.220.10/24
      - name: Loopback0
        type: VIRTUAL
        ipv4_address: 100.0.254.112/32
        ipv6_address: 2001:db8:100:254::112/128
  - name: East-Leaf01
    role: Datacenter Leaf
    location: East Side Data Center 
    device_type: ceos
    platform: EOS
    software_version: 4.34.0F
    primary_ip4: 192.168.220.18/24
    interfaces:
      - name: Loopback0
        type: VIRTUAL
        ipv4_address: 100.1.254.3/32
        ipv6_address: 2001:db8:101:254::3/128
      - name: Port-Channel1
        type: LAG
        mode: Access
      - name: Port-Channel2
        type: LAG
        mode: Access
      - name: Port-Channel3
        type: LAG
        mode: Access
      - name: Port-Channel4
        type: LAG
        mode: Access
      - name: Vlan253
        type: VIRTUAL
        ipv4_address: 100.1.253.1/24
        ipv6_address: 2001:db8:101:253::1/64
      - name: eth1
        type: 1000base-t
        ipv4_address: 100.1.101.2/24
        ipv6_address: 2001:db8:102:101::2/64
        z_device: East-Spine01
        z_interface: eth1
      - name: eth2
        type: 1000base-t
        ipv4_address: 100.1.201.21/24
        ipv6_address: 2001:db8:102:201::21/64
        z_device: East-Spine02
        z_interface: eth1
      - name: eth3
        type: 1000base-t
      - name: eth4
        type: 1000base-t
      - name: eth5
        type: 1000base-t
      - name: eth6
        type: 1000base-t
      - name: Management0
        type: 1000base-t
        vrf: clab-mgmt
        ipv4_address: 192.168.220.18/24
  - name: East-Leaf02
    role: Datacenter Leaf
    location: East Side Data Center 
    device_type: ceos
    platform: EOS
    software_version: 4.34.0F
    primary_ip4: 192.168.220.19/24
    interfaces:
      - name: eth1
        type: 1000base-t
        ipv4_address: 100.1.102.12/24
        ipv6_address: 2001:db8:102:102::12/64
        z_device: East-Spine01
        z_interface: eth2
      - name: eth2
        type: 1000base-t
        ipv4_address: 100.1.202.22/24
        ipv6_address: 2001:db8:102:202::22/64
        z_device: East-Spine02
        z_interface: eth2
      - name: eth3
        type: 1000base-t
      - name: eth4
        type: 1000base-t
      - name: eth5
        type: 1000base-t
      - name: eth6
        type: 1000base-t
      - name: eth7
        type: 1000base-t
      - name: Management0
        type: 1000base-t
        vrf: clab-mgmt
        ipv4_address: 192.168.220.19/24
  - name: East-Spine01
    role: Datacenter Spine
    location: East Side Data Center 
    device_type: ceos
    platform: EOS
    software_version: 4.34.0F
    primary_ip4: 192.168.220.16/24
    interfaces:
      - name: Loopback0
        type: VIRTUAL
        ipv4_address: 100.1.254.1/32
        ipv6_address: 2001:db8:101:254::1/128
      - name: eth1
        type: 1000base-t
        ipv4_address: 100.1.101.1/24
        ipv6_address: 2001:db8:102:101::1/64
        z_device: East-Leaf01
        z_interface: eth1
      - name: eth2
        type: 1000base-t
        ipv4_address: 100.1.102.1/24
        ipv6_address: 2001:db8:102:102::1/64
        z_device: East-Leaf02
        z_interface: eth1
      - name: eth3
        type: 1000base-t
      - name: eth4
        type: 1000base-t
      - name: eth5
        type: 1000base-t
      - name: eth6
        type: 1000base-t
      - name: eth7
        type: 1000base-t
        ipv4_address: 100.1.11.11/24
        ipv6_address: 2001:db8:102:11::11/64
        z_device: CE2
        z_interface: Ethernet0/2
      - name: Management0
        type: 1000base-t
        vrf: clab-mgmt
        ipv4_address: 192.168.220.16/24
  - name: East-Spine02
    role: Datacenter Spine
    location: East Side Data Center 
    device_type: ceos
    platform: EOS
    software_version: 4.34.0F
    primary_ip4: 192.168.220.17/24
    interfaces:
      - name: Loopback0
        type: VIRTUAL
        ipv4_address: 100.1.254.2/32
        ipv6_address: 2001:db8:101:254::2/128
      - name: eth1
        type: 1000base-t
        ipv4_address: 100.1.201.2/24
        ipv6_address: 2001:db8:102:201::2/64
        z_device: East-Leaf01
        z_interface: eth2
      - name: eth2
        type: 1000base-t
        ipv4_address: 100.1.202.2/24
        ipv6_address: 2001:db8:102:202::2/64
        z_device: East-Leaf02
        z_interface: eth2
      - name: eth3
        type: 1000base-t
      - name: eth4
        type: 1000base-t
      - name: eth5
        type: 1000base-t
      - name: eth6
        type: 1000base-t
      - name: eth7
        type: 1000base-t
        ipv4_address: 100.1.12.12/24
        ipv6_address: 2001:db8:102:12::12/64
        z_device: CE2
        z_interface: Ethernet0/3
      - name: Management0
        type: 1000base-t
        ipv4_address: 192.168.220.17/24
        vrf: clab-mgmt
  - name: P1
    role: Provider Router
    location: Backbone
    device_type: iol
    platform: IOS
    software_version: 17.12.01
    primary_ip4: 192.168.220.2/24
    interfaces:
      - name: Ethernet0/0
        type: 1000base-t
      - name: Ethernet0/1
        type: 1000base-t
        ipv4_address: 100.0.12.1/24
        ipv6_address: 2001:db8:100:12::1/64
        z_device: P2
        z_interface: Ethernet0/1
      - name: Ethernet0/2
        type: 1000base-t
        ipv4_address: 100.0.13.1/24
        ipv6_address: 2001:db8:100:13::1/64
        z_device: P3
        z_interface: Ethernet0/2
      - name: Ethernet1/0
        type: 1000base-t
        ipv4_address: 100.0.101.1/24
        ipv6_address: 2001:db8:100:101::1/64
        z_device: RR1
        z_interface: Ethernet0/1
      - name: Ethernet1/1
        type: 1000base-t
        ipv4_address: 100.0.11.1/24
        ipv6_address: 2001:db8:100:11::1/64
        z_device: PE1
        z_interface: Ethernet0/1
      - name: Ethernet0/0
        type: 1000base-t
        vrf: clab-mgmt
        ipv4_address: 192.168.220.2/24
      - name: Loopback0
        type: VIRTUAL
        ipv4_address: 100.0.254.1/32
        ipv6_address: 2001:db8:100:254::1/128
  - name: P2
    role: Provider Router
    location: Backbone
    device_type: iol
    platform: IOS
    software_version: 17.12.01
    primary_ip4: 192.168.220.3/24
    interfaces:
      - name: Ethernet0/0
        type: 1000base-t
      - name: Ethernet0/1
        type: 1000base-t
        ipv4_address: 100.0.12.2/24
        ipv6_address: 2001:db8:100:12::2/64
        z_device: P1
        z_interface: Ethernet0/1
      - name: Ethernet0/2
        type: 1000base-t
        ipv4_address: 100.0.24.2/24
        ipv6_address: 2001:db8:100:24::2/64
        z_device: P4
        z_interface: Ethernet0/2
      - name: Ethernet0/3
        type: 1000base-t
        ipv4_address: 100.0.102.2/24
        ipv6_address: 2001:db8:100:102::2/64
        z_device: RR1
        z_interface: Ethernet0/2
      - name: Ethernet1/0
        type: 1000base-t
        ipv4_address: 100.0.22.2/24
        ipv6_address: 2001:db8:100:22::2/64
        z_device: PE3
        z_interface: Ethernet0/1
      - name: Ethernet0/0
        type: 1000base-t
        vrf: clab-mgmt
        ipv4_address: 192.168.220.3/24
      - name: Loopback0
        type: VIRTUAL
        ipv4_address: 100.0.254.2/32
        ipv6_address: 2001:db8:100:254::2/128
  - name: P3
    role: Provider Router
    location: Backbone
    device_type: iol
    platform: IOS
    software_version: 17.12.01
    primary_ip4: 192.168.220.4/24
    interfaces:
      - name: Ethernet0/0
        type: 1000base-t
      - name: Ethernet0/1
        type: 1000base-t
        ipv4_address: 100.0.34.3/24
        ipv6_address: 2001:db8:100:34::3/64
        z_device: P4
        z_interface: Ethernet0/1
      - name: Ethernet0/2
        type: 1000base-t
        ipv4_address: 100.0.13.3/24
        ipv6_address: 2001:db8:100:13::3/64
        z_device: P1
        z_interface: Ethernet0/2
      - name: Ethernet0/3
        type: 1000base-t
        ipv4_address: 100.0.31.3/24
        ipv6_address: 2001:db8:100:31::3/64
        z_device: PE1
        z_interface: Ethernet0/2
      - name: Ethernet1/0
        type: 1000base-t
        ipv4_address: 100.0.33.3/24
        ipv6_address: 2001:db8:100:33::3/64
        z_device: PE2
        z_interface: Ethernet0/1
      - name: Ethernet0/0
        type: 1000base-t
        vrf: clab-mgmt
        ipv4_address: 192.168.220.4/24
      - name: Loopback0
        type: VIRTUAL
        ipv4_address: 100.0.254.3/32
        ipv6_address: 2001:db8:100:254::3/128
  - name: P4
    role: Provider Router
    location: Backbone
    device_type: iol
    platform: IOS
    software_version: 17.12.01
    primary_ip4: 192.168.220.5/24
    interfaces:
      - name: Ethernet0/0
        type: 1000base-t
      - name: Ethernet0/1
        type: 1000base-t
        ipv4_address: 100.0.34.4/24
        ipv6_address: 2001:db8:100:34::4/64
        z_device: P3
        z_interface: Ethernet0/1
      - name: Ethernet0/2
        type: 1000base-t
        ipv4_address: 100.0.24.4/24
        ipv6_address: 2001:db8:100:24::4/64
        z_device: P2
        z_interface: Ethernet0/2
      - name: Ethernet0/3
        type: 1000base-t
        ipv4_address: 100.0.42.4/24
        ipv6_address: 2001:db8:100:42::4/64
        z_device: PE2
        z_interface: Ethernet0/2
      - name: Ethernet1/0
        type: 1000base-t
        ipv4_address: 100.0.43.4/24
        ipv6_address: 2001:db8:100:43::4/64
        z_device: PE3
        z_interface: Ethernet0/2
      - name: Ethernet0/0
        type: 1000base-t
        vrf: clab-mgmt
        ipv4_address: 192.168.220.5/24
      - name: Loopback0
        type: VIRTUAL
        ipv4_address: 100.0.254.4/32
        ipv6_address: 2001:db8:100:254::4/128
  - name: PE1
    role: Provider Edge Router
    location: Backbone
    device_type: iol
    platform: IOS
    software_version: 17.12.01
    primary_ip4: 192.168.220.6/24
    interfaces:
      - name: Ethernet0/0
        type: 1000base-t
      - name: Ethernet0/1
        type: 1000base-t
        ipv4_address: 100.0.11.11/24
        ipv6_address: 2001:db8:100:11::11/64
        z_device: P1
        z_interface: Ethernet1/1
      - name: Ethernet0/2
        type: 1000base-t
        ipv4_address: 100.0.31.11/24
        ipv6_address: 2001:db8:100:31::11/64
        z_device: P3
        z_interface: Ethernet0/3
      - name: Ethernet0/3
        type: 1000base-t
        ipv4_address: 100.0.111.11/24
        ipv6_address: 2001:db8:100:111::11/64
        z_device: CE1
        z_interface: Ethernet0/1
      - name: Ethernet0/0
        type: 1000base-t
        vrf: clab-mgmt
        ipv4_address: 192.168.220.6/24
      - name: Loopback0
        type: VIRTUAL
        ipv4_address: 100.0.254.11/32
        ipv6_address: 2001:db8:100:254::11/128
  - name: PE2
    role: Provider Edge Router
    location: Backbone
    device_type: iol
    platform: IOS
    software_version: 17.12.01
    primary_ip4: 192.168.220.7/24
    interfaces:
      - name: Ethernet0/0
        type: 1000base-t
      - name: Ethernet0/1
        type: 1000base-t
        ipv4_address: 100.0.33.33/24
        ipv6_address: 2001:db8:100:33::33/64
        z_device: P3
        z_interface: Ethernet1/0
      - name: Ethernet0/2
        type: 1000base-t
        ipv4_address: 100.0.42.12/24
        ipv6_address: 2001:db8:100:42::12/64
        z_device: P4
        z_interface: Ethernet0/3
      - name: Ethernet0/3
        type: 1000base-t
        ipv4_address: 100.0.222.22/24
        ipv6_address: 2001:db8:100:222::22/64
        z_device: CE2
        z_interface: Ethernet0/1
      - name: Ethernet0/0
        type: 1000base-t
        vrf: clab-mgmt
        ipv4_address: 192.168.220.7/24
      - name: Loopback0
        type: VIRTUAL
        ipv4_address: 100.0.254.12/32
        ipv6_address: 2001:db8:100:254::12/128
  - name: PE3
    role: Provider Edge Router
    location: Backbone
    device_type: iol
    platform: IOS
    software_version: 17.12.01
    primary_ip4: 192.168.220.8/24
    interfaces:
      - name: Ethernet0/0
        type: 1000base-t
      - name: Ethernet0/1
        type: 1000base-t
        ipv4_address: 100.0.22.12/24
        ipv6_address: 2001:db8:100:22::12/64
        z_device: P2
        z_interface: Ethernet1/0
      - name: Ethernet0/2
        type: 1000base-t
        ipv4_address: 100.0.43.43/24
        ipv6_address: 2001:db8:100:43::43/64
        z_device: P4
        z_interface: Ethernet1/0
      - name: Ethernet0/3
        type: 1000base-t
      - name: Ethernet0/0
        type: 1000base-t
        vrf: clab-mgmt
        ipv4_address: 192.168.220.8/24
      - name: Loopback0
        type: VIRTUAL
        ipv4_address: 100.0.254.13/32
        ipv6_address: 2001:db8:100:254::13/128
  - name: RR1
    role: Provider Route Reflector
    location: Backbone
    device_type: iol
    platform: IOS
    software_version: 17.12.01
    primary_ip4: 192.168.220.11/24
    interfaces:
      - name: Ethernet0/1
        type: 1000base-t
        ipv4_address: 100.0.101.101/24
        ipv6_address: 2001:db8:100:101::101/64
        z_device: P1
        z_interface: Ethernet1/0
      - name: Ethernet0/2
        type: 1000base-t
        ipv4_address: 100.0.102.101/24
        ipv6_address: 2001:db8:100:102::101/64
        z_device: P2
        z_interface: Ethernet0/3
      - name: Ethernet0/3
        type: 1000base-t
      - name: Ethernet0/0
        type: 1000base-t
        vrf: clab-mgmt
        ipv4_address: 192.168.220.11/24
      - name: Loopback0
        type: VIRTUAL
        ipv4_address: 100.0.254.5/32
        ipv6_address: 2001:db8:100:254::5/128
  - name: West-Leaf01
    role: Datacenter Leaf
    location: West Side Data Center 
    device_type: ceos
    platform: EOS
    software_version: 4.34.0F
    primary_ip4: 192.168.220.14/24
    interfaces:
      - name: Loopback0
        type: VIRTUAL
        ipv4_address: 100.2.254.3/32
        ipv6_address: 2001:db8:102:254::3/128
      - name: Port-Channel1
        type: LAG
        mode: Access
      - name: Port-Channel2
        type: LAG
        mode: Access
      - name: Port-Channel3
        type: LAG
        mode: Access
      - name: Port-Channel4
        type: LAG
        mode: Access
      - name: Vlan253
        type: VIRTUAL
        ipv4_address: 100.2.253.1/24
        ipv6_address: 2001:db8:102:253::1/64
      - name: eth1
        type: 1000base-t
        ipv4_address: 100.2.101.2/24
        ipv6_address: 2001:db8:102:101::2/64
        z_device: West-Spine01
        z_interface: eth1
      - name: eth2
        type: 1000base-t
        ipv4_address: 100.2.201.21/24
        ipv6_address: 2001:db8:102:201::21/64
        z_device: West-Spine02
        z_interface: eth1
      - name: eth3
        type: 1000base-t
      - name: eth4
        type: 1000base-t
      - name: eth5
        type: 1000base-t
      - name: eth6
        type: 1000base-t
      - name: eth7
        type: 1000base-t
        z_device: CE1
        z_interface: Ethernet0/2
      - name: Management0
        type: 1000base-t
        ipv4_address: 192.168.220.14/24
        vrf: clab-mgmt
  - name: West-Leaf02
    role: Datacenter Leaf
    location: West Side Data Center 
    device_type: ceos
    platform: EOS
    software_version: 4.34.0F
    primary_ip4: 192.168.220.15/24
    interfaces:
      - name: Loopback0
        type: VIRTUAL
        ipv4_address: 100.2.254.4/32
        ipv6_address: 2001:db8:102:254::4/128
      - name: Port-Channel1
        type: LAG
        mode: Access
      - name: Port-Channel2
        type: LAG
        mode: Access
      - name: Port-Channel3
        type: LAG
        mode: Access
      - name: Port-Channel4
        type: LAG
        mode: Access
      - name: Vlan253
        type: VIRTUAL
        ipv4_address: 100.2.253.2/24
        ipv6_address: 2001:db8:102:253::2/64
      - name: eth1
        type: 1000base-t
        ipv4_address: 100.2.102.12/24
        ipv6_address: 2001:db8:102:102::12/64
        z_device: West-Spine01
        z_interface: eth2
      - name: eth2
        type: 1000base-t
        ipv4_address: 100.2.202.22/24
        ipv6_address: 2001:db8:102:202::22/64
        z_device: West-Spine02
        z_interface: eth2
      - name: eth3
        type: 1000base-t
      - name: eth4
        type: 1000base-t
      - name: eth5
        type: 1000base-t
      - name: eth6
        type: 1000base-t
      - name: eth7
        type: 1000base-t
      - name: Management0
        type: 1000base-t
        ipv4_address: 192.168.220.15/24
        vrf: clab-mgmt
  - name: West-Spine01
    role: Datacenter Spine
    location: West Side Data Center 
    device_type: ceos
    platform: EOS
    software_version: 4.34.0F
    primary_ip4: 192.168.220.12/24
    interfaces:
      - name: Loopback0
        type: VIRTUAL
        ipv4_address: 100.2.254.1/32
        ipv6_address: 2001:db8:102:254::1/128
      - name: eth1
        type: 1000base-t
        ipv4_address: 100.2.101.1/24
        ipv6_address: 2001:db8:102:101::1/64
        z_device: West-Leaf01
        z_interface: eth1
      - name: eth2
        type: 1000base-t
        ipv4_address: 100.2.102.1/24
        ipv6_address: 2001:db8:102:102::1/64
        z_device: West-Leaf02
        z_interface: eth1
      - name: eth3
        type: 1000base-t
      - name: eth4
        type: 1000base-t
      - name: eth5
        type: 1000base-t
      - name: eth6
        type: 1000base-t
      - name: eth7
        type: 1000base-t
        ipv4_address: 100.2.11.11/24
        ipv6_address: 2001:db8:102:11::11/64
      - name: Management0
        type: 1000base-t
        ipv4_address: 192.168.220.12/24
        vrf: clab-mgmt
  - name: West-Spine02
    role: Datacenter Spine
    location: West Side Data Center 
    device_type: ceos
    platform: EOS
    software_version: 4.34.0F
    primary_ip4: 192.168.220.13/24
    interfaces:
      - name: Loopback0
        type: VIRTUAL
        ipv4_address: 100.2.254.2/32
        ipv6_address: 2001:db8:102:254::2/128
      - name: eth1
        type: 1000base-t
        ipv4_address: 100.2.201.2/24
        ipv6_address: 2001:db8:102:201::2/64
        z_device: West-Leaf01
        z_interface: eth2
      - name: eth2
        type: 1000base-t
        ipv4_address: 100.2.202.2/24
        ipv6_address: 2001:db8:102:202::2/64
        z_device: West-Leaf02
        z_interface: eth2
      - name: eth3
        type: 1000base-t
      - name: eth4
        type: 1000base-t
      - name: eth5
        type: 1000base-t
      - name: eth6
        type: 1000base-t
      - name: eth7
        type: 1000base-t
        ipv4_address: 100.2.12.12/24
        ipv6_address: 2001:db8:102:12::12/64
        z_device: CE1
        z_interface: Ethernet0/3
      - name: Management0
        type: 1000base-t
        ipv4_address: 192.168.220.13/24
        vrf: clab-mgmt
```

### Managing Nautobot with Ansible - Orginizational Models
Now that we've defined our Nautobot data model, let's walk through how to manage and populate Nautobot using Ansible. We'll use the above files along with a set of tasks to automate the creation of locations, roles, platforms, device types, IPAM data, and more, bringing our lab topology to life inside Nautobot.

The ```roles/load_nautobot/tasks/main.yml``` will contain all of our related tasks. I will explain each step as we go.

These Ansible tasks automate the population of organizational data into Nautobot by leveraging the networktocode.nautobot collection. It begins by loading input data from the origanization_data.yml file using include_vars. The first task creates the specified location types in Nautobot, setting them as nestable and applying the relevant content types. Next, it provisions the actual locations, associating each with its location type and, optionally, a parent location and description. Finally, it creates custom roles with specific colors and applicable content types. Each step is loop-driven to process all defined entries efficiently and ensures the state of the resources is set to present, guaranteeing their creation or update.

```yaml
---
- include_vars: ./origanization_data.yml

- name: Create location types
  networktocode.nautobot.location_type:
    url: "{{ nb_url }}"
    token: "{{ nb_token }}"
    validate_certs: false
    name: "{{ item.name }}"
    nestable: true
    content_types: "{{ item.content_type }}"
  loop: "{{ location_types }}"

- name: Create locations
  networktocode.nautobot.location:
    url: "{{ nb_url }}"
    token: "{{ nb_token }}"
    validate_certs: false
    name: "{{ item.name }}"
    status: Active
    location_type:
      name: "{{ item.location_type }}"
    parent: "{{ item.parent |default(omit) }}"
    description: "{{ item.description |default(omit) }}"
    state: present
  loop: "{{ locations }}"

- name: Create roles
  networktocode.nautobot.role:
    url: "{{ nb_url }}"
    token: "{{ nb_token }}"
    validate_certs: false
    name: "{{ item.name }}"
    color: "{{ item.color }}"
    content_types: "{{ item.content_types }}"
    state: present
  loop: "{{ roles }}"
```

This set of Ansible tasks is focused on configuring IP Address Management (IPAM) data in Nautobot using values sourced from the ipam_data.yml file. It starts by creating namespaces, which serve as logical containers for organizing IP-related resources. Next, it provisions VRFs (Virtual Routing and Forwarding instances), associating them with optional namespaces and route distinguishers (RDs) for multi-tenant routing support. The workflow then continues by creating IP prefixes within the specified namespaces and marking them as active. Following that, individual IP addresses are created and also marked active, again optionally scoped to a namespace. The final task assigns the "Loopback" role to IP addresses identified as loopbacks (those with /32 or /128 CIDRs), ensuring these special-purpose addresses are categorized appropriately within Nautobot.

```yaml
- include_vars: ./ipam_data.yml

- name: Create a namespace
  networktocode.nautobot.namespace:
    url: "{{ nb_url }}"
    token: "{{ nb_token }}"
    validate_certs: false
    name: "{{ item.name }}"
    description: "{{ item.description |default(omit) }}"
    state: present
  loop: "{{ namespaces }}"

- name: Create vrf
  networktocode.nautobot.vrf:
    url: "{{ nb_url }}"
    token: "{{ nb_token }}"
    validate_certs: false
    name: "{{ item.name }}"
    description: "{{ item.description |default(omit) }}"
    namespace: "{{ item.namespace | default(omit) }}"
    rd: "{{ item.rd }}"
    state: present
  loop: "{{ vrfs }}"

- name: Create prefixes
  networktocode.nautobot.prefix:
    url: "{{ nb_url }}"
    token: "{{ nb_token }}"
    validate_certs: false
    prefix: "{{ item.prefix }}"
    namespace: "{{ item.namespace | default(omit) }}"
    status: Active
    state: present
  loop: "{{ prefixes }}"

- name: Create IP addresses
  networktocode.nautobot.ip_address:
    url: "{{ nb_url }}"
    token: "{{ nb_token }}"
    validate_certs: false
    address: "{{ item.address }}"
    status: Active
    namespace: "{{ item.namespace | default(omit) }}"
    state: present
  loop: "{{ ip_addresses }}"

- name: Assign Loopback Role to Loopback IPs
  networktocode.nautobot.ip_address:
    url: "{{ nb_url }}"
    token: "{{ nb_token }}"
    validate_certs: false
    address: "{{ item.address }}"
    status: Active
    namespace: "{{ item.namespace | default(omit) }}"
    role: "Loopback"
    state: present
  loop: "{{ ip_addresses }}"
  when: "'/32' in item.address or '/128' in item.address"
```

This set of Ansible tasks is responsible for provisioning physical and logical device inventory in Nautobot, using structured data from the nautobot_devices.yml file. It begins by creating manufacturers, which are required for defining hardware models. Device types are then registered, linking them to their respective manufacturers and specifying physical characteristics such as rack height. Platforms are added next to associate operating systems and automation drivers with manufacturers. Software versions are created and linked to platforms to represent the active firmware or OS running on devices.

The next set of tasks creates the actual devices in Nautobot, assigning them a type, role, and location. Each device’s interfaces are created using a nested loop, ensuring proper interface type and optional mode are set. Following this, IP addresses (both IPv4 and IPv6) are assigned to interfaces where applicable, by checking for the presence of address fields. Finally, cables are created to represent physical connectivity between interfaces on different devices. The cable creation task includes logic to gracefully skip errors related to existing cable connections, ensuring the playbook continues execution without failure when attempting to create already-established links.

```yaml
- include_vars: ./nautobot_devices.yml

- name: Create manufacturers
  networktocode.nautobot.manufacturer:
    url: "{{ nb_url }}"
    token: "{{ nb_token }}"
    validate_certs: false
    name: "{{ item.name }}"
    state: present
  loop: "{{ manufacturers }}"

- name: Create device types
  networktocode.nautobot.device_type:
    url: "{{ nb_url }}"
    token: "{{ nb_token }}"
    validate_certs: false
    model: "{{ item.model }}"
    manufacturer: "{{ item.manufacturer }}"
    u_height: "{{ item.u_height }}"
    is_full_depth: false
    state: present
  loop: "{{ device_types }}"

- name: Create platforms
  networktocode.nautobot.platform:
    url: "{{ nb_url }}"
    token: "{{ nb_token }}"
    validate_certs: false
    name: "{{ item.name }}"
    manufacturer: "{{ item.manufacturer }}"
    network_driver: "{{ item.network_driver }}"
    state: present
  loop: "{{ platforms }}"

- name: Create a software version
  networktocode.nautobot.software_version:
    url: "{{ nb_url }}"
    token: "{{ nb_token }}"
    validate_certs: false
    version: "{{ item.version }}"
    platform: "{{ item.platform }}"
    status: Active
    state: present
  loop: "{{ software_versions }}"
  register: software_version_results

- name: Create devices
  networktocode.nautobot.device:
    url: "{{ nb_url }}"
    token: "{{ nb_token }}"
    validate_certs: false
    name: "{{ item.name }}"
    device_type: "{{ item.device_type }}"
    role: "{{ item.role }}"
    location: "{{ item.location }}"
    platform: "{{ item.platform | default(omit) }}"
    status: Active
    state: present
  loop: "{{ devices }}"
  register: device_results

{%raw%}
- name: Build list of device/software_version ID pairs
  set_fact:
    software_assignments: >-
      {{
        software_assignments | default([]) +
        [ {
          "device_id": (
            device_results.results
            | selectattr('item.name', 'equalto', item.name)
            | map(attribute='device.id')
            | list
            | first
          ),
          "software_version_id": (
            software_version_results.results
            | selectattr('item.version', 'equalto', item.software_version)
            | map(attribute='software_version.id')
            | list
            | first
          )
        } ]
      }}
  loop: "{{ devices }}"
  when: item.software_version is defined
  {%endraw%}

- name: Update device software_version via Nautobot API
  uri:
    url: "{{ nb_url }}/api/dcim/devices/{{ item.device_id }}/"
    method: PATCH
    headers:
      Authorization: "Token {{ nb_token }}"
      Content-Type: "application/json"
    body: |
      {
        "software_version": "{{ item.software_version_id }}"
      }
    body_format: json
    validate_certs: false
    status_code: 200
  loop: "{{ software_assignments }}"
  when: item.device_id is not none and item.software_version_id is not none
{%raw%}
- name: Create interfaces for each device
  networktocode.nautobot.device_interface:
    url: "{{ nb_url }}"
    token: "{{ nb_token }}"
    validate_certs: false
    device: "{{ item.0.name }}"
    name: "{{ item.1.name }}"
    type: "{{ item.1.type }}"
    mode: "{{ item.1.mode | default(omit) }}"
    mgmt_only: "{% if item.1.ipv4_address is defined and '192.168.220.' in item.1.ipv4_address %}true{% else %}false{% endif %}"
    enabled: True
    status: Active
    state: present
  loop: "{{ devices | subelements('interfaces', 'skip_missing=True') }}"
{%endraw%}
- name: Add IPv4 addresses to interfaces
  networktocode.nautobot.ip_address_to_interface:
    url: "{{ nb_url }}"
    token: "{{ nb_token }}"
    validate_certs: false
    ip_address:
      address: "{{ item.1.ipv4_address }}"
    interface:
      name: "{{ item.1.name }}"
      device: "{{ item.0.name }}"
  loop: "{{ devices | subelements('interfaces', 'skip_missing=True') }}"
  when: item.1.ipv4_address is defined

- name: Add IPv6 addresses to interfaces
  networktocode.nautobot.ip_address_to_interface:
    url: "{{ nb_url }}"
    token: "{{ nb_token }}"
    validate_certs: false
    ip_address:
      address: "{{ item.1.ipv6_address }}"
    interface:
      name: "{{ item.1.name }}"
      device: "{{ item.0.name }}"
  loop: "{{ devices | subelements('interfaces', 'skip_missing=True') }}"
  when: item.1.ipv6_address is defined

- name: Assign Primary IPv4 to Device
  networktocode.nautobot.device:
    url: "{{ nb_url }}"
    token: "{{ nb_token }}"
    validate_certs: false
    name: "{{ item.name }}"
    primary_ip4: "{{ item.primary_ip4 }}"
    status: Active
    state: present
  loop: "{{ devices }}"

- name: Create cable within Nautobot
  networktocode.nautobot.cable:
    url: "{{ nb_url }}"
    token: "{{ nb_token }}"
    validate_certs: false
    termination_a_type: dcim.interface
    termination_a:
      device: "{{ item.0.name }}"
      name: "{{ item.1.name }}"
    termination_b_type: dcim.interface
    termination_b:
      device: "{{ item.1.z_device }}"
      name: "{{ item.1.z_interface }}"
    status: Connected
    state: present
  loop: "{{ devices | subelements('interfaces', skip_missing=True) }}"
  loop_control:
    label: "{{ item.0.name }} -> {{ item.1.name }}"
  when: item.1.z_interface is defined
  register: cable_result
  failed_when: >
    cable_result.failed and
    ('already has a cable attached' not in (cable_result.msg | default('')) and
     'cable dcim.interface' not in (cable_result.msg | default('')))
```

## Conclusion
With these Ansible tasks, we’ve demonstrated how to take structured YAML data and turn it into a fully populated and interconnected network inventory within Nautobot. From establishing your organizational structure and IPAM foundations to modeling devices, interfaces, and physical cabling, this approach provides a reproducible, automated workflow for managing lab or production environments. By leveraging the Nautobot Ansible Collection, you gain precise control over your source of truth while keeping your infrastructure as code practices intact. Whether you're building out a lab for testing or automating a production deployment, this method ensures consistency, traceability, and scalability across your network operations.