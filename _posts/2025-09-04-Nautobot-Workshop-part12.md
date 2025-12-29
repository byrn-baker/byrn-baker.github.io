---
title: Nautobot Workshop Blog Series - Part 12 - From L3 Links to IGP Loopbacks
date: 2025-09-04 8:00:00
categories: [Nautobot, Ansible, Automation]
tags: [NetworkAutomation, NetworkSourceOfTruth, nautobot, AutomationPlatform, NautobotTutorials]
lab_vps_banner: true
image:
  path: /assets/img/nautobot_workshop/light_title_image-50.webp
---

# Using Nautobot Jobs for Data Validation
In my previous blog post, [Nautobot Jobs - Creating validation jobs](https://blog.byrnbaker.me/posts/Nautobot-Workshop-part11/), we explored how to automate ping tests between directly connected router interfaces to confirm Layer 3 adjacencies. This foundational validation ensures that point-to-point links are properly configured and operational, a critical first step in building a reliable network. But as networks scale, especially in workshop environments like mine that rely on OSPF as the Interior Gateway Protocol (IGP), with BGP peering over loopbacks and MPLS for traffic engineering, we need to extend the checks deeper into the routing domain. 

Today, we're naturally progressing from those L3 link validations to verifying IGP provider loopbacks. Why? In an OSPF-based design, loopbacks serve as stable router IDs and peering endpoints for BGP sessions. They also underpin MPLS label distribution (e.g., via LDP or SR-MPLS). If loopbacks aren't advertised via OSPF or reachable end-to-end, higher-layer services like BGP and MPLS will fail. This new job, IGP Provider Loopback Validation, builds directly on the L3 ping concept but shifts focus to multi-hop reachability, confirming OSPF route presence and ping success from source loopbacks to provider loopbacks. We'll also enhance the Nautobot UI with a custom results tab for better visualization, making it easier to spot issues in large topologies.

This post dives into the Python code (`igploopback_validation.py`) and HTML templates (`customized_jobresult.html`, `igp_validation_form.html`), explaining what each part does and why it’s designed that way. The focus is on clarity, ensuring you understand the job’s logic and UI customization for validating OSPF in a BGP/MPLS-ready network.

## Using Nornir + NautobotInventory for Route Validation

Before diving into the full `IGPProviderLoopbackValidation` job, it helps to see how **Nornir** works with Nautobot’s inventory and NAPALM. This standalone script shows the core workflow:  

1. **Pull inventory directly from Nautobot** (via the `NautobotInventory` plugin).  
2. **Normalize platforms** to use the correct NAPALM driver (so iOS vs EOS works without manual tweaks).  
3. **Run validation tasks** using Nornir/NAPALM (`napalm_get` and `napalm_cli`).  
4. **Display results** in a consistent format with `print_result`.  

This is essentially the same pattern the Nautobot Job builds on, just stripped down to focus on OSPF route checks.  

```python
import logging
import os
from nornir import InitNornir
from nornir.core.inventory import ConnectionOptions
from nornir_napalm.plugins.tasks import napalm_cli, napalm_get
from nornir_utils.plugins.functions import print_result

LOGGER = logging.getLogger(__name__)

def initialize():
    nr = InitNornir(
        inventory={
            "plugin": "NautobotInventory",
            "options": {
                "nautobot_url": "http://localhost:8080/",
                "nautobot_token": "0123456789abcdef0123456789abcdef01234567",
                "filter_parameters": {"role": "Provider Router"},
                "ssl_verify": False,
            },
        },
    )

    nr.inventory.defaults.username = os.getenv("NORNIR_USERNAME")
    nr.inventory.defaults.password = os.getenv("NORNIR_PASSWORD")

    for name, host in nr.inventory.hosts.items():
        nb_obj = host.data.get("pynautobot_object")
        platform = nb_obj.platform if nb_obj else None
        napalm_driver = getattr(platform, "napalm_driver", None)

        if napalm_driver:
            print(f"[INFO] Setting NAPALM driver for {name}: {napalm_driver}")
            host.platform = napalm_driver

            params = host.get_connection_parameters("napalm")
            extras = dict(params.extras or {})
            extras = {"optional_args": extras.get("optional_args", {})}
            host.connection_options["napalm"] = ConnectionOptions(
                hostname=params.hostname,
                port=params.port,
                username=params.username,
                password=params.password,
                platform=napalm_driver,
                extras=extras,
            )
        else:
            print(f"[ERROR] {name}: Nautobot Platform.napalm_driver is not set or invalid")

    print(f"Total hosts loaded: {len(nr.inventory.hosts)}")
    for h in nr.inventory.hosts.values():
        plat = h.data.get("pynautobot_object").platform if h.data.get("pynautobot_object") else None
        print(
            f"- {h.name}: platform_name={getattr(plat, 'name', None)}, "
            f"network_driver={getattr(plat, 'network_driver', None)}, "
            f"napalm_driver={h.platform}, "
            f"conn.platform={h.get_connection_parameters('napalm').platform}"
        )

    return nr

def show_ospf_routes_cli(task):
    """
    Show OSPF routes via CLI command, chosen per NAPALM driver.
    Uses napalm_cli directly instead of dispatcher.
    """
    drv = (task.host.platform or "").lower()

    if drv in ("ios", "eos"):
        cmd = "show ip route ospf"

    return task.run(
        task=napalm_cli,
        commands=[cmd],
    )

def show_ospf_routes_parsed(task, destination):
    r = task.run(
        task=napalm_get,
        getters=["get_route_to"],
        getters_options={"get_route_to": {"destination": destination}},
    )
    routes = r.result.get("get_route_to")

    if isinstance(routes, str):
        return f"napalm_get(get_route_to) returned: {routes}"

    ospf_only = {}
    for prefix, entries in routes.items():
        for e in entries:
            proto = (e.get("protocol") or e.get("protocols") or "").lower()
            if "ospf" in proto:
                ospf_only.setdefault(prefix, []).append(e)

    return ospf_only or f"No OSPF routes found for {destination}"

def main():
    if os.getenv("NAUTOBOT_TOKEN"):
        print("Nautobot API Token is set.")
    else:
        print("Nautobot API Token is not set. Set NAUTOBOT_TOKEN.")

    nr = initialize()
    if not nr.inventory.hosts:
        print("No hosts loaded from Nautobot.")
        return

    # print("Showing OSPF routes (CLI)...")
    # res_cli = nr.run(task=show_ospf_routes_cli)
    # print_result(res_cli)
    
    print("Showing OSPF routes (NAPALM getter)...")
    res_parsed = nr.run(task=show_ospf_routes_parsed, destination="100.0.254.5/32")
    print_result(res_parsed)

if __name__ == "__main__":
    main()
```
You can also look at the code [HERE](https://github.com/byrn-baker/nornir-example)

Running this script will:

- Pull your provider routers from Nautobot.
- Normalize their NAPALM driver settings.
- Ask each one: “Do you have an OSPF route to 100.0.254.5/32?”
- Print a parsed result table showing which devices succeed or fail.

> TIP: Using the Napalm Driver
> I found it defaulted to the network_driver so this needed to be overriden.
> This was not an issue in the nautobot job.
{: .prompt-tip }

This small example shows the core pattern that my full Nautobot Job builds on. The job then scales this pattern into structured tests (multiple prefixes, cross-device validation, IPv6 support, ping checks, and UI-friendly results).

**Example Output**
```bash
$ python nornir_example.py 
Nautobot API Token is set.
[INFO] Setting NAPALM driver for P1: ios
[INFO] Setting NAPALM driver for P2: ios
[INFO] Setting NAPALM driver for P3: ios
[INFO] Setting NAPALM driver for P4: ios
Total hosts loaded: 4
- P1: platform_name=IOS, network_driver=cisco_ios, napalm_driver=ios, conn.platform=ios
- P2: platform_name=IOS, network_driver=cisco_ios, napalm_driver=ios, conn.platform=ios
- P3: platform_name=IOS, network_driver=cisco_ios, napalm_driver=ios, conn.platform=ios
- P4: platform_name=IOS, network_driver=cisco_ios, napalm_driver=ios, conn.platform=ios
Showing OSPF routes (NAPALM getter)...
show_ospf_routes_parsed*********************************************************
* P1 ** changed : False ********************************************************
vvvv show_ospf_routes_parsed ** changed : False vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv INFO
{ '100.0.254.5/32': [ { 'age': 864000,
                        'current_active': True,
                        'inactive_reason': '',
                        'last_active': True,
                        'next_hop': '100.0.101.2',
                        'outgoing_interface': 'Ethernet0/3',
                        'preference': 11,
                        'protocol': 'ospf',
                        'protocol_attributes': {},
                        'routing_table': 'default',
                        'selected_next_hop': True}]}
---- napalm_get ** changed : False --------------------------------------------- INFO
{ 'get_route_to': { '100.0.254.5/32': [ { 'age': 864000,
                                          'current_active': True,
                                          'inactive_reason': '',
                                          'last_active': True,
                                          'next_hop': '100.0.101.2',
                                          'outgoing_interface': 'Ethernet0/3',
                                          'preference': 11,
                                          'protocol': 'ospf',
                                          'protocol_attributes': {},
                                          'routing_table': 'default',
                                          'selected_next_hop': True}]}}
^^^^ END show_ospf_routes_parsed ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* P2 ** changed : False ********************************************************
vvvv show_ospf_routes_parsed ** changed : False vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv INFO
{ '100.0.254.5/32': [ { 'age': 864000,
                        'current_active': True,
                        'inactive_reason': '',
                        'last_active': True,
                        'next_hop': '100.0.102.2',
                        'outgoing_interface': 'Ethernet0/3',
                        'preference': 11,
                        'protocol': 'ospf',
                        'protocol_attributes': {},
                        'routing_table': 'default',
                        'selected_next_hop': True}]}
---- napalm_get ** changed : False --------------------------------------------- INFO
{ 'get_route_to': { '100.0.254.5/32': [ { 'age': 864000,
                                          'current_active': True,
                                          'inactive_reason': '',
                                          'last_active': True,
                                          'next_hop': '100.0.102.2',
                                          'outgoing_interface': 'Ethernet0/3',
                                          'preference': 11,
                                          'protocol': 'ospf',
                                          'protocol_attributes': {},
                                          'routing_table': 'default',
                                          'selected_next_hop': True}]}}
^^^^ END show_ospf_routes_parsed ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* P3 ** changed : False ********************************************************
vvvv show_ospf_routes_parsed ** changed : False vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv INFO
{ '100.0.254.5/32': [ { 'age': 864000,
                        'current_active': True,
                        'inactive_reason': '',
                        'last_active': True,
                        'next_hop': '100.0.13.1',
                        'outgoing_interface': 'Ethernet0/2',
                        'preference': 21,
                        'protocol': 'ospf',
                        'protocol_attributes': {},
                        'routing_table': 'default',
                        'selected_next_hop': True}]}
---- napalm_get ** changed : False --------------------------------------------- INFO
{ 'get_route_to': { '100.0.254.5/32': [ { 'age': 864000,
                                          'current_active': True,
                                          'inactive_reason': '',
                                          'last_active': True,
                                          'next_hop': '100.0.13.1',
                                          'outgoing_interface': 'Ethernet0/2',
                                          'preference': 21,
                                          'protocol': 'ospf',
                                          'protocol_attributes': {},
                                          'routing_table': 'default',
                                          'selected_next_hop': True}]}}
^^^^ END show_ospf_routes_parsed ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* P4 ** changed : False ********************************************************
vvvv show_ospf_routes_parsed ** changed : False vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv INFO
{ '100.0.254.5/32': [ { 'age': 864000,
                        'current_active': True,
                        'inactive_reason': '',
                        'last_active': True,
                        'next_hop': '100.0.24.2',
                        'outgoing_interface': 'Ethernet0/2',
                        'preference': 21,
                        'protocol': 'ospf',
                        'protocol_attributes': {},
                        'routing_table': 'default',
                        'selected_next_hop': True}]}
---- napalm_get ** changed : False --------------------------------------------- INFO
{ 'get_route_to': { '100.0.254.5/32': [ { 'age': 864000,
                                          'current_active': True,
                                          'inactive_reason': '',
                                          'last_active': True,
                                          'next_hop': '100.0.24.2',
                                          'outgoing_interface': 'Ethernet0/2',
                                          'preference': 21,
                                          'protocol': 'ospf',
                                          'protocol_attributes': {},
                                          'routing_table': 'default',
                                          'selected_next_hop': True}]}}
^^^^ END show_ospf_routes_parsed ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```


## Why Extend Validation to IGP Loopbacks?
Building on the benefits outlined in the L3 validation automation, validating loopbacks addresses is the next logical layer in network design
- **Multi-hop Assurance**: L3 neighbor pings confirm direct links, but loopbacks test the full IGP convergence, catching issues like OSPF area misconfigurations or route filtering.
- **BGP and MPLS Readiness**: In the OSPF setup, BGP peers over loopbacks. MPLS relies on loopback reachability for label bindings. Validating this early prevents downstream failures.
- **Scalability in Design**: For provider-like environments (e.g., core/edge routers), focus on loopbacks to ensure key nodes are visible network-wide.
- **Enhanced Reporting**: Unlike basic logs, we'll persist structured data for a custom UI tab, allowing tabular reports with summaries, ideal for auditing OSPF health before enabling BGP/MPLS.

Our example job, `IGPProviderLoopbackValidation`, checks if each provider loopback appears in the OSPF table and is pingable from source devices' loopbacks, with IPv6 support and fallbacks for broader compatibility.

## Code Walkthrough
This job:
1. Queries the source and provider devices (scoped by sites/roles).
2. Extracting loopback IPs (IPv4/IPv6) from Nautobot.
3. Building cross-device tests (source loopback to provider loopback).
4. Using NAPALM to verify OSPF routes (with CLI fallback for IPv6) and ping.
5. Aggregating into a structured payload for UI rendering, with pass/fail summaries.

### Imports and Setup
```python
from collections import defaultdict
import re
from nautobot.apps.jobs import Job, register_jobs, BooleanVar, IntegerVar, MultiObjectVar, StringVar
from nautobot.dcim.models import Device, Interface, Location
from nautobot.extras.models import Role
from nornir import InitNornir
from nornir.core.plugins.inventory import InventoryPluginRegister
from nautobot_plugin_nornir.plugins.inventory.nautobot_orm import NautobotORMInventory
from nornir.core.task import Task, Result
from nornir.core.filter import F
from nornir_napalm.plugins.tasks import napalm_ping, napalm_get, napalm_cli

try:
    InventoryPluginRegister.register("nautobot-inventory", NautobotORMInventory)
except Exception:
    pass
```

- **What**: Imports Nautobot job utilities, models (Device, Interface), Nornir for orchestration, and NAPALM for network tasks. Registers the Nautobot ORM inventory plugin.
- **Why**: Nautobot requires specific imports for jobs and database access. Nornir enables parallel device tasks; NAPALM provides vendor-agnostic route/ping operations. The plugin registration links Nornir to Nautobot’s inventory without external APIs, simplifying credential management.

### Job Class and Metadata
```python
class IGPProviderLoopbackValidation(Job):
    """
    Validate IGP by:
      1) Ensuring each selected 'provider' loopback appears in the OSPF routing table.
      2) Pinging each provider loopback from the local device's loopback IP.
    Includes IPv6 CLI fallback for route checks and enhanced logging.
    Returns results under result.result.results.igp_validation for UI.
    """
    class Meta:
        name = "IGP Provider Loopback Validation (Nornir)"
        description = "Verify provider loopbacks are learned via OSPF and reachable from local loopback. Includes IPv6 CLI fallback and table report."
        commit_default = False
```

- **What**: Defines the job with a docstring outlining its two-step validation (route check, ping) and UI output path. Metadata sets the UI name, description, and disables auto-commit.
- **Why**: The docstring clarifies purpose for developers; metadata ensures the job appears correctly in Nautobot’s UI. `commit_default=False` prevents unintended database changes, as this is a read-only validation.

#### Users Inputs
```python
sites = MultiObjectVar(model=Location, ..., label="Limit Source Devices to Sites")
roles = MultiObjectVar(model=Role, ..., label="Limit Source Devices to Roles")
provider_roles = MultiObjectVar(model=Role, ..., label="Provider Device Roles (loopbacks to validate)")
loopback_name = StringVar(default="Loopback0", label="Loopback Interface Name")
ipv6 = BooleanVar(default=False, label="Validate IPv6")
vrf = StringVar(required=False, label="VRF (optional)")
count = IntegerVar(default=3, min_value=1, max_value=20, label="ICMP Count")
timeout = IntegerVar(default=2, min_value=1, max_value=10, label="Per-ping Timeout (seconds)")
skip_ipv6_route_check = BooleanVar(default=False, label="Skip IPv6 Route Validation")
```

- **What**: Defines UI inputs for scoping devices (`sites`, `roles`), targeting provider loopbacks (`provider_roles`), specifying loopback names, enabling IPv6, setting VRFs, configuring ping parameters, and skipping IPv6 route checks.
- **Why**: 
  - Inputs make the job flexible without code changes. `provider_roles` allows targeting key devices (e.g., core routers) for validation. 
  - loopback_name defaults to "Loopback0" for common setups. 
  - ipv6 and vrf support dual-stack and isolated contexts. 
  - `skip_ipv6_route_check` handles NAPALM driver limitations, ensuring job completion even on unsupported platforms.

#### Helper Functions
These extract and prepare data for tests:

```python
def _get_first_ip_on_interface(self, iface: Interface, want_ipv6: bool):
    for ip in iface.ip_addresses.all().order_by("pk"):
        host_ip = ip.address.ip
        if (host_ip.version == 6) == want_ipv6:
            return ip  # return the IPAddress object
    return None

def _get_loopback_ip(self, device: Device, loopback_name: str, want_ipv6: bool):
    iface = device.interfaces.filter(name=loopback_name).prefetch_related("ip_addresses").first()
    if not iface:
        return None
    return self._get_first_ip_on_interface(iface, want_ipv6=want_ipv6)

def _collect_provider_targets(self, devices_qs, loopback_name: str, want_ipv6: bool):
    targets = []
    for dev in devices_qs:
        ip_obj_v4 = self._get_loopback_ip(dev, loopback_name, want_ipv6=False)
        if ip_obj_v4:
            targets.append({
                "dst_dev_name": dev.name,
                "dst_ip_str": str(ip_obj_v4.address.ip),
                "dst_prefix": str(ip_obj_v4.address),
                "family": "IPv4",
            })
        if want_ipv6:
            ip_obj_v6 = self._get_loopback_ip(dev, loopback_name, want_ipv6=True)
            if ip_obj_v6:
                targets.append({
                    "dst_dev_name": dev.name,
                    "dst_ip_str": str(ip_obj_v6.address.ip),
                    "dst_prefix": str(ip_obj_v6.address),
                    "family": "IPv6",
                })
    return targets
```

- **What**: 
  - `_get_first_ip_on_interface` finds the first IPv4 or IPv6 address on an interface. 
  - `_get_loopback_ip` fetches the named loopback interface’s IP. 
  - `_collect_provider_targets` builds a list of target dicts (device name, IP, prefix, family) from provider devices.
- **Why**: These modular functions centralize IP extraction logic, reducing code duplication. Prefetching (`prefetch_related`) optimizes database queries by fetching IPs upfront. The target list ensures only valid loopbacks are tested, supporting both IP families for BGP/MPLS compatibility.

### Main `run` Method
The entry point orchestrates the workflow:

```python
def run(self, *, sites, roles, provider_roles, loopback_name, ipv6, vrf, count, timeout, skip_ipv6_route_check):
    self.logger.info("Starting IGP Provider Loopback Validation.")
    want_ipv6 = bool(ipv6)
    icmp_count = int(count)
    per_ping_timeout = int(timeout)
    vrf_name = (vrf or "").strip() or None
    skip_ipv6_routes = bool(skip_ipv6_route_check)

    # Query devices
    src_devices = Device.objects.filter(status__name="Active")
    if sites:
        src_devices = src_devices.filter(location__in=sites)
    if roles:
        src_devices = src_devices.filter(role__in=roles)
    provider_devices = Device.objects.filter(status__name="Active", role__in=provider_roles) if provider_roles else src_devices
    src_devices = src_devices.prefetch_related("interfaces__ip_addresses", "platform").distinct()
    provider_devices = provider_devices.prefetch_related("interfaces__ip_addresses").distinct()

    # Early exit if no devices
    if not src_devices.exists():
        self.logger.warning("No source devices found for the selected scope.")
        return {"results": {"igp_validation": {"columns": [], "rows": [], "summary": {"total": 0, "passes": 0, "fails": 0}}}}

    # Collect targets
    provider_targets = self._collect_provider_targets(provider_devices, loopback_name, want_ipv6=want_ipv6)
    if not provider_targets:
        self.logger.warning("No provider loopback targets found (check roles/loopback name/IPs).")
        return {"results": {"igp_validation": {"columns": [], "rows": [], "summary": {"total": 0, "passes": 0, "fails": 0}}}}

    # Build test plan
    tests_by_host = defaultdict(list)
    napalm_driver_by_host = {}
    for dev in src_devices:
        local_v4 = self._get_loopback_ip(dev, loopback_name, want_ipv6=False)
        local_v6 = self._get_loopback_ip(dev, loopback_name, want_ipv6=True) if want_ipv6 else None
        local_ip_by_family = {
            "IPv4": str(local_v4.address.ip) if local_v4 else None,
            "IPv6": str(local_v6.address.ip) if local_v6 else None,
        }
        napalm_driver_by_host[dev.name] = getattr(getattr(dev, "platform", None), "napalm_driver", None)
        for tgt in provider_targets:
            if tgt["dst_dev_name"] == dev.name:
                continue
            src_ip = local_ip_by_family.get(tgt["family"])
            if not src_ip:
                self.logger.error(
                    "Device %s missing %s loopback IP on %s; cannot test targets in this family.",
                    dev.name, tgt["family"], loopback_name,
                )
                continue
            tests_by_host[dev.name].append({
                "family": tgt["family"],
                "src_dev_name": dev.name,
                "src_ip": src_ip,
                "dst_dev_name": tgt["dst_dev_name"],
                "dst_ip": tgt["dst_ip_str"],
                "dst_prefix": tgt["dst_prefix"],
            })

    if not tests_by_host:
        self.logger.warning("No eligible tests generated (missing loopbacks or no cross-device targets).")
        return {"results": {"igp_validation": {"columns": [], "rows": [], "summary": {"total": 0, "passes": 0, "fails": 0}}}}

    # Initialize Nornir
    nr = InitNornir(
        logging={"enabled": False},
        runner={"options": {"num_workers": 20}},
        inventory={
            "plugin": "nautobot-inventory",
            "options": {
                "credentials_class": "nautobot_plugin_nornir.plugins.credentials.env_vars.CredentialsEnvVars",
                "queryset": src_devices,
            },
        },
    )
    target_hostnames = list(tests_by_host.keys())
    nr_filtered = nr.filter(F(name__in=target_hostnames))
    for host_name, tests in tests_by_host.items():
        if host_name in nr_filtered.inventory.hosts:
            nr_filtered.inventory.hosts[host_name].data["tests_for_host"] = tests
            nr_filtered.inventory.hosts[host_name].data["napalm_driver"] = napalm_driver_by_host.get(host_name)
```

- **What**: Processes inputs (cast to appropriate types), queries active devices (scoped by sites/roles), sets provider devices (defaults to sources if unset), collects targets, builds per-host test lists (skipping self-pings), and initializes Nornir with filtered hosts.
- **Why**: 
  - This sets up the job’s scope and test plan. Early exits with empty reports handle edge cases (no devices/IPs) to avoid crashes. 
  - Prefetching optimizes database queries. 
  - Skipping self-pings prevents irrelevant tests. 
  - Nornir’s parallelism (`num_workers=20`) scales for large networks, and attaching tests to host data ensures each device runs only its relevant checks.

### Route Check Helpers
These verify OSPF routes:

```python
def _ospf_route_check_via_napalm_get(task: Task, dst_prefix: str, vrf_name: str | None) -> tuple[bool, list]:
    getters = ["get_route_to"]
    getters_options = {"get_route_to": {"destination": dst_prefix}}
    if vrf_name:
        getters_options["get_route_to"]["vrf"] = vrf_name
    r = task.run(name=f"ROUTE napalm_get {dst_prefix}", task=napalm_get, getters=getters, getters_options=getters_options)
    route_data = r.result.get("get_route_to", {})
    routes = route_data.get(dst_prefix)
    if routes is None and route_data:
        routes = next(iter(route_data.values()))
    routes = routes or []
    ok = False
    for entry in routes:
        prot = str(entry.get("protocol", "")).lower()
        active = bool(entry.get("current_active"))
        if active and "ospf" in prot:
            ok = True
            break
    return ok, routes

def _ospf_route_check_via_cli(task: Task, family: str, dst_prefix: str, vrf_name: str | None) -> tuple[bool, str]:
    is_v6 = (family == "IPv6")
    base = "show ipv6 route" if is_v6 else "show ip route"
    cmd = f"{base} {('vrf ' + vrf_name + ' ') if vrf_name else ''}{dst_prefix}"
    res = task.run(name=f"ROUTE cli {dst_prefix}", task=napalm_cli, commands=[cmd])
    out = res.result.get(cmd, "") if isinstance(res.result, dict) else str(res.result)
    text = str(out)
    low = text.lower()
    if dst_prefix.split("/")[0] not in low and dst_prefix not in low:
        return False, text
    ospf_hit = ("ospf" in low)
    code_hit = False
    code_patterns = [
        r"^\s*o[ a-z0-9]*\s+.*" + re.escape(dst_prefix.split("/")[0]),
        r"^\s*o[ a-z0-9]*\s+" + re.escape(dst_prefix),
    ]
    for pat in code_patterns:
        if re.search(pat, text, flags=re.IGNORECASE | re.MULTILINE):
            code_hit = True
            break
    ok = bool(ospf_hit or code_hit)
    return ok, text
```

- **What**: 
  - `_ospf_route_check_via_napalm_get` uses NAPALM’s `get_route_to` to check for an active OSPF route to the target prefix.
  - `_ospf_route_check_via_cli` runs show ipv6 route and parses output with regex for OSPF indicators (e.g., 'O' code).
- **Why**: 
  - NAPALM getters provide structured data, ideal for reliable parsing, but some drivers lack IPv6 or VRF support.
  - The CLI fallback ensures compatibility by parsing raw output, using regex to match OSPF routes across vendors (e.g., 'O IA' for inter-area). 
  - This dual approach maximizes robustness for BGP/MPLS prerequisites.

### Per-Host Task
```python
def verify_igp_to_providers(task: Task, icmp_count: int, per_ping_timeout: int) -> Result:
    tests_for_host = task.host.data.get("tests_for_host", [])
    composite_results = []
    table_rows = []
    success_rows = []
    fail_rows = []
    success_dst_devices = set()
    failed_dst_devices = set()

    for test in tests_for_host:
        desc = f"{test['family']} {task.host.name}(lo) -> {test['dst_ip']} on {test['dst_dev_name']}(lo)"
        # Route check
        route_ok = False
        route_method = None
        if test["family"] == "IPv6" and bool(skip_ipv6_routes):
            self.logger.info("OSPF SKIP: %s - IPv6 route validation skipped by setting.", desc)
            route_ok = None
            route_method = "SKIP"
        else:
            try:
                ok, routes = _ospf_route_check_via_napalm_get(task, test["dst_prefix"], vrf_name)
                route_ok, route_method = ok, "napalm_get"
                if not ok:
                    self.logger.warning("OSPF MISS: %s - no active OSPF route via napalm_get; attempting CLI fallback.", desc)
                    try:
                        ok_cli, _text = _ospf_route_check_via_cli(task, test["family"], test["dst_prefix"], vrf_name)
                        route_ok, route_method = ok_cli, "cli"
                    except Exception as e_cli:
                        self.logger.error("OSPF FAIL: %s - CLI fallback error: %s", desc, e_cli)
            except Exception as e_get:
                self.logger.warning("OSPF WARN: %s - napalm_get error: %s; trying CLI fallback.", desc, e_get)
                try:
                    ok_cli, _text = _ospf_route_check_via_cli(task, test["family"], test["dst_prefix"], vrf_name)
                    route_ok, route_method = ok_cli, "cli"
                except Exception as e_cli2:
                    self.logger.error("OSPF FAIL: %s - route lookup error (CLI fallback): %s", desc, e_cli2)

        # Ping check
        ping_ok = False
        try:
            kwargs = {
                "dest": test["dst_ip"],
                "source": test["src_ip"],
                "count": icmp_count,
                "timeout": per_ping_timeout,
            }
            if vrf_name:
                kwargs["vrf"] = vrf_name
            p = task.run(name=f"PING {desc}", task=napalm_ping, **kwargs)
            data = p.result
            if isinstance(data, dict):
                if "success" in data and isinstance(data["success"], dict):
                    ping_ok = data["success"].get("packet_loss") in (0, 0.0)
                elif "packet_loss" in data:
                    ping_ok = data.get("packet_loss") in (0, 0.0)
            if not ping_ok:
                self.logger.error("PING FAIL: %s - result: %s", desc, data)
        except Exception as e:
            self.logger.error("PING FAIL: %s - ping error: %s", desc, e)

        # Verdict
        final_ok = bool(ping_ok) if test["family"] == "IPv6" and skip_ipv6_routes else bool(route_ok) and bool(ping_ok)

        # Logging
        if final_ok:
            self.logger.info("SUCCESS: %s -> %s (%s) [%s -> %s]", ...)
            success_rows.append(test)
            success_dst_devices.add(test["dst_dev_name"])
        else:
            self.logger.error("FAIL: %s -> %s (%s) [%s -> %s] (route_ok=%s, ping_ok=%s)", ...)
            fail_rows.append(test)
            failed_dst_devices.add(test["dst_dev_name"])

        # Table row
        table_rows.append({
            "source_device": test["src_dev_name"],
            "source_ip": test["src_ip"],
            "target_device": test["dst_dev_name"],
            "target_ip": test["dst_ip"],
            "target_prefix": test["dst_prefix"],
            "family": test["family"],
            "vrf": vrf_name or "",
            "route_method": route_method or "",
            "route_status": "SKIP" if route_ok is None else ("PASS" if route_ok else "FAIL"),
            "ping_status": "PASS" if ping_ok else "FAIL",
            "result": "PASS" if final_ok else "FAIL",
        })

    # Per-host summary
    total_per_host = len(tests_for_host)
    succ = len(success_rows)
    if succ:
        self.logger.info("SUMMARY SUCCESS: %s reached %s/%s targets: %s", ...)
    if fail_rows:
        self.logger.error("SUMMARY FAIL: %s had failures to %s/%s targets: %s", ...)

    task.host.data["composite_results"] = composite_results
    task.host.data["table_rows"] = table_rows
    return Result(host=task.host, result=f"Executed {len(tests_for_host)} provider checks")
```

- **What**: Iterates host-specific tests, runs route checks (skipping IPv6 if set), pings from source to target loopback, determines pass/fail (route+ping or ping-only for IPv6 skip), logs details, builds table rows, and summarizes per host.
- **Why**: 
  - This task encapsulates per-device logic for Nornir’s parallel execution. 
  - Route checks ensure OSPF advertises loopbacks; pings confirm reachability for BGP/MPLS. 
  - Detailed logging aids debugging (e.g., which check failed). 
  - Table rows feed the UI, with fields like route_method showing how routes were checked (NAPALM or CLI). 
  - Per-host summaries provide a quick overview, enhancing auditability.

### Execution and Aggregation
```python
agg = nr_filtered.run(name="IGP Provider Loopback Validation", task=verify_igp_to_providers, ...)
total = 0
passes = 0
fails = 0
all_rows = []
for host_name, _multi_result in agg.items():
    host_obj = nr_filtered.inventory.hosts.get(host_name)
    rows = host_obj.data.get("table_rows", []) if host_obj else []
    total += len(rows)
    for r in rows:
        if r.get("result") == "PASS":
            passes += 1
        else:
            fails += 1
    all_rows.extend(rows)

report_payload = {
    "columns": ["Source Device", "Src Loopback", "Target Device", "Target Loopback", "Family", "VRF", "Route Check", "Ping", "Result"],
    "rows": [{
        "Source Device": r["source_device"],
        "Src Loopback": r["source_ip"],
        "Target Device": r["target_device"],
        "Target Loopback": f"{r['target_ip']} ({r['target_prefix']})",
        "Family": r["family"],
        "VRF": r["vrf"],
        "Route Check": f"{r['route_status']}{'/' + r['route_method'] if r['route_method'] else ''}",
        "Ping": r["ping_status"],
        "Result": r["result"],
    } for r in all_rows],
    "summary": {"total": total, "passes": passes, "fails": fails},
}

try:
    self.job_result.data_update({"results": {"igp_validation": report_payload}})
except Exception:
    try:
        data = getattr(self.job_result, "data", {}) or {}
        results_key = data.get("results") or {}
        results_key["igp_validation"] = report_payload
        data["results"] = results_key
        self.job_result.data = data
        self.job_result.save()
    except Exception as e:
        self.logger.error("Could not persist report data to JobResult: %s", e)

self.logger.info(f"Summary: {passes}/{total} checks passed, {fails} failed.")
if fails > 0:
    return {"results": {"igp_validation": report_payload}}
return {"results": {"igp_validation": report_payload}}
```

- **What**: Executes tasks via Nornir, aggregates table rows, counts passes/fails, builds a structured payload with columns/rows/summary, persists it to `JobResult.data['results']['igp_validation']`, logs overall summary, and returns payload (optionally raising for UI failure status).
- **Why**: 
  - Parallel execution scales for large networks.
  - The payload’s structure (columns, rows, summary) enables custom UI rendering, unlike plain logs.
  - Persisting via data_update ensures data is saved even if the job fails, critical for debugging.
  - The return ensures UI access, aligning with Nautobot’s job result model.

### Registration
```python
register_jobs(IGPProviderLoopbackValidation)
```

- **What**: Registers the job for Nautobot’s UI.
- **Why**: Makes the job discoverable and executable via the Jobs menu.

## UI Customization: HTML Templates
To make results operator-friendly, we override Nautobot’s Job Results page with a custom tab.

`customized_jobresult.html`
```html
{%raw%}
{% extends 'generic/object_detail.html' %}
{% load helpers %}
{% load custom_links %}
{% load form_helpers %}
{% load log_levels %}
{% load plugins %}
{% load static %}
{% load buttons %}

{% block breadcrumbs %}
    <li><a href="{% url 'extras:jobresult_list' %}">Job Results</a></li>
    {% if result.job_model is not None %}
        <li>{{ result.job_model.grouping }}</li>
        <li><a href="{% url 'extras:jobresult_list' %}?job_model={{ result.job_model.name }}">
            {{ result.job_model }}
        </a></li>
    {% elif associated_record %}
        {% if associated_record.name %}
            <li><a href="{% url 'extras:jobresult_list' %}?name={{ associated_record.name|urlencode }}">
                {{ associated_record.name }}
            </a></li>
        {% else %}
            <li>{{ associated_record }}</li>
        {% endif %}
    {% elif job %}
        <li><a href="{% url 'extras:jobresult_list' %}?name={{ job.class_path|urlencode }}">
            {{ job.class_path }}
        </a></li>
    {% else %}
        <li>{{ result.name }}</li>
    {% endif %}
    <li>{{ result.created }}</li>
{% endblock breadcrumbs %}

{% block buttons %}
    {% if perms.extras.run_job %}
        {% if result.job_model and result.task_kwargs %}
            <a href="{% url 'extras:job_run' pk=result.job_model.pk %}?kwargs_from_job_result={{ result.pk }}"
               class="btn btn-success">
                <span class="mdi mdi-repeat" aria-hidden="true"></span> Re-Run
            </a>
        {% elif result.job_model is not None %}
            <a href="{% url 'extras:job_run' pk=result.job_model.pk %}"
               class="btn btn-primary">
                <span class="mdi mdi-play" aria-hidden="true"></span> Run
            </a>
        {% endif %}
    {% endif %}
    <a href="{% url 'extras-api:joblogentry-list' %}?job_result={{ result.pk }}&format=csv" class="btn btn-success">
        <span class="mdi mdi-database-export" aria-hidden="true"></span> Export
    </a>
    {{ block.super }}
{% endblock buttons %}

{% block title %}
    Job Result:
    {% if result.job_model is not None %}
        {{ result.job_model }}
    {% elif associated_record %}
        {{ associated_record }}
    {% elif job %}
        {{ job }}
    {% else %}
        {{ result.name }}
    {% endif %}
{% endblock %}

{% block extra_nav_tabs %}
    {% if result.data.output %}
        <li role="presentation">
            <a href="#output" role="tab" data-toggle="tab">Output</a>
        </li>
    {% endif %}
    {% if result.result.results.igp_validation %}
        <li role="presentation">
            <a href="#igp-validation" role="tab" data-toggle="tab">IGP Validation</a>
        </li>
    {% endif %}
{% endblock %}

{% block content_full_width_page %}
    {% include 'extras/inc/jobresult.html' with result=result log_table=log_table %}
{% endblock content_full_width_page %}

{% block advanced_content_left_page %}
    <div class="panel panel-default">
        <div class="panel-heading">
            <strong>Job Keyword Arguments</strong>
        </div>
        <div class="panel-body">
            {% include 'extras/inc/json_data.html' with data=result.task_kwargs format="json" %}
        </div>
    </div>
    <div class="panel panel-default">
        <div class="panel-heading">
            <strong>Job Positional Arguments</strong>
        </div>
        <div class="panel-body">
            {% include 'extras/inc/json_data.html' with data=result.task_args format="json" %}
        </div>
    </div>
    <div class="panel panel-default">
        <div class="panel-heading">
            <strong>Job Celery Keyword Arguments</strong>
        </div>
        <div class="panel-body">
            {% include 'extras/inc/json_data.html' with data=result.celery_kwargs format="json" %}
        </div>
    </div>
{% endblock advanced_content_left_page %}
{% block advanced_content_right_page %}
    <div class="panel panel-default">
        <div class="panel-heading">
            <strong>Worker</strong>
        </div>
        <table class="table table-hover panel-body attr-table">
            <tbody>
                <tr>
                    <td>Worker Hostname</td>
                    <td>{{ result.worker }}</td>
                </tr>
                <tr>
                    <td>Queue</td>
                    <td>{{ result.celery_kwargs.queue}}</td>
                </tr>
                <tr>
                    <td>Task Name</td>
                    <td>{{ result.task_name }}</td>
                </tr>
                <tr>
                    <td>Meta</td>
                    <td>{% include 'extras/inc/json_data.html' with data=result.meta format="json" %}</td>
                </tr>
            </tbody>
        </table>
    </div>
    <div class="panel panel-default">
        <div class="panel-heading">
            <strong>Traceback</strong>
        </div>
        <div class="panel-body">
            {% include 'extras/inc/json_data.html' with data=result.traceback format="python" %}
        </div>
    </div>
{% endblock advanced_content_right_page %}

{% block extra_tab_content %}
    {% if result.data.output %}
        <div role="tabpanel" class="tab-pane" id="output">
            <pre>{{ result.data.output }}</pre>
        </div>
    {% endif %}
    {% if result.result.results.igp_validation %}
        <div role="tabpanel" class="tab-pane" id="igp-validation">
            {% include 'extras/inc/igp_validation_form.html' %}
        </div>
    {% endif %}
{% endblock extra_tab_content %}

{% block javascript %}
    {{ block.super }}
    {% include 'extras/inc/jobresult_js.html' with result=result %}
    <script src="{% versioned_static 'js/tableconfig.js' %}"></script>
    <script src="{% versioned_static 'js/log_level_filtering.js' %}"></script>
{% endblock %}
{%endraw%}
```

- **What**: Replaces Nautobot’s jobresults.html, adding an “IGP Validation” tab in extra_nav_tabs if `result.result.results.igp_validation` exists. In extra_tab_content, renders the tab’s content via an include.
- **Why**: Adds a dedicated tab for IGP results, keeping logs separate. Checking `result.result.results.igp_validation` ensures the tab only appears when relevant. The include keeps the template modular, aligning with Django’s best practices.

`igp_validation_form.html`
```html
{%raw%}
{% load helpers %}
{% if result.data.results.igp_validation %}
  <div class="card mb-3">
    <div class="card-header"><strong>IGP Provider Loopback Validation - Summary</strong></div>
    <div class="card-body">
      <div class="row g-3">
        <div class="col-auto"><span class="badge bg-secondary">Total: {{ result.data.results.igp_validation.summary.total|default_if_none:"0" }}</span></div>
        <div class="col-auto"><span class="badge bg-success">Pass: {{ result.data.results.igp_validation.summary.passes|default_if_none:"0" }}</span></div>
        <div class="col-auto"><span class="badge bg-danger">Fail: {{ result.data.results.igp_validation.summary.fails|default_if_none:"0" }}</span></div>
      </div>
    </div>
  </div>
  <div class="card">
    <div class="card-header"><strong>IGP Provider Loopback Validation Results</strong></div>
    <div class="table-responsive">
      <table class="table table-hover table-striped mb-0">
        <thead>
          <tr>
            {% if result.data.results.igp_validation.columns %}
              {% for col in result.data.results.igp_validation.columns %}
                <th scope="col">{{ col }}</th>
              {% endfor %}
            {% elif result.data.results.igp_validation.rows and result.data.results.igp_validation.rows.0 %}
              {% for k in result.data.results.igp_validation.rows.0 %}
                <th scope="col">{{ k }}</th>
              {% endfor %}
            {% else %}
              <th scope="col">No data</th>
            {% endif %}
          </tr>
        </thead>
        <tbody>
          {% if result.data.results.igp_validation.rows %}
            {% if result.data.results.igp_validation.columns %}
              {% for row in result.data.results.igp_validation.rows %}
                <tr>
                  {% for col in result.data.results.igp_validation.columns %}
                    {% with val=row|get_item:col %}
                      {% if col == "Route Check" or col == "Ping" or col == "Result" %}
                        {% if val and "PASS" in val %}
                          <td><span class="badge bg-success">{{ val }}</span></td>
                        {% elif val and "SKIP" in val %}
                          <td><span class="badge bg-secondary">{{ val }}</span></td>
                        {% else %}
                          <td><span class="badge bg-danger">{{ val }}</span></td>
                        {% endif %}
                      {% else %}
                        <td>{{ val }}</td>
                      {% endif %}
                    {% endwith %}
                  {% endfor %}
                </tr>
              {% endfor %}
            {% else %}
              {% with first_row=result.data.results.igp_validation.rows.0 %}
                {% for row in result.data.results.igp_validation.rows %}
                  <tr>
                    {% for k in first_row %}
                      {% with val=row|get_item:k %}
                        {% if k == "Route Check" or k == "Ping" or k == "Result" %}
                          {% if val and "PASS" in val %}
                            <td><span class="badge bg-success">{{ val }}</span></td>
                          {% elif val and "SKIP" in val %}
                            <td><span class="badge bg-secondary">{{ val }}</span></td>
                          {% else %}
                            <td><span class="badge bg-danger">{{ val }}</span></td>
                        {% endif %}
                      {% else %}
                        <td>{{ val }}</td>
                      {% endif %}
                    {% endwith %}
                  {% endfor %}
                </tr>
              {% endfor %}
            {% endwith %}
          {% endif %}
        {% else %}
          <tr>
            {% if result.data.results.igp_validation.columns %}
              <td colspan="{{ result.data.results.igp_validation.columns|length }}" class="text-muted">No results available.</td>
            {% else %}
              <td class="text-muted">No results available.</td>
            {% endif %}
          </tr>
        {% endif %}
      </tbody>
    </table>
  </div>
{% else %}
  <div class="alert alert-warning mb-0">No IGP validation data available.</div>
{% endif %}
{%endraw%}
```

- **What**: 
  - Renders a summary card with Total/Pass/Fail badges and a responsive table using columns and rows from the payload. 
  - Status fields (Route Check, Ping, Result) get color-coded badges (green=PASS, red=FAIL, gray=SKIP). 
  - Fallbacks handle missing columns by using row keys.
- **Why**: 
  - The summary provides a quick overview, critical for large result sets. 
  - The table’s color-coding highlights issues (e.g., OSPF route missing) instantly. 
  - Fallbacks ensure rendering even if payload structure varies, enhancing robustness. 
  - The responsive design suits Nautobot’s UI, making it operator-friendly for troubleshooting.

## Setup and Running
1. Place `igploopback_validation.py` in `nautobot-docker-compose/jobs` folder.
2. Mount templates via `docker-compose.local.yml`:

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
      - "../custom_python_code/custom_ext.py:/usr/local/lib/python${PYTHON_VER}/site-packages/nautobot_design_builder/contrib/ext.py"
      - "../templates/igp_validation_form.html:/usr/local/lib/python${PYTHON_VER}/site-packages/nautobot/extras/templates/extras/inc/igp_validation_form.html"
      - "../templates/customized_jobresult.html:/usr/local/lib/python${PYTHON_VER}/site-packages/nautobot/extras/templates/extras/jobresult.html"
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
      - "../custom_python_code/custom_ext.py:/usr/local/lib/python${PYTHON_VER}/site-packages/nautobot_design_builder/contrib/ext.py"
  celery_beat:
    volumes:
      - "../config/nautobot_config.py:/opt/nautobot/nautobot_config.py"
      - "../jobs:/opt/nautobot/jobs"
      - "../custom_jinja_filters:/opt/nautobot/custom_jinja_filters"
      - "../custom_python_code/custom_ext.py:/usr/local/lib/python${PYTHON_VER}/site-packages/nautobot_design_builder/contrib/ext.py"
```

Run via Nautobot UI (Extras > Jobs).

## Output
UI shows a tab with summary badges and a table, color-coding PASS/FAIL/SKIP.

<img src="/assets/img/nautobot_workshop/igp-validation-tab.webp" alt="Custom Tab">

## Conclusion
This job ensures OSPF loopbacks are ready for BGP and MPLS, automating critical validations with robust fallbacks and a user-friendly UI. 

It’s a key step in scaling network assurance for complex designs. 

Explore [Nautobot’s](https://github.com/nautobot/nautobot) docs. Full code as always is in the [Github Repository](https://github.com/byrn-baker/Nautobot-Workshop).