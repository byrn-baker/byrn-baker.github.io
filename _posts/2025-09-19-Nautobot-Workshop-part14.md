---
title: Nautobot Workshop Blog Series - Part 14 - Nautobot Device Lifecycle Management - Part 1
date: 2025-09-12 0:00:00
categories: [Nautobot, Ansible, Automation]
tags: [NetworkAutomation, NetworkSourceOfTruth, nautobot, AutomationPlatform, NautobotTutorials]
image:
  path: /assets/img/nautobot_workshop/light_title_image-50.webp
---

# Nautobot Device Lifecycle Management App: Streamlining Network Asset Management
What happens when you need to track the full lifecycle of your devices from acquisition to end-of-life? That's where the Nautobot Device Lifecycle Management (DLM) app comes in. This app extends Nautobot's capabilities to handle the ongoing management of hardware and software lifecycles, ensuring your network stays compliant, secure, and efficient.

## What is the Nautobot Device Lifecycle Management App?
At its core, the DLM app is an extension for Nautobot designed to manage the lifecycles of network devices, device types, and inventory items. 
It integrates seamlessly with Nautobot's existing data models, allowing you to associate lifecycle information directly with your devices. This means you can capture critical details like end-of-life (EOL) notices, end-of-support dates, and maintenance contracts all in one place. 

The app was developed to address a common pain point in network operations: keeping track of when hardware or software reaches obsolescence, managing vulnerabilities, and ensuring devices are running approved versions. By centralizing this data, it helps organizations plan upgrades, mitigate risks, and optimize resource allocation without jumping between disparate tools or spreadsheets.

### Key Features and What It Does
The DLM app packs a punch with features focused on both hardware and software management. Here's a breakdown:
**Hardware Lifecycle Management**

- **End-of-Life Tracking**: The app allows you to record and report on hardware EOL and end-of-support dates for devices, device types, and inventory items. This helps identify unsupported assets that could pose risks to your network. 
- **Reporting Tools**: Generate reports like the "Device Hardware Notice Report" to quickly see which devices are affected by upcoming lifecycle events, making it easier to prioritize replacements or upgrades.

### Software Lifecycle Management
- **Validated Software Versions**: It supports tracking organizationally approved software versions and validates whether devices or inventory items are running compliant software. Jobs like "Device Software Validation - Report" and "Inventory Item Software Validation - Report" produce detailed outputs, including CSV exports for further analysis. 
- **CVE Discovery and Vulnerability Management**: One standout feature is the automated discovery of Common Vulnerabilities and Exposures (CVEs) via integration with the NIST National Vulnerability Database (NVD) API. You set up an API key, run the "NIST - Software CVE Search" job, and the app maps vulnerabilities to affected software and devices. This is crucial for security-conscious teams, as it automates what could otherwise be a manual, error-prone process. 
- **Software Image and Version Handling**: While earlier versions had custom models for software images and versions, recent updates have migrated these to Nautobot's core models (like SoftwareVersion and SoftwareImageFile) for better integration.

### Contract and Support Management
- **Maintenance Contracts**: Associate contracts with devices and inventory items, then use the app's reporting to monitor coverage. This includes linking contacts (now using Nautobot's core Contact model) for vendor support. 

### User Interface and Automation
- **Visual Dashboards**: List views for hardware and software notices with advanced filtering, plus detail views that link back to affected devices.
- **Jobs and Integrations**: Beyond reports, jobs like "Generate Vulnerabilities" help map CVEs to your infrastructure. The app also supports custom relationships, such as linking software to devices or CVEs to software. 

In essence, the app automates the ingestion of vendor notices, standards updates, and vulnerability data, turning raw information into actionable insights for decision-making.

### How It Integrates with Nautobot
The DLM app doesn't operate in isolation—it builds on Nautobot's foundation. It introduces models and relationships that tie lifecycle data to core entities like Devices, DeviceTypes, and InventoryItems. 

