---
title: Nautobot Workshop Blog Series - Part 17 - Nautobot Job Hooks - Reducing configuration drift between your live devices and your source of truth
date: 2025-10-08 8:00:00
categories: [Nautobot, Ansible, Automation]
tags: [NetworkAutomation, NetworkSourceOfTruth, nautobot, AutomationPlatform, NautobotTutorials]
image:
  path: /assets/img/nautobot_workshop/light_title_image-50.webp
---

# Nautobot Job Hooks - Reducing configuration drift between your live devices and your source of truth
<div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
  <iframe src="https://www.youtube.com/embed/gZfgyWimL00" 
          frameborder="0" 
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
          allowfullscreen 
          style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
  </iframe>
</div>

[▶️ Watch the video](https://youtu.be/gZfgyWimL00)

In this post, we’ll reduce configuration drift by wiring Nautobot Job Hooks to enforce interface intent from your Source of Truth (SoT) onto your live network devices. When a Device Interface is updated or deleted in Nautobot, the job reconciles Cisco IOS/NX-OS or Arista EOS configurations to match what’s in Nautobot.

## Concept: Reducing configuration drift between live devices and your SoT
Drift happens when live device configs diverge from your intended state stored in your SoT. Reducing drift means automatically reconciling live configs back to - intent when changes occur.
- Why it matters:
  - Reliability: Devices behave per design rather than ad hoc edits.
  - Auditability: The “why” lives in the SoT; enforcement is automated and logged.
  - Velocity with safety: Changes are reviewed in SoT, then pushed consistently to devices.
- Where it fits in CI/CD:
  - Propose and validate intent (in Git and/or Nautobot) in CI.
  - Merge and update Nautobot (SoT) as the single source.
  - Job Hooks perform event-driven enforcement to live devices.
  - Pipelines observe job results, fail fast on errors, and support rollback by reverting intent.

### What we’ll build
- A Nautobot Job Hook that reacts to DCIM > Interface Updated/Deleted events to:
  - If the Interface has IPv4/IPv6 in Nautobot: 
    - configure those IPs and only no-shut if enabled is True.
  - If the Interface has no IPs: 
    - remove IPs and shut the interface.
  - On Interface delete: best-effort cleanup (remove IPs and shut).
- Multi-vendor support: 
  - Cisco IOS/NX-OS and Arista EOS using Platform.network_driver.
- Works with physical interfaces, port-channels, and VLAN SVIs.

### Prerequisites
Netmiko installed where Nautobot runs:
- Device credentials (use Nautobot Secrets in production; env vars here for simplicity):
- Each Platform has network_driver set to a Netmiko device_type (e.g., cisco_ios, cisco_nxos, arista_eos).

## Job code
Save as jobs/auto_config_interface.py in your sandbox folder.
```python
# jobs/auto_config_interface.py
import os
from ipaddress import ip_interface

from nautobot.apps.jobs import JobHookReceiver, register_jobs
from nautobot.dcim.models import Interface, Device


class AutoConfigureInterface(JobHookReceiver):
    """
    Interface-driven job that keeps Cisco/Arista device config in sync with Nautobot.

    Triggers: DCIM > Interface (Updated, Deleted)
    Behavior:
      * If the interface has any IPs (v4 and/or v6) in Nautobot, configure those IPs on the device.
      * Admin state: only 'no shutdown' if interface.enabled is True; otherwise 'shutdown' (even if IPs exist).
      * If the interface has no IPs, remove any IP config ('no ip address' / 'no ipv6 address') and 'shutdown'.

    Vendors: Cisco IOS/NX-OS and Arista EOS (uses Platform.network_driver)
    Connect: device.primary_ip4, else primary_ip6, else device.name
    """

    class Meta:
        name = "Auto Configure Interface (Interface-driven Cisco/Arista v4/v6)"
        description = "On Interface update/delete: set/remove IPv4/IPv6 and admin state (gates no-shut by enabled flag)."
        commit_default = True
        grouping = "JobHooks"

    # -----------------------
    # Helpers
    # -----------------------
    def _get_host_for_device(self, device):
        if device.primary_ip4:
            return str(device.primary_ip4.address.ip)
        if device.primary_ip6:
            return str(device.primary_ip6.address.ip)
        return device.name

    def _driver_family(self, driver):
        """
        Return 'cisco', 'arista', or None for unsupported.
        Accepts common variants.
        """
        d = (driver or "").lower().strip()
        if any(x in d for x in ("cisco_ios", "cisco_nxos", "cisco_xe", "ios", "nxos", "xe", "cisco")):
            return "cisco"
        if any(x in d for x in ("arista_eos", "eos", "arista")):
            return "arista"
        return None

    def _collect_first_ips(self, interface):
        """
        Return (ipv4_cidr_or_none, ipv6_cidr_or_none) from Interface.ip_addresses.
        Prefers the first address of each family.
        """
        v4 = None
        v6 = None
        for ip in interface.ip_addresses.all():
            if not getattr(ip, "address", None):
                continue
            ver = getattr(ip.address, "version", None)
            if ver == 4 and v4 is None:
                v4 = str(ip.address)
            elif ver == 6 and v6 is None:
                v6 = str(ip.address)
            if v4 and v6:
                break
        return v4, v6

    def _is_l3_capable_phys(self, if_name):
        """
        True for typical L2/L3 physical or aggregated ports that may need 'no switchport' for L3 config.
        Skip SVI (Vlan) and Loopback.
        """
        name = (if_name or "").lower()
        if name.startswith("vlan") or name.startswith("lo") or name.startswith("loopback"):
            return False
        return True

    def _build_cfg_from_state(self, driver, interface_name, v4_cidr, v6_cidr, enabled_flag):
        """
        Build config lines so device matches Nautobot state:
        - If any IP present (v4 and/or v6): add those IPs.
        - If no IPs: remove any existing IP config.
        - Admin state: 'no shutdown' only if enabled_flag is True; otherwise 'shutdown'.
        """
        fam = self._driver_family(driver)
        if fam is None:
            raise RuntimeError(f"Unsupported network_driver '{driver}'.")

        cfg = [f"interface {interface_name}"]
        has_any_ip = bool(v4_cidr or v6_cidr)

        # If adding IPs on a physical/port-channel, ensure routed mode
        if has_any_ip and self._is_l3_capable_phys(interface_name):
            cfg.append("no switchport")

        # IPv4
        if v4_cidr:
            v4 = ip_interface(v4_cidr)
            if fam == "cisco":
                cfg.append(f"ip address {v4.ip} {v4.netmask}")
            else:
                # Arista prefers prefix format for IPv4
                cfg.append(f"ip address {v4.ip}/{v4.network.prefixlen}")
        else:
            # Remove any IPv4 if none in Nautobot
            cfg.append("no ip address")

        # IPv6
        if v6_cidr:
            v6 = ip_interface(v6_cidr)
            if fam == "cisco":
                cfg.append(f"ipv6 address {v6.with_prefixlen}")
            else:
                # EOS commonly needs ipv6 enabled on the interface
                cfg.append("ipv6 enable")
                cfg.append(f"ipv6 address {v6.with_prefixlen}")
        else:
            cfg.append("no ipv6 address")

        # Admin state gated by 'enabled' boolean
        cfg.append("no shutdown" if enabled_flag and has_any_ip else "shutdown")
        return cfg

    def _build_cleanup_for_deleted_interface(self, driver, interface_name):
        """
        Best-effort cleanup when the Interface was deleted in Nautobot.
        Remove any IPs and shut the port.
        """
        fam = self._driver_family(driver)
        if fam is None:
            raise RuntimeError(f"Unsupported network_driver '{driver}'.")

        cfg = [f"interface {interface_name}"]
        cfg.append("no ip address")
        cfg.append("no ipv6 address")
        cfg.append("shutdown")
        return cfg

    def _connect(self, host, username, password, device_type):
        from netmiko import ConnectHandler
        return ConnectHandler(
            host=host,
            username=username,
            password=password,
            device_type=device_type,
            timeout=30,
        )

    def _norm_action(self, action):
        a = (action or "").lower()
        if a.startswith("creat"):
            return "create"
        if a.startswith("updat"):
            return "update"
        if a.startswith("delet"):
            return "delete"
        return a

    # -----------------------
    # Core
    # -----------------------
    def run(self, object_change=None, **kwargs):
        if object_change is None:
            raise RuntimeError("JobHookReceiver requires 'object_change' in kwargs.")

        ct = object_change.changed_object_type  # ContentType
        action = self._norm_action(getattr(object_change, "action", ""))
        obj_id = object_change.changed_object_id

        # Only handle DCIM.Interface events (Updated, Deleted)
        if not (ct.app_label == "dcim" and ct.model == "interface"):
            self.logger.info(f"Ignoring {ct.app_label}.{ct.model} action={action}; only DCIM.Interface is handled.")
            return "No changes."

        # Credentials
        username = (
            os.getenv("NET_USERNAME")
            or os.getenv("NAUTOBOT_NET_USERNAME")
            or os.getenv("NAPALM_USERNAME")
        )
        password = (
            os.getenv("NET_PASSWORD")
            or os.getenv("NAUTOBOT_NET_PASSWORD")
            or os.getenv("NAPALM_PASSWORD")
        )
        if not (username and password):
            raise RuntimeError("Set NET_USERNAME and NET_PASSWORD (or equivalent) for device access.")

        if action in ("update", "create"):
            # Interface exists in DB
            interface = Interface.objects.select_related("device__platform").get(id=obj_id)
            device = interface.device
            platform = device.platform
            driver = getattr(platform, "network_driver", None) if platform else None
            if not driver or self._driver_family(driver) is None:
                self.logger.warning(
                    f"Skipping {device.name} {interface.name}: unsupported or missing network_driver '{driver}'."
                )
                return "No changes."

            host = self._get_host_for_device(device)

            # Collect current desired addressing and admin state from Nautobot
            v4_cidr, v6_cidr = self._collect_first_ips(interface)
            enabled_flag = bool(getattr(interface, "enabled", True))

            cfg = self._build_cfg_from_state(driver, interface.name, v4_cidr, v6_cidr, enabled_flag)

            self.logger.info(
                f"Connecting to {device.name} ({host}) as {username}; driver '{driver}'. "
                f"Desired: v4={v4_cidr}, v6={v6_cidr}, enabled={enabled_flag}"
            )
            try:
                conn = self._connect(host, username, password, driver)
                self.logger.info(f"Sending configuration to {device.name}: {cfg}")
                output = conn.send_config_set(cfg)
                self.logger.info(output)
                # Save best-effort
                try:
                    save_output = conn.save_config()
                except Exception:
                    try:
                        save_output = conn.send_command_timing("write memory")
                    except Exception:
                        save_output = "Save not supported or failed."
                self.logger.info(f"Configuration saved on {device.name}. Output: {save_output}")
                conn.disconnect()
            except Exception as exc:
                self.logger.error(f"Failed to configure {device.name} {interface.name}: {exc}")
                raise

            state_desc = (
                f"{'IP set' if (v4_cidr or v6_cidr) else 'IP removed'}; "
                f"{'no shut' if (enabled_flag and (v4_cidr or v6_cidr)) else 'shutdown'}"
            )
            return f"Applied on {device.name} {interface.name}: {state_desc}"

        elif action == "delete":
            # Interface deleted: cleanup using object_data
            data = getattr(object_change, "object_data", {}) or {}
            if_name = data.get("name")
            device_id = data.get("device")
            if not if_name or not device_id:
                self.logger.warning("Interface delete missing 'name' or 'device' in object_data; skipping.")
                return "No changes."

            try:
                device = Device.objects.select_related("platform").get(id=device_id)
            except Device.DoesNotExist:
                self.logger.warning(f"Device {device_id} not found; skipping cleanup for deleted interface {if_name}.")
                return "No changes."

            driver = getattr(device.platform, "network_driver", None) if device.platform else None
            if not driver or self._driver_family(driver) is None:
                self.logger.warning(f"Skipping {device.name} {if_name}: unsupported or missing network_driver '{driver}'.")
                return "No changes."

            host = self._get_host_for_device(device)
            cfg = self._build_cleanup_for_deleted_interface(driver, if_name)

            self.logger.info(f"Connecting to {device.name} ({host}) as {username}; driver '{driver}' for delete cleanup")
            try:
                conn = self._connect(host, username, password, driver)
                self.logger.info(f"Sending cleanup to {device.name}: {cfg}")
                output = conn.send_config_set(cfg)
                self.logger.info(output)
                # Save best-effort
                try:
                    save_output = conn.save_config()
                except Exception:
                    try:
                        save_output = conn.send_command_timing("write memory")
                    except Exception:
                        save_output = "Save not supported or failed."
                self.logger.info(f"Cleanup saved on {device.name}. Output: {save_output}")
                conn.disconnect()
            except Exception as exc:
                self.logger.error(f"Failed cleanup on {device.name} {if_name}: {exc}")
                raise

            return f"Cleanup applied on {device.name} {if_name}: IPs removed; shutdown"

        else:
            self.logger.info(f"Ignoring interface action={action}; only update/create/delete handled.")
            return "No changes."


register_jobs(AutoConfigureInterface)
```

### Imports
- os: read device credentials from environment variables (quick demo approach).
- ipaddress.ip_interface: robustly parse IPv4 and IPv6 CIDR strings from Nautobot, and derive netmask/prefixlen for correct vendor syntax.
- nautobot.apps.jobs.JobHookReceiver: special base class for event-driven jobs; Nautobot passes object_change (the ObjectChange record) directly to run(). This is why the job - doesn’t define user input fields.
- nautobot.apps.jobs.register_jobs: registers the Job class so Nautobot can discover and run it.
- nautobot.dcim.models.Interface: we read the Interface from the DB to discover its IPs and enabled flag.
- nautobot.dcim.models.Device: used during delete cleanup to find the device by ID that the interface belonged to.

### Why there are no fields (no user input variables)
- This job is not an interactive, form-driven job; it’s event-driven via Job Hooks.
- JobHookReceiver’s run() receives object_change for the specific Interface event. From that, we look up the exact Interface and read all needed state (IPs, enabled, device, - platform).
- Operationally, this ensures the job is fully deterministic and idempotent based on SoT data, not per-run manual inputs.

### Class AutoConfigureInterface and Meta
- Subclasses JobHookReceiver to accept the object_change payload that Nautobot emits for each Interface event.
- Meta.name/description: how the job appears in Nautobot’s UI.
- Meta.grouping = "JobHooks": groups it under a sensible heading.
- Meta.commit_default = True: conventional default; Netmiko changes occur on the device regardless of “dry run” in the Nautobot sense (there’s no db transaction here), but this keeps UI consistent.

### Helper methods
- _get_host_for_device(device): chooses management address with a sensible preference (primary IPv4 first, then IPv6, then hostname).
- _driver_family(driver): simplifies multi-vendor logic by mapping platform.network_driver to a family. This job supports Cisco IOS/NX-OS and Arista EOS. Extend this to support - more vendors.
- _collect_first_ips(interface): gets the first IPv4 and first IPv6 assigned to the Interface. It keeps the example simple while supporting dual-stack. If you use multiple - addresses or secondaries, you’d extend this to render them all.
- _is_l3_capable_phys(if_name): guards “no switchport” so we only push it to routed physical/Port-Channel interfaces. We explicitly skip SVIs (VlanX) and Loopbacks where - switchport doesn’t apply.
- _build_cfg_from_state(driver, interface_name, v4_cidr, v6_cidr, enabled_flag):
  - Produces the intended per-interface configuration based on Nautobot state.
  - If any IP exists:
    - For Cisco: ip address A.B.C.D M.M.M.M and ipv6 address X::/len.
    - For Arista: ip address A.B.C.D/len; ipv6 enable + ipv6 address X::/len.
  - Adds “no switchport” for routed physical/Port-Channel interfaces so the device accepts L3 addressing.
  - If no IPs exist: emits “no ip address” and “no ipv6 address” to clean up any existing config.
  - Admin state: only “no shutdown” if enabled_flag is True and at least one IP is present; otherwise “shutdown.”
- _build_cleanup_for_deleted_interface(driver, interface_name): best-effort cleanup when the Interface is removed from Nautobot. We can’t read live IPs anymore, so we send generic - “no ip address” / “no ipv6 address” and “shutdown.”
- _connect(host, username, password, device_type): encapsulates Netmiko connection. It lazily imports ConnectHandler to keep module load light and makes unit testing easier.
- _norm_action(action): normalizes action strings (Created/Updated/Deleted vs create/update/delete) for consistency.

### run method
- Validates this event is for DCIM.Interface; otherwise returns early.
- Reads credentials from environment (swap to Nautobot Secrets Groups in production).
- For update/create:
  - Loads the Interface now in the DB to get the canonical intended state: IPv4/IPv6 and enabled flag.
  - Determines the platform driver and management address.
  - Builds config with _build_cfg_from_state() and pushes using Netmiko.
  - Saves configuration (conn.save_config() or write memory).
- For delete:
  - Pulls interface name and device ID from object_change.object_data.
  - Connects to the device and performs cleanup via _build_cleanup_for_deleted_interface().

### Why it’s interface-driven and not IP-driven
Job Hooks are run when a database object is Created, Updated, or Deleted. To avoid having interface configurations pushed when creating IP addresses for other uses, we focused this Job Hook directly on interface updates and deletions. This avoids unnecessary jobs being run when they are not needed. With Job Hooks, it's important that your configurations are as narrowly scoped as possible, as they will make changes to your live devices. With great power comes great responsibility.

### SVIs (interface VlanX) and Loopbacks
The job supports SVIs and Loopbacks. It does not send “no switchport” to them; it only applies/removes IPs and sets admin state according to the enabled flag.

### Cisco vs Arista specifics
- Cisco IOS/NX-OS:
  - IPv4 uses mask notation (A.B.C.D M.M.M.M).
  - IPv6 uses ipv6 address X::/len (global routing enablement like ipv6 unicast-routing should be a separate baseline).
- Arista EOS:
  - IPv4 uses prefix notation (A.B.C.D/len).
  - IPv6 ensures ipv6 enable on the interface, then ipv6 address X::/len.

### Credentials and security
The example uses environment variables NET_USERNAME and NET_PASSWORD for simplicity. For production use Nautobot Secrets and Secrets Groups, RBAC, and possibly device credential abstraction (per-tenant, per-platform).

### Idempotency and scope
The job applies a straightforward declarative pattern if the SoT says IPs exist, it applies them; if not, it removes them. It does not diff the running configuration beyond that. For more surgical changes, incorporate config retrieval (e.g., NAPALM getters or Netmiko show commands) and render deltas. It configures at most one IPv4 and one IPv6 per interface; extend _collect_first_ips and builder logic if you require multiple addresses, secondary IPs, or VRFs.

### Registering and wiring the Job Hook
Code ends with register_jobs(AutoConfigureInterface)
Create a Job Hook in Nautobot:
- Extras -> Job Hooks -> Add
- Content Types: DCIM > Interfaces
- Events: Updated, Deleted (optionally Created)
- Job: Auto Configure Interface (Interface-driven Cisco/Arista v4/v6)
- Job kwargs: leave empty (JobHookReceiver receives object_change automatically)
- Optional filter: device__isnull: false


# Wrap-Up
In this part of the series, we put “reduce drift” into practice by wiring Nautobot’s Job Hooks to enforce interface intent from your Source of Truth onto live devices. The result: when an interface is updated (or deleted) in Nautobot, Cisco and Arista devices are reconciled automatically to match your intended state.
