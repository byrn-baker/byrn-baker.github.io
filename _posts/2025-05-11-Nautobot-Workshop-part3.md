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

[origanization_data.yml](https://github.com/byrn-baker/Nautobot-Workshop/blob/main/ansible-lab/nautobot-data/origanization_data.yml)

[ipam_data.yml](https://github.com/byrn-baker/Nautobot-Workshop/blob/main/ansible-lab/nautobot-data/ipam_data.yml)

[nautobot_devices.yml](https://github.com/byrn-baker/Nautobot-Workshop/blob/main/ansible-lab/nautobot-data/nautobot_devices.yml)

### Managing Nautobot with Ansible - Orginizational Models
Now that we've defined our Nautobot data model, let's walk through how to manage and populate Nautobot using Ansible. We'll use the above files along with a set of tasks to automate the creation of locations, roles, platforms, device types, IPAM data, and more, bringing our lab topology to life inside Nautobot.

The ```roles/load_nautobot/tasks/main.yml``` will contain all of our related tasks. I will explain each step as we go.

These Ansible tasks automate the population of organizational data into Nautobot by leveraging the networktocode.nautobot collection. It begins by loading input data from the origanization_data.yml file using include_vars. The first task creates the specified location types in Nautobot, setting them as nestable and applying the relevant content types. Next, it provisions the actual locations, associating each with its location type and, optionally, a parent location and description. Finally, it creates custom roles with specific colors and applicable content types. Each step is loop-driven to process all defined entries efficiently and ensures the state of the resources is set to present, guaranteeing their creation or update.

[main.yml](https://github.com/byrn-baker/Nautobot-Workshop/blob/main/ansible-lab/roles/load_nautobot/tasks/main.yml)

This set of Ansible tasks is focused on configuring IP Address Management (IPAM) data in Nautobot using values sourced from the ipam_data.yml file. It starts by creating namespaces, which serve as logical containers for organizing IP-related resources. Next, it provisions VRFs (Virtual Routing and Forwarding instances), associating them with optional namespaces and route distinguishers (RDs) for multi-tenant routing support. The workflow then continues by creating IP prefixes within the specified namespaces and marking them as active. Following that, individual IP addresses are created and also marked active, again optionally scoped to a namespace. The final task assigns the "Loopback" role to IP addresses identified as loopbacks (those with /32 or /128 CIDRs), ensuring these special-purpose addresses are categorized appropriately within Nautobot.

This set of Ansible tasks is responsible for provisioning physical and logical device inventory in Nautobot, using structured data from the nautobot_devices.yml file. It begins by creating manufacturers, which are required for defining hardware models. Device types are then registered, linking them to their respective manufacturers and specifying physical characteristics such as rack height. Platforms are added next to associate operating systems and automation drivers with manufacturers. Software versions are created and linked to platforms to represent the active firmware or OS running on devices.

The next set of tasks creates the actual devices in Nautobot, assigning them a type, role, and location. Each device’s interfaces are created using a nested loop, ensuring proper interface type and optional mode are set. Following this, IP addresses (both IPv4 and IPv6) are assigned to interfaces where applicable, by checking for the presence of address fields. Finally, cables are created to represent physical connectivity between interfaces on different devices. The cable creation task includes logic to gracefully skip errors related to existing cable connections, ensuring the playbook continues execution without failure when attempting to create already-established links.

## Conclusion
With these Ansible tasks, we’ve demonstrated how to take structured YAML data and turn it into a fully populated and interconnected network inventory within Nautobot. From establishing your organizational structure and IPAM foundations to modeling devices, interfaces, and physical cabling, this approach provides a reproducible, automated workflow for managing lab or production environments. By leveraging the Nautobot Ansible Collection, you gain precise control over your source of truth while keeping your infrastructure as code practices intact. Whether you're building out a lab for testing or automating a production deployment, this method ensures consistency, traceability, and scalability across your network operations.