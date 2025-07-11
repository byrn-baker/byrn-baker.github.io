---
title: Nautobot Workshop Blog Series - Part 6 - Extending Nautobot's Data Model - A Deep Dive into Custom Fields and Computed Fields
date: 2025-07-09 9:10:00
categories: [Nautobot,Ansible,Automtation]
tags: [Nautobot,NetworkAutomation,CustomFields,ComputedFields,NetworkSourceOfTruth]
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


## Part 6 - Extending Nautobot's Data Model: A Deep Dive into Custom Fields and Computed Fields

As network automation continues to evolve, the need for flexible, extensible network source of truth solutions becomes increasingly critical. Nautobot, the modern network automation platform, addresses this need through its powerful custom fields and computed fields capabilities. These features allow network engineers to extend Nautobot's core data model without modifying the underlying code, making it possible to capture organization-specific network attributes and derive meaningful insights from existing data.

## Understanding Custom Fields in Nautobot

Custom fields in Nautobot provide a mechanism to add additional attributes to existing content types without requiring database schema changes or code modifications. They offer a declarative way to extend the data model, making Nautobot adaptable to diverse network environments and organizational requirements.

### Types of Custom Fields

Nautobot supports several custom field types, each designed for specific data requirements:

- **Text Fields**: For free-form text input with optional validation
- **Integer Fields**: For numeric values with optional range constraints
- **Boolean Fields**: For true/false values with configurable defaults
- **Select Fields**: For predefined choice lists ensuring data consistency
- **Multi-Select Fields**: For scenarios requiring multiple selections
- **Date Fields**: For timestamp and scheduling information
- **URL Fields**: For storing web links and references
- **JSON Fields**: For complex structured data storage

### Real-World Implementation: OSPF Configuration Management

Let's examine a practical implementation using OSPF (Open Shortest Path First) protocol configuration as an example. Network engineers often need to track various OSPF parameters at the interface level, which aren't part of Nautobot's core data model.

```yaml
custom_fields:
  - name: OSPF Network Type
    grouping: OSPF
    description: Network type for OSPF
    key: ospf_network_type
    type: select
    choices:
      - point-to-point
      - broadcast
      - non-broadcast
      - point-to-multipoint
    content_types:
      - dcim.interface
```

This custom field demonstrates several key concepts:

**Grouping**: The `grouping` parameter organizes related fields in the user interface, making it easier to manage large numbers of custom fields. Here, all OSPF-related fields are grouped together.

**Data Validation**: The `select` type ensures only valid OSPF network types can be chosen, preventing configuration errors and maintaining data integrity.

**Content Type Targeting**: By specifying `dcim.interface`, this field only appears on interface objects, keeping the UI clean and contextually relevant.

### Advanced Custom Field Features

#### Regular Expression Validation

For fields requiring specific formats, Nautobot supports regex validation:

```yaml
  - name: OSPF Area
    grouping: OSPF
    description: OSPF Area ID assigned to this interface (decimal or dotted format)
    key: ospf_area
    type: text
    validation_regex: ^([0-9]{1,10}|([0-9]{1,3}\.){3}[0-9]{1,3})$
    content_types:
      - dcim.interface
```

This field accepts OSPF area IDs in both decimal format (e.g., "0", "1", "100") and dotted decimal format (e.g., "0.0.0.0", "10.0.0.1"), providing flexibility while maintaining data consistency.

#### Default Values and Boolean Logic

Boolean fields can include default values, streamlining data entry:

```yaml
  - name: OSPF BFD Enabled
    grouping: OSPF
    description: Enable BFD for OSPF on this interface
    key: ospf_bfd
    type: boolean
    default: false
    content_types:
      - dcim.interface
```

This approach reduces manual data entry while ensuring consistent defaults across the network infrastructure.

### Building a Comprehensive Configuration Framework

The complete OSPF custom field implementation creates a comprehensive framework for managing OSPF configurations:

- **Network Type**: Defines the OSPF network behavior
- **Area Assignment**: Associates interfaces with OSPF areas
- **Cost Metrics**: Influences OSPF path selection
- **Authentication**: Secures OSPF communications
- **Timing Parameters**: Controls OSPF hello and dead intervals
- **BFD Integration**: Enables fast failure detection

This framework transforms Nautobot from a basic network inventory tool into a comprehensive OSPF configuration management system.

## Computed Fields: Deriving Intelligence from Data

