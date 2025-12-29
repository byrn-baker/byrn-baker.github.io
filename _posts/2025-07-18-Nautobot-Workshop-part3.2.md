---
title: Nautobot Workshop Blog Series - Part 3.2 Using the Nautobot Design Builder App
date: 2025-07-18 09:00:00
categories: [Nautobot, Ansible, Automation]
tags: [NetworkAutomation, NetworkSourceOfTruth, nautobot, AutomationPlatform, NautobotTutorials]
lab_vps_banner: true
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


## Building BGP Infrastructure with Nautobot Design Builder: Extending the BGP Peering Extension
<div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
  <iframe src="https://www.youtube.com/embed/vGvwJLQdbCs" 
          frameborder="0" 
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
          allowfullscreen 
          style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
  </iframe>
</div>

[▶️ Watch the video](https://youtube.com/shorts/vGvwJLQdbCs)

Update on a couple of things I did to help the Design Builder App fully deploy the intial data needed for this Nautobot Workshop.

## The Challenge: BGP Peering Complexity

The Nautobot Design Builder app comes with an extension to add peering endpoints to the Nautobot BGP Models plugin, but it had limitations when dealing with specific fields related to these endpoint models. Specifically, the original extension didn't properly handle additional endpoint fields like:
- Peer group
- Interface
- IP address
- Description

For my workshop, I needed to create a comprehensive BGP infrastructure that would demonstrate realistic network topologies with proper peer group configurations and interface bindings and Descriptions.

## The Solution: Custom Extension Development

### Creating the Enhanced BGP Template

First, I developed a comprehensive Jinja2 template that could handle complex BGP configurations:

```yaml
{% raw %}
autonomous_systems:
{% for device in bgp_routing if device.bgp is defined %}
  - "!create_or_update:asn": {{ device.bgp.asn }}
    description: {{ device.bgp.description | default("ASN for " ~ device.name) }}
    status__name: Active
    "!ref": "{{ device.name | lower | replace('-', '_') }}_{{ device.bgp.asn }}"
{% endfor %}

bgp_routing_instances:
{% for device in bgp_routing if device.bgp is defined %}
  - "!create_or_update:device": "!ref:{{ device.name | lower | replace('-', '_') }}"
    "!ref": "{{ device.name | lower | replace('-', '_') }}_{{ device.bgp.asn }}_ri"
    autonomous_system__asn: {{ device.bgp.asn }}
    status__name: Active
    router_id: "!ref:{{ device.name | lower | replace('-', '_') }}_loopback0_ipv4"
{% endfor %}

bgp_address_families:
{% for device in bgp_routing if device.bgp is defined %}
  {% for af in device.bgp.afi_safi %}
  - "!create_or_update:afi_safi": {{ af.afi_safi }}
    routing_instance: "!ref:{{ device.name | lower | replace('-', '_') }}_{{ device.bgp.asn }}_ri"
    {% if af.extra_attributes is defined %}
    extra_attributes:
{% for key, value in af.extra_attributes.items() %}
      {{ key }}: {{ value }}
{% endfor %}
    {% endif %}
  {% endfor %}
{% endfor %}

bgp_peer_groups:
{% for device in bgp_routing if device.bgp is defined %}
  {% for pg in device.bgp.bgp_peer_groups %}
  - "!create:name": {{ pg.name }}
    "!ref": "{{ device.name | lower | replace('-', '_') }}_{{ device.bgp.asn }}_{{ pg.name | lower | replace('-', '_') }}_pg"
    routing_instance: "!ref:{{ device.name | lower | replace('-', '_') }}_{{ device.bgp.asn }}_ri"
    autonomous_system__asn: {{ pg.peer_asn }}
    enabled: true
    {% if pg.local_interface is defined %}
    source_interface: "!ref:{{ device.name | lower | replace('-', '_') }}_{{ pg.local_interface | lower | replace('/', '_') | replace('-', '_') }}"
    {% endif %}
    {% if pg.extra_attributes is defined %}
    extra_attributes:
          {% for key, value in pg.extra_attributes.items() %}
      {{ key }}: {{ value }}
          {% endfor %}
        {% endif %}
  {% endfor %}
{% endfor %}

bgp_peer_group_address_families:
{% for device in bgp_routing if device.bgp is defined %}
  {% for pg in device.bgp.bgp_peer_groups %}
    {% if pg.afi_safi is defined %}
      {% for af in pg.afi_safi %}
  - "!create:afi_safi": {{ af.afi_safi }}
    peer_group: "!ref:{{ device.name | lower | replace('-', '_') }}_{{ device.bgp.asn }}_{{ pg.name | lower | replace('-', '_') }}_pg"
    import_policy: {{ pg.in_route_map }}
    export_policy: {{ pg.out_route_map }}
    multipath: true
        {% if af.extra_attributes is defined %}
    extra_attributes:
          {% for key, value in af.extra_attributes.items() %}
      {{ key }}: {{ value }}
          {% endfor %}
        {% endif %}
      {% endfor %}
    {% endif %}
  {% endfor %}
{% endfor %}

{% macro bgp_peer_endpoint(dev, asn, intf, ip, peer_group, peer_dev, peer_intf, device_ctx=None) -%}
routing_instance: "!ref:{{ dev | lower | replace('-', '_') }}_{{ asn }}_ri"
source_interface: "!ref:{{ dev | lower | replace('-', '_') }}_{{ intf | lower | replace('/', '_') | replace('-', '_') }}"
source_ip: "!ref:{{ dev | lower | replace('-', '_') }}_{{ intf | lower | replace('/', '_') | replace('-', '_') }}_{{ 'ipv4' if ':' not in ip else 'ipv6' }}"
{% if peer_group and device_ctx %}
peer_group: "!ref:{{ device_ctx | lower | replace('-', '_') }}_{{ asn }}_{{ peer_group | lower | replace('-', '_') }}_pg"
{% endif %}
description: {{ peer_dev }}_{{ peer_intf }}
{%- endmacro %}

{% set seen = namespace(keys=[]) %}
bgp_peerings:
{% for device in bgp_routing if device.bgp is defined and device.bgp.bgp_peers is defined %}
  {% set local_dev = device.name %}
  {% set local_asn = device.bgp.asn %}
  {% for peer in device.bgp.bgp_peers %}
    {% set peer_dev = peer.peer_device %}
    {% set peer_asn = peer.peer_asn if peer.peer_asn is defined else (
        (bgp_routing | selectattr("name", "equalto", peer_dev) | map(attribute="bgp.asn") | list | first)
    ) %}
    {% set local_ip = peer.local_address %}
    {% set peer_ip = peer.peer_address %}
    {% set local_intf = peer.local_interface %}
    {% set peer_intf = peer.peer_interface %}
    {% set local_peer_group = peer.local_peer_group if peer.local_peer_group is defined else None %}
    {% set remote_peer_group = peer.remote_peer_group if peer.remote_peer_group is defined else None %}
    {% set description = peer_dev ~ "_" ~ peer_intf %}
    {% set endpoints = [
      local_dev, local_asn, local_intf, local_ip, local_peer_group or '',
      peer_dev, peer_asn, peer_intf, peer_ip, remote_peer_group or ''
    ] %}
    {% set peering_key = endpoints | map('string') | sort | join('__') %}
    {% if peering_key not in seen.keys %}
      {% set _ = seen.keys.append(peering_key) %}
- "!bgp_peering":
    endpoints:
      - {{ bgp_peer_endpoint(local_dev, local_asn, local_intf, local_ip, local_peer_group, local_dev) | indent(8, false) }}
      - {{ bgp_peer_endpoint(peer_dev, peer_asn, peer_intf, peer_ip, remote_peer_group, peer_dev) | indent(8, false) }}
    status__name: "Active"
    {% endif %}
  {% endfor %}
{% endfor %}
{% endraw %}
```

This template systematically creates all the necessary BGP components, from autonomous systems to peer groups and individual peerings.

### The Key Innovation: Enhanced Peer Endpoint Building
The core improvement was in the ```build_peer_endpoint``` method of the BGPPeeringExtension class:

```python
def build_peer_endpoint(self, endpoint_data):
    """Build or look up a PeerEndpoint using !refs, ModelInstances, or filters."""
    endpoint = dict(endpoint_data)

    # Handle routing instance resolution
    if "routing_instance" in endpoint:
        endpoint["routing_instance"] = self.resolve_or_create(self.RoutingInstance, endpoint["routing_instance"])
    elif any(k.startswith("routing_instance__") for k in endpoint.keys()):
        ri_filter = {k.replace("routing_instance__", ""): endpoint.pop(k) for k in list(endpoint) if k.startswith("routing_instance__")}
        endpoint["routing_instance"] = self.resolve_or_create(self.RoutingInstance, ri_filter)

    # Handle peer group resolution
    if "peer_group" in endpoint:
        endpoint["peer_group"] = self.resolve_or_create(self.PeerGroup, endpoint["peer_group"])
    elif "peer_group__name" in endpoint:
        ri = endpoint["routing_instance"]
        endpoint["peer_group"] = self.resolve_or_create(
            self.PeerGroup,
            {
                "name": endpoint.pop("peer_group__name"),
                "routing_instance": ri,
            },
        )

    # Handle source interface and IP resolution
    if "source_interface" in endpoint:
        endpoint["source_interface"] = self.resolve_or_create(
            self.Interface,
            endpoint["source_interface"],
        )

    if "source_ip" in endpoint:
        endpoint["source_ip"] = self.resolve_or_create(
            self.IPAddress,
            endpoint["source_ip"],
        )

    return self.PeerEndpoint(self.environment, endpoint)
```

This enhanced method properly resolves all the BGP Models endpoint fields which provides a richer more accurate configurations.

### Testing the Solution: Docker Development Environment
One of the most elegant aspects of this solution was how easy it was to test changes using Docker. Here's the docker-compose configuration that made development seamless:

```yaml
services:
  nautobot:
    command: "nautobot-server runserver 0.0.0.0:8080"
    ports:
      - "8080:8080"
    volumes:
      - "../config/nautobot_config.py:/opt/nautobot/nautobot_config.py"
      - "../jobs:/opt/nautobot/jobs"
      - "../custom_jinja_filters:/opt/nautobot/custom_jinja_filters"
      - "../custom_python_code/custom_ext.py:/usr/local/lib/python${PYTHON_VER}/site-packages/nautobot_design_builder/contrib/ext.py"
    healthcheck:
      interval: "30s"
      timeout: "10s"
      start_period: "60s"
      retries: 3
      test: ["CMD", "true"]
      
  celery_worker:
    volumes:
      - "../config/nautobot_config.py:/opt/nautobot/nautobot_config.py"
      - "../jobs:/opt/nautobot/jobs"
      - "../custom_jinja_filters:/opt/nautobot/custom_jinja_filters"
      - "../custom_python_code/custom_ext.py:/usr/local/lib/python${PYTHON_VER}/site-packages/nautobot_design_builder/contrib/ext.py"
```

The key insight here is the volume mapping that replaces the default ```ext.py``` file with our custom version:

```
"../custom_python_code/custom_ext.py:/usr/local/lib/python${PYTHON_VER}/site-packages/nautobot_design_builder/contrib/ext.py"
```

This approach allowed me to rapidly iterate on the extension code without rebuilding containers or complex installation procedures.

### The Results: Complex BGP Topologies Made Simple
With these enhancements, I could create sophisticated BGP configurations using simple YAML definitions:

```yaml
- "!bgp_peering":
    endpoints:
      - routing_instance: "!ref:rr1_65000_ri"
        source_interface: "!ref:rr1_loopback0"
        source_ip: "!ref:rr1_loopback0_ipv4"
        peer_group: "!ref:backbone_rr_ipv4_peers_pg"
        description: rr1_loopback0
      - routing_instance: "!ref:p1_65000_ri"
        source_interface: "!ref:p1_loopback0"
        source_ip: "!ref:p1_loopback0_ipv4"
        peer_group: "!ref:backbone_rr_ipv4_peers_pg"
        description: p1_loopback0
    status__name: "Active"
```

This creates fully functional BGP peerings with proper peer group associations, interface bindings, and IP address assignments.

## Contributing Back to the Community
The beauty of open-source software is the ability to contribute improvements back to the community. Here's how you can submit your enhancements to the Nautobot Design Builder project, following the official Nautobot contribution guidelines:

**Step 1**: Check Existing Issues and Discussions
Before starting work, ensure your enhancement hasn't already been requested or implemented:
- Search GitHub issues for existing feature requests or bug reports
- Check GitHub discussions for ongoing conversations
- Consider starting with a GitHub Discussion to validate and shape your proposed featureutobot-app-design-builder

**Step 2**: Create or Identify an Issue
If your enhancement is substantial:
- Open a new GitHub issue describing your proposed changes
- Include a detailed description of the functionality being proposed
- Provide a use case explaining who would use it and what value it adds
- Ask to be assigned to the issue so others know it's being worked on

**Step 3**: Fork and Clone the Repository
```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/nautobot-app-design-builder.git
cd nautobot-app-design-builder
```

***Step 4***: Test Your Changes
```bash
# Run the test suite to ensure nothing is broken
poetry run pytest

# Test your specific functionality
poetry run pytest tests/test_bgp_extensions.py -v
```

**Step 5**: Create a Feature Branch
```bash
# Create a descriptive branch name
git checkout -b feature/enhanced-bgp-peering-extension
```

***Step 6***: Make Your Changes
Replace the existing BGP peering extension with your enhanced version:
```bash
# Copy your custom_ext.py changes to the appropriate location
cp /path/to/your/custom_ext.py nautobot_design_builder/contrib/ext.py
```

**Step 7**: Test Your Changes
Ensure your changes don't break existing functionality:
```bash
# Run the full test suite
poetry run pytest

# Test your specific functionality
poetry run pytest tests/test_bgp_extensions.py -v
```

**Step 8**: Create Changelog Fragment
All pull requests must include a changelog fragment in the ```./changes``` directory:
```bash
# Create a fragment using your GitHub issue number and type
# Valid types: added, changed, dependencies, deprecated, documentation, fixed, housekeeping, removed, security
echo "Enhanced BGP peering extension with peer group support and improved configuration handling." > changes/123.added
```

**Step 9**: Document Your Changes
Create or update documentation explaining:
- What the enhancement does
- How to use the new features
- Any breaking changes
- Examples of the new functionality

**Step 10**: Commit Your Changes
Follow good commit practices:
```bash
git add .
git commit -m "Enhanced BGP peering extension with peer group support

- Added comprehensive peer group resolution
- Improved source interface and IP handling
- Enhanced endpoint description generation
- Added support for complex BGP configurations

Fixes #123"
```

**Step 11**: Submit a Pull Request
```bash
# Push to your fork
git push origin feature/enhanced-bgp-peering-extension
```

Then create a pull request on GitHub with:
- A clear description of the changes
- Reference to the related GitHub issue
- The problem it solves
- Examples of how to use the new functionality
- Any relevant test results

**Step 12**: Code Review and Collaboration
- Be responsive to feedback from maintainers
- Make requested changes promptly
- Ensure all CI checks pass (Python syntax, tests, PEP 8 compliance)
- Be patient as the review process may take some time depending on the complexity and current backlog

>**Note**: All code submissions must meet the following criteria:
- Python syntax is valid
- All unit tests pass successfully
- PEP 8 compliance is enforced (lines may be greater than 80 characters)
- At least one changelog fragment is included
{: .prompt-tip }

## Lessons Learned
This project taught me several valuable lessons about extending Nautobot:
1. **Docker Development**: Using volume mounts to override package files makes rapid prototyping incredibly efficient
2. **Extension Architecture**: The Design Builder's extension system is flexible and powerful when you understand the underlying patterns
3. **Community Contribution**: Open-source projects thrive on community contributions, and the maintainers are typically very welcoming of thoughtful improvements
4. **Testing is Critical**: Even small changes can have unexpected consequences, so thorough testing is essential

### Communication Channels:
- **GitHub Issues**: For feature requests and bug reports
- **GitHub Discussions**: For general discussion and support
- **Slack**: Join the #nautobot channel on Network to Code Slack for quick questions

Following these guidelines ensures your contribution aligns with the Nautobot project's standards and increases the likelihood of acceptance into the codebase.

## Conclusion
The Nautobot Design Builder app provides a strong foundation for building complex network data models. By extending its capabilities and contributing back to the community, we can make it even more powerful for real-world networking scenarios.

This was my first time contributing updates to a project I didn’t originally create, and it was a rewarding experience. The enhanced BGP peering extension I developed for my workshop highlights how custom extensions can address sophisticated networking requirements while preserving the clarity and flexibility that make Nautobot such a compelling tool.

Whether you're preparing for a workshop, automating production infrastructure, or exploring new ways to model network designs, the combination of Nautobot, the Design Builder app, and custom extensions offers a robust and adaptable platform for network automation.