For instance, you can define validated software for specific device types and run validation jobs to check compliance across your fleet. 
Setup is straightforward: Install the app via GitHub (it's open-source and hosted at nautobot/nautobot-app-device-lifecycle-mgmt), configure integrations like the NIST API, and start running jobs. 

It's particularly useful for organizations managing large-scale networks where manual tracking is impractical.

## Creating a Nautobot Job to manage vendor specific CVEs
To avoid redundancy, we will focus on dynamic software discovery from live devices and fetching additional CVEs from Cisco PSIRT and Arista security advisories—sources that might include vendor-exclusive details missing from NIST. This data is then tracked in DLM for unified reporting.

### Updating Nautobot Docker to include the nautobot-device-lifecycle-mgmt app
To add the Nautobot Device Lifecycle Management app (package name: nautobot-device-lifecycle-mgmt) to your project using Poetry, which will update the [tool.poetry.dependencies] section in your pyproject.toml file, run the following command in your project's root directory (where pyproject.toml is located):

```bash
$ poetry add nautobot-device-lifecycle-mgmt
$ poetry add beautifulsoup4
```

This command automatically installs the latest version of the package, adds it as a dependency in pyproject.toml, and updates poetry.lock for reproducibility. If you need a specific version (e.g., for compatibility with your Nautobot version), specify it like this:

```bash
poetry add nautobot-device-lifecycle-mgmt@^3.0.0
```

> Replace ^3.0.0 with the desired version constraint; check the PyPI page for available versions.
{: .prompt-tip }

Rebuild the container to include this new app.

```bash
$ invoke build
```

After adding the dependency, you must also enable the plugin in your Nautobot configuration. Edit nautobot_config.py (typically in your Nautobot project root) to include it in the PLUGINS list:

```python
# Enable installed plugins. Add the name of each plugin to the list.
# PLUGINS = ["nautobot_example_plugin"]
PLUGINS = [
    "nautobot_plugin_nornir", 
    "nautobot_bgp_models", 
    "nautobot_golden_config",
    "nautobot_design_builder",
    "nautobot_device_lifecycle_mgmt",
    ]
```

Optionally, add any plugin-specific configurations under PLUGINS_CONFIG (as per the official docs):

```python
# Plugins configuration settings. These settings are used by various plugins that the user may have installed.
# Each key in the dictionary is the name of an installed plugin and its value is a dictionary of settings.
PLUGINS_CONFIG = {
    "nautobot_plugin_nornir": {
        "use_config_context": {"secrets": False, "connection_options": True},
        # Optionally set global connection options.
        "connection_options": {
            "napalm": {
                "extras": {
                    "optional_args": {"global_delay_factor": 1},
                },
            },
            "netmiko": {
                "extras": {
                    "global_delay_factor": 1,
                },
            },
        },
        "nornir_settings": {
            "credentials": "nautobot_plugin_nornir.plugins.credentials.nautobot_secrets.CredentialsNautobotSecrets",
            "runner": {
                "plugin": "threaded",
                "options": {
                    "num_workers": 20,
                },
            },
        },
        "nautobot_golden_config": {
            "per_feature_bar_width": 0.15,
            "per_feature_width": 13,
            "per_feature_height": 4,
            "enable_backup": True,
            "enable_compliance": True,
            "enable_intended": True,
            "enable_sotagg": True,
            "enable_plan": True,
            "enable_deploy": True,
            "enable_postprocessing": False,
            "sot_agg_transposer": None,
            "postprocessing_callables": [],
            "postprocessing_subscribed": [],
            "jinja_env": {
                "undefined": "jinja2.StrictUndefined",
                "trim_blocks": True,
                "lstrip_blocks": False,
            },
            # "default_deploy_status": "Not Approved",
            # "get_custom_compliance": "my.custom_compliance.func"
        },
    },
    "nautobot_golden_config": {
        "per_feature_bar_width": 0.15,
        "per_feature_width": 13,
        "per_feature_height": 4,
        "enable_backup": True,
        "enable_compliance": True,
        "enable_intended": True,
        "enable_sotagg": True,
        "enable_plan": True,
        "enable_deploy": True,
        "enable_postprocessing": True,
        "sot_agg_transposer": None,
        "postprocessing_callables": ['nautobot_golden_config.utilities.config_postprocessing.render_secrets'],
        "postprocessing_subscribed": [],
        "jinja_env": {
            "undefined": "jinja2.StrictUndefined",
            "trim_blocks": True,
            "lstrip_blocks": False,
        },
        # "default_deploy_status": "Not Approved",
        # "get_custom_compliance": "my.custom_compliance.func"
    },
    "nautobot_device_lifecycle_mgmt": {
        "barchart_bar_width": float(os.environ.get("BARCHART_BAR_WIDTH", 0.1)),
        "barchart_width": int(os.environ.get("BARCHART_WIDTH", 12)),
        "barchart_height": int(os.environ.get("BARCHART_HEIGHT", 5)),
        "enabled_metrics": [x for x in os.environ.get("NAUTOBOT_DLM_ENABLED_METRICS", "").split(",") if x],
    },
}
```

Finally start up the contianer

```bash
$ invoke debug
```

### Objectives for our Vendor CVE Discovery Job
The primary goal of this custom Nautobot job is to automate the discovery and management of security vulnerabilities (CVEs) and lifecycle information for network devices, specifically targeting Cisco and Arista platforms. By integrating with Nautobot's Device Lifecycle Management (DLM) app, it ensures that vulnerability data is centralized, up-to-date, and actionable within the Nautobot ecosystem. This helps network operators identify risks, plan patches or upgrades, and maintain compliance without manual intervention.

**Key Objectives:**
- **Software Version Discovery**: Automatically detect running software versions on selected devices using NAPALM, normalizing them for consistency.
- **CVE Fetching and Persistence**: Retrieve vendor-specific security advisories (CVEs) from Cisco PSIRT API and Arista's website (primary focus on Cisco for this post), then create or update corresponding records in DLM models (CVELCM and VulnerabilityLCM).
- **Affected Software Association**: Link discovered vulnerabilities to the specific software versions, enabling targeted reporting and remediation.
- **Hardware Lifecycle Updates (Optional)**: Fetch Cisco End-of-Life/End-of-Support (EoX) data for device types and populate HardwareLCM models to track obsolescence.
- **Dry-Run Support**: Allow previewing changes without modifying the database, aiding in testing and validation.
- **Compatibility with DLM Versions**: Dynamically handle variations in DLM model structures (e.g., SoftwareLCM vs. other models like SoftwareImageLCM) to support different app versions, - primarily targeting v2.x but with adaptability.
- **Logging and Error Handling**: Provide detailed logs for troubleshooting, warnings for unsupported platforms or missing credentials, and graceful failure for individual devices.

Overall, the job reduces manual effort in vulnerability management, enhances security posture, and integrates vendor data directly into Nautobot for a single source of truth.

### Building the code
#### Imports

```python
import os
import re
import requests
from datetime import date, datetime
from types import SimpleNamespace

from bs4 import BeautifulSoup

from nautobot.apps.jobs import Job, MultiObjectVar, ObjectVar, DryRunVar, BooleanVar, register_jobs
from nautobot.dcim.models import Device, Platform
from nautobot.extras.models import Status, SecretsGroup
from nautobot.extras.choices import (
    SecretsGroupAccessTypeChoices,
    SecretsGroupSecretTypeChoices,
)

from nautobot_device_lifecycle_mgmt.models import (
    SoftwareLCM,
    CVELCM,
    VulnerabilityLCM,
    HardwareLCM
)

from napalm import get_network_driver


class VendorCVEDiscoveryJob(Job):
    """Discover software via NAPALM, fetch vendor CVEs, and update DLM models."""

    devices = MultiObjectVar(
        model=Device,
        required=False,
        description="Select devices to process (optional). If empty, the job will process all Active devices.",
    )

    secrets_group = ObjectVar(
        model=SecretsGroup,
        required=True,
        description="Secrets Group providing device credentials. Associations for username and password are recommended.",
    )

    dry_run = DryRunVar(
        description="Enable dry run mode to preview changes without committing them."
    )

    include_hardware_notices = BooleanVar(
        description="Pull Cisco EoX (End-of-Sale/Support/Software/Security) and update HardwareLCM for device types.",
        default=False,
        required=False,
    )

    class Meta:
        name = "Vendor CVE Discovery (NAPALM)"
        description = "Discover software, fetch CVEs (Cisco/Arista), and optionally EoX hardware notices; update DLM models"
        read_only = False
        field_order = ("devices", "secrets_group", "include_hardware_notices", "dry_run")
```

We will import several libraries for this job that will primarily be used to normalize the data we are attempting to capture. Our Job meta data and inputs will be used to target the devices we want to pull the CVEs for and pull device credentials available to Nautobot.

### Helpers
```python
# ---------------------
    # Secrets helpers
    # ---------------------
    @staticmethod
    def _choice_value(choices_cls, candidate_attrs, default_value):
        for attr in candidate_attrs:
            if hasattr(choices_cls, attr):
                return getattr(choices_cls, attr)
        return default_value

    def _fetch_from_assoc(self, group: SecretsGroup, assoc) -> str | None:
        access_type = getattr(assoc, "access_type", None) or self._choice_value(
            SecretsGroupAccessTypeChoices, ["TYPE_GENERIC"], "generic"
        )
        secret_type = getattr(assoc, "secret_type", None)
        name = getattr(assoc, "name", None)
        if name and secret_type:
            try:
                return group.get_secret_value(
                    access_type=access_type,
                    secret_type=secret_type,
                    secret_name=name,
                )
            except Exception:
                pass
        if hasattr(assoc, "get_secret_value"):
            try:
                return assoc.get_secret_value()
            except Exception:
                pass
        if hasattr(assoc, "get_value"):
            try:
                return assoc.get_value()
            except Exception:
                pass
        return None

    def _get_secret_from_group(self, group: SecretsGroup, secret_type, obj=None) -> str | None:
        # Try SSH first, then Generic, in case your Secrets Group uses SSH scoping
        access_type_candidates = []
        for attr in ("TYPE_SSH", "TYPE_GENERIC"):
            access_type_candidates.append(
                getattr(SecretsGroupAccessTypeChoices, attr, attr.split("_", 1)[1].lower())
            )
        for access_type in access_type_candidates:
            try:
                val = group.get_secret_value(
                    access_type=access_type,
                    secret_type=secret_type,
                    obj=obj,  # pass the device if available; many backends don't need it, but it's safe
                )
                if val:
                    return val
            except Exception:
                # Try the next access_type
                continue
        return None

    def _get_username_from_group(self, group: SecretsGroup, obj=None) -> str | None:
        secret_type = getattr(SecretsGroupSecretTypeChoices, "TYPE_USERNAME", "username")
        return self._get_secret_from_group(group, secret_type, obj=obj) or os.getenv("NAPALM_USERNAME")

    def _get_password_from_group(self, group: SecretsGroup, obj=None) -> str | None:
        secret_type = getattr(SecretsGroupSecretTypeChoices, "TYPE_PASSWORD", "password")
        return self._get_secret_from_group(group, secret_type, obj=obj) or os.getenv("NAPALM_PASSWORD")

    def _get_net_credentials(self, group: SecretsGroup, obj=None) -> tuple[str | None, str | None]:
        username = self._get_username_from_group(group, obj=obj)
        password = self._get_password_from_group(group, obj=obj)
        if not username or not password:
            self.logger.warning(
                f"Missing device credentials from Secrets Group '{getattr(group, 'name', group)}'. "
                "Ensure it has associations for username and password, or set NAPALM_USERNAME/NAPALM_PASSWORD."
            )
        return username, password

    def _get_cisco_credentials(self) -> tuple[str | None, str | None]:
        return os.getenv("CISCO_CLIENT_ID"), os.getenv("CISCO_CLIENT_SECRET")
```

In Nautobot, sensitive credentials like usernames, passwords, API keys, or tokens are managed through the SecretsGroup model, which aggregates multiple Secret objects. Each Secret defines how to retrieve a value from a backend provider (e.g., environment variables, HashiCorp Vault, AWS Secrets Manager, or custom plugins). This abstraction ensures secrets are not stored in plain text in the database but fetched dynamically when needed. 

The helpers in this section are essential for the following reasons:
- **Flexibility in Secrets Configuration**: Users can configure SecretsGroup in various ways. Secrets might be associated by access_type (e.g., TYPE_SSH for network device access via SSH, or TYPE_GENERIC for general use) and secret_type (e.g., TYPE_USERNAME or TYPE_PASSWORD). The code doesn't assume a fixed setup; instead, it tries common configurations to maximize compatibility. For example, device credentials for NAPALM (used for software discovery on Cisco/Arista devices) might be scoped under SSH for security reasons, but could fall back to Generic.
- **Error Resilience and Fallbacks**: Not all SecretsGroup instances will have secrets defined the same way. If a secret isn't found via the primary method, the helpers fall back to environment variables (e.g., NAPALM_USERNAME or NAPALM_PASSWORD). This allows the job to run in simpler environments without a fully configured SecretsGroup, or during testing/debugging.
- **Dynamic Retrieval with Context**: Nautobot's get_secret_value method can optionally take an obj parameter (e.g., a Device instance) for providers that support per-object secrets (like device-specific credentials). The helpers incorporate this to handle such cases.
- **Abstraction for Different Credential Types**: The job needs two main credential sets:
  - Network device credentials (username/password) for NAPALM connections.
  - Cisco API credentials (client ID/secret) for PSIRT and EoX APIs.

These are handled differently: device creds via SecretsGroup (potentially device-specific), API creds via env vars (global and not device-tied).

Without these helpers, the code would be brittle, hardcoding assumptions about access_type or secret_type could fail if the SecretsGroup is configured differently. They promote reusability, 

> - The @staticmethod decorator in Python is used to define a static method within a class. A static method is a method that belongs to the class rather than to any specific instance of the class. It can be called directly on the class itself (e.g., ClassName.method()) or on an instance (e.g., instance.method()), but unlike regular instance methods, it does not receive an implicit first argument like self (for instances) or cls (for class methods). This makes it ideal for utility functions that are logically related to the class but do not need to access or modify class or instance state. 
> - Use @staticmethod when you want to encapsulate a function within a class for organizational reasons but don't need it to interact with class or instance attributes.
{: .prompt-tip }

### Using Nautobots NBSHELL
This allows you to interact with Nautobot models directly in a Python environment. 

Open a command prompt into your nautobot container

```bash
nautobot@1fbba40e0775:~$ nautobot-server nbshell
/usr/local/lib/python3.12/site-packages/pycountry/__init__.py:10: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
  import pkg_resources
20:50:47.882 WARNING nautobot.core.api.routers routers.py                   get_api_root_view() :
  Something has changed an OrderedDefaultRouter's APIRootView attribute to a custom class. Please verify that class GoldenConfigRootView implements appropriate authentication controls.
# Shell Plus Model Imports
from constance.models import Constance
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session
from django_celery_beat.models import ClockedSchedule, CrontabSchedule, IntervalSchedule, PeriodicTask, PeriodicTasks, SolarSchedule
from django_celery_results.models import ChordCounter, GroupResult, TaskResult
from nautobot.circuits.models import Circuit, CircuitTermination, CircuitType, Provider, ProviderNetwork
from nautobot.cloud.models import CloudAccount, CloudNetwork, CloudNetworkPrefixAssignment, CloudResourceType, CloudService, CloudServiceNetworkAssignment
from nautobot.dcim.models.cables import Cable, CablePath
from nautobot.dcim.models.device_component_templates import ConsolePortTemplate, ConsoleServerPortTemplate, DeviceBayTemplate, FrontPortTemplate, InterfaceTemplate, ModuleBayTemplate, PowerOutletTemplate, PowerPortTemplate, RearPortTemplate
from nautobot.dcim.models.device_components import ConsolePort, ConsoleServerPort, DeviceBay, FrontPort, Interface, InterfaceRedundancyGroup, InterfaceRedundancyGroupAssociation, InventoryItem, ModuleBay, PowerOutlet, PowerPort, RearPort
from nautobot.dcim.models.devices import Controller, ControllerManagedDeviceGroup, Device, DeviceFamily, DeviceRedundancyGroup, DeviceType, DeviceTypeToSoftwareImageFile, InterfaceVDCAssignment, Manufacturer, Module, ModuleType, Platform, SoftwareImageFile, SoftwareVersion, VirtualChassis, VirtualDeviceContext
from nautobot.dcim.models.locations import Location, LocationType
from nautobot.dcim.models.power import PowerFeed, PowerPanel
from nautobot.dcim.models.racks import Rack, RackGroup, RackReservation
from nautobot.extras.models.change_logging import ObjectChange
from nautobot.extras.models.contacts import Contact, ContactAssociation, Team
from nautobot.extras.models.customfields import ComputedField, CustomField, CustomFieldChoice
from nautobot.extras.models.datasources import GitRepository
from nautobot.extras.models.groups import DynamicGroup, DynamicGroupMembership, StaticGroupAssociation
from nautobot.extras.models.jobs import Job, JobButton, JobHook, JobLogEntry, JobQueue, JobQueueAssignment, JobResult, ScheduledJob, ScheduledJobs
from nautobot.extras.models.metadata import MetadataChoice, MetadataType, ObjectMetadata
from nautobot.extras.models.models import ConfigContext, ConfigContextSchema, CustomLink, ExportTemplate, ExternalIntegration, FileAttachment, FileProxy, GraphQLQuery, HealthCheckTestModel, ImageAttachment, Note, SavedView, UserSavedViewAssociation, Webhook
from nautobot.extras.models.relationships import Relationship, RelationshipAssociation
from nautobot.extras.models.roles import Role
from nautobot.extras.models.secrets import Secret, SecretsGroup, SecretsGroupAssociation
from nautobot.extras.models.statuses import Status
from nautobot.extras.models.tags import Tag, TaggedItem
from nautobot.ipam.models import IPAddress, IPAddressToInterface, Namespace, Prefix, PrefixLocationAssignment, RIR, RouteTarget, Service, VLAN, VLANGroup, VLANLocationAssignment, VRF, VRFDeviceAssignment, VRFPrefixAssignment
from nautobot.tenancy.models import Tenant, TenantGroup
from nautobot.users.models import AdminGroup, ObjectPermission, Token, User
from nautobot.virtualization.models import Cluster, ClusterGroup, ClusterType, VMInterface, VirtualMachine
from nautobot.wireless.models import ControllerManagedDeviceGroupRadioProfileAssignment, ControllerManagedDeviceGroupWirelessNetworkAssignment, RadioProfile, SupportedDataRate, WirelessNetwork
from nautobot_bgp_models.models import AddressFamily, AutonomousSystem, AutonomousSystemRange, BGPRoutingInstance, PeerEndpoint, PeerEndpointAddressFamily, PeerGroup, PeerGroupAddressFamily, PeerGroupTemplate, Peering
from nautobot_design_builder.models import ChangeRecord, ChangeSet, Deployment, Design
from nautobot_device_lifecycle_mgmt.models import CVELCM, ContactLCM, ContractLCM, DeviceHardwareNoticeResult, DeviceSoftwareValidationResult, HardwareLCM, InventoryItemSoftwareValidationResult, ProviderLCM, SoftwareImageLCM, SoftwareLCM, ValidatedSoftwareLCM, VulnerabilityLCM
from nautobot_golden_config.models import ComplianceFeature, ComplianceRule, ConfigCompliance, ConfigPlan, ConfigRemove, ConfigReplace, GoldenConfig, GoldenConfigSetting, RemediationSetting
from nautobot_ssot.integrations.infoblox.models import SSOTInfobloxConfig
from nautobot_ssot.integrations.itential.models import AutomationGatewayModel
from nautobot_ssot.integrations.servicenow.models import SSOTServiceNowConfig
from nautobot_ssot.models import SSOTConfig, Sync, SyncLogEntry
from silk.models import Profile, Request, Response, SQLQuery
from social_django.models import Association, Code, Nonce, Partial, UserSocialAuth
# Shell Plus Django Imports
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Avg, Case, Count, F, Max, Min, Prefetch, Q, Sum, When
from django.utils import timezone
from django.urls import reverse
from django.db.models import Exists, OuterRef, Subquery
# Django version 4.2.24
# Nautobot version 2.4.10
# Nautobot Plugin for Nornir version 2.2.1
# BGP Models version 2.3.2
# Golden Configuration version 2.5.0
# Nautobot Design Builder version 2.2.0
# Nautobot Device Lifecycle Management version 3.1.1
# Single Source of Truth version 3.9.4
# Device Onboarding version 4.3.1
Python 3.12.11 (main, Jun  4 2025, 17:15:26) [GCC 12.2.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)
>>> 
```

In the nbhshell we can retrieve the secrets group, then get the username and password from within that group

```bash
>>> from nautobot.extras.models import SecretsGroup
>>> from nautobot.extras.choices import SecretsGroupAccessTypeChoices, SecretsGroupSecretTypeChoices
>>> group = SecretsGroup.objects.get(name="cisco-credentials")
>>> group
<SecretsGroup: cisco-credentials>
```

This gives us access to its methods and related objects. Use dir(group) to list available methods, revealing get_secret_value among them. 

```bash
>>> dir(group)
['DoesNotExist', 'Meta', 'MultipleObjectsReturned', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getstate__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__setstate__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_check_column_name_clashes', '_check_constraints', '_check_db_table_comment', '_check_default_pk', '_check_field_name_clashes', '_check_fields', '_check_id_field', '_check_index_together', '_check_indexes', '_check_local_fields', '_check_long_column_names', '_check_m2m_through_same_relationship', '_check_managers', '_check_model', '_check_model_name_db_lookup_clashes', '_check_ordering', '_check_property_name_related_field_accessor_clashes', '_check_single_primary_key', '_check_swappable', '_check_unique_together', '_content_type', '_content_type_cache_key', '_content_type_cached', '_custom_field_data', '_do_insert', '_do_update', '_generate_field_lookups_from_natural_key_field_names', '_get_FIELD_display', '_get_expr_references', '_get_field_value_map', '_get_next_or_previous_by_FIELD', '_get_next_or_previous_in_order', '_get_pk_val', '_get_unique_checks', '_meta', '_perform_date_checks', '_perform_unique_checks', '_prepare_related_fields_for_save', '_save_parents', '_save_table', '_set_pk_val', '_state', 'adelete', 'arefresh_from_db', 'asave', 'associated_contacts', 'associated_object_metadata', 'associations', 'cf', 'check', 'clean', 'clean_fields', 'cloudaccount_set', 'composite_key', 'created', 'csv_natural_key_field_lookups', 'custom_field_data', 'date_error_message', 'delete', 'description', 'destination_for_associations', 'device_redundancy_groups', 'devices', 'documentation_static_path', 'dynamic_groups', 'dynamic_groups_cached', 'dynamic_groups_list', 'dynamic_groups_list_cached', 'externalintegration_set', 'from_db', 'full_clean', 'get_absolute_url', 'get_changelog_url', 'get_computed_field', 'get_computed_fields', 'get_computed_fields_grouping', 'get_computed_fields_grouping_advanced', 'get_computed_fields_grouping_basic', 'get_constraints', 'get_custom_field_groupings', 'get_custom_field_groupings_advanced', 'get_custom_field_groupings_basic', 'get_custom_fields', 'get_custom_fields_advanced', 'get_custom_fields_basic', 'get_deferred_fields', 'get_dynamic_groups_url', 'get_notes_url', 'get_relationships', 'get_relationships_data', 'get_relationships_data_advanced_fields', 'get_relationships_data_basic_fields', 'get_relationships_with_related_objects', 'get_secret_value', 'git_repositories', 'has_computed_fields', 'has_computed_fields_advanced', 'has_computed_fields_basic', 'id', 'interfaceredundancygroup_set', 'is_cloud_resource_type_model', 'is_contact_associable_model', 'is_dynamic_group_associable_model', 'is_metadata_associable_model', 'is_saved_view_model', 'last_updated', 'name', 'natural_key', 'natural_key_args_to_kwargs', 'natural_key_field_lookups', 'natural_slug', 'notes', 'objects', 'pk', 'prepare_database_save', 'present_in_database', 'refresh_from_db', 'required_related_objects_errors', 'save', 'save_base', 'secrets', 'secrets_group_associations', 'serializable_value', 'source_for_associations', 'ssotservicenowconfig_set', 'static_group_association_set', 'to_objectchange', 'unique_error_message', 'validate_constraints', 'validate_unique', 'validated_save', 'wireless_networks']
```

Then we can use help
```bash
>>> help(group.get_secret_value)
Help on method get_secret_value in module nautobot.extras.models.secrets:

get_secret_value(access_type, secret_type, obj=None, **kwargs) method of nautobot.extras.models.secrets.SecretsGroup instance
    Helper method to retrieve a specific secret from this group.

    May raise SecretError and/or Django ObjectDoesNotExist exceptions; it's up to the caller to handle those.
```

You can introspect the Django model field choices
```bash
>>> SecretsGroupAssociation._meta.get_field("access_type").choices
<class 'nautobot.extras.choices.SecretsGroupAccessTypeChoices'>
>>> SecretsGroupAssociation._meta.get_field("secret_type").choices
<class 'nautobot.extras.choices.SecretsGroupSecretTypeChoices'>
>>> [v for v, _ in SecretsGroupAssociation._meta.get_field("access_type").choices]
['Generic', 'Console', 'gNMI', 'HTTP(S)', 'NETCONF', 'REST', 'RESTCONF', 'SNMP', 'SSH']
>>> [v for v, _ in SecretsGroupAssociation._meta.get_field("secret_type").choices]
['key', 'password', 'secret', 'token', 'username', 'url', 'notes']
>>> for name in ("access_type", "secret_type"):
...     print(f"{name}:")
...     for value, label in SecretsGroupAssociation._meta.get_field(name).choices:
...         print(f"  {value}  # {label}")
... 
access_type:
  Generic  # Generic
  Console  # Console
  gNMI  # gNMI
  HTTP(S)  # HTTP(S)
  NETCONF  # NETCONF
  REST  # REST
  RESTCONF  # RESTCONF
  SNMP  # SNMP
  SSH  # SSH
secret_type:
  key  # Key
  password  # Password
  secret  # Secret
  token  # Token
  username  # Username
  url  # URL
  notes  # Notes
```

Finally we can fetch the value of the correct keys for username and password.
```bash
>>> username = group.get_secret_value(access_type=SecretsGroupAccessTypeChoices.TYPE_GENERIC,secret_type=SecretsGroupSecretTypeChoices.TYPE_USERNAME)
>>> username
'cisco'
>>> 
>>> 
>>> password = group.get_secret_value(access_type=SecretsGroupAccessTypeChoices.TYPE_GENERIC,secret_type=SecretsGroupSecretTypeChoices.TYPE_PASSWORD)
>>> password
'cisco'
>>> 
>>> 
>>> print(username,password)
cisco cisco
>>>
```

- **Imports:** Load the necessary models and choice classes. SecretsGroup is the model for grouped secrets, and the choices define enums for access_type (e.g., TYPE_GENERIC for general use, or TYPE_NETCONF/TYPE_SSH for specific protocols) and secret_type (e.g., TYPE_USERNAME, TYPE_PASSWORD).
- **Retrieval**: Use SecretsGroup.objects.get() to fetch the group. Then, call get_secret_value() on it, specifying the access_type and secret_type to identify which secret to fetch. This method dynamically resolves the value from the backend provider (e.g., env vars, Vault) without storing it in the database.
- **Error Handling**: If the secret can't be retrieved (e.g., missing association or provider error), it raises a SecretError. In practice, wrap in try/except.
Best Practices: Don't hardcode or log secrets. Use specific access_type if your group is configured for protocols like SSH or REST (e.g., TYPE_SSH for network device access). 

# Conclusion
In the next post we will continue building out the code needed to accomplish our objectives. We will delve into more functions and helpers that will be used to normalize our data, and import that data into Nautobots DLM App. 