While custom fields extend the data model with additional storage, computed fields provide dynamic calculations and data derivation capabilities. Computed fields execute code to generate values based on existing object attributes, creating intelligent, context-aware information.

### Common Use Cases for Computed Fields

#### Network Calculations
- **Full Device Name**: Concatenate device name with site and role (e.g., "switch01-datacenter-access")
- **Interface Naming Compliance**: Validate interface names against organizational standards using regex
- **Power Budget Status**: Calculate remaining power capacity from device power draw and rack limits

#### Compliance and Validation
- **Configuration Compliance**: Verify adherence to organizational standards
- **Security Posture**: Assess security configuration status
- **Documentation Status**: Track configuration documentation completeness

#### Operational Intelligence
- **Environmental Monitoring**: Calculate power consumption and cooling requirements
- **Capacity Planning**: Determine growth projections and resource requirements
- **Performance Metrics**: Aggregate and analyze network performance data

### Implementation Strategies

When implementing computed fields, consider these architectural patterns:

**Caching Strategy**: Computed fields can be resource-intensive. Implement appropriate caching mechanisms to balance performance with data freshness requirements.

**Error Handling**: Robust error handling ensures computed fields gracefully handle missing or invalid data, preventing system instability.

**Performance Optimization**: Complex calculations should be optimized for performance, particularly when applied to large datasets.

## Best Practices for Custom and Computed Fields

### Design Principles

**Semantic Naming**: Use clear, descriptive names that reflect the field's purpose and content. Avoid technical jargon that might confuse users.

**Logical Grouping**: Organize related fields into logical groups, making the interface intuitive and reducing cognitive load.

**Validation Strategy**: Implement appropriate validation rules to ensure data quality while maintaining usability.

**Documentation**: Provide clear descriptions and examples for each custom field, facilitating adoption and reducing support overhead.

### Maintenance and Evolution

**Regular Review**: Periodically review custom field usage and relevance, removing unused fields to maintain system cleanliness.

**Performance Monitoring**: Monitor the performance impact of custom and computed fields, optimizing as necessary to maintain system responsiveness.

**User Feedback**: Gather user feedback on custom field effectiveness and usability, iterating based on operational experience.

## Advanced Integration Patterns

### Workflow Integration

Custom fields can integrate with Nautobot's workflow engine, enabling automated validation and processing:

```python
# Example workflow integration
def validate_ospf_configuration(interface):
    if interface.custom_field_data.get('ospf_enabled'):
        required_fields = ['ospf_area', 'ospf_network_type']
        for field in required_fields:
            if not interface.custom_field_data.get(field):
                raise ValidationError(f"OSPF enabled interfaces require {field}")
```

### GraphQL Integration

Custom fields automatically integrate with Nautobot's GraphQL API, enabling sophisticated queries:

```graphql
query {
  devices {
    name
    interfaces {
      name
    cf_ospf_network_type
    cf_ospf_area
    cf_ospf_bfd
    }
  }
}
```

## Future Considerations

As networks become increasingly complex and software-defined, the importance of flexible, extensible network documentation systems grows. Nautobot's custom fields and computed fields provide the foundation for building sophisticated network management platforms that can adapt to evolving requirements.

The combination of custom fields for data extension and computed fields for intelligent derivation creates a powerful framework for network automation. Organizations can capture their unique network attributes while automatically generating operational intelligence, creating a comprehensive network source of truth that drives automation and operational excellence.

## Conclusion

Nautobot's custom fields and computed fields represent a paradigm shift in network documentation and automation. By providing extensible, declarative mechanisms for data model enhancement, these features enable organizations to build sophisticated network management platforms tailored to their specific requirements.

The OSPF configuration example demonstrates how custom fields can transform a basic network inventory into a comprehensive configuration management system. Combined with computed fields for intelligent data derivation, organizations can create powerful network automation platforms that scale with their infrastructure and operational maturity.

As network automation continues to evolve, the flexibility and extensibility provided by custom fields and computed fields will become increasingly valuable. Organizations that leverage these capabilities effectively will build more robust, maintainable, and intelligent network automation platforms, ultimately achieving greater operational efficiency and reliability.

The key to success lies in thoughtful design, comprehensive validation, and continuous iteration based on operational experience. By following best practices and leveraging Nautobot's extensibility features, network engineers can build powerful, sustainable network automation solutions that grow with their organizations' needs.
