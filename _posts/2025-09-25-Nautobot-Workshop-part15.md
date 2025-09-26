---
title: Nautobot Workshop Blog Series - Part 15 - Nautobot Device Lifecycle Management - Part 2
date: 2025-09-25 0:00:00
categories: [Nautobot, Ansible, Automation]
tags: [NetworkAutomation, NetworkSourceOfTruth, nautobot, AutomationPlatform, NautobotTutorials]
image:
  path: /assets/img/nautobot_workshop/light_title_image-50.webp
---

# Creating a Nautobot Job to manage vendor specific CVEs
Building on last week's foundation, this post dives deeper into the essential helpers for pulling platform data, NAPALM drivers, and IP addresses for device logins. We'll also explore the utilities for fetching and normalizing data from Nautobot and the Cisco CVEs API, making your automation more robust and adaptable.

## Platform and Host Helpers
### `_platform_to_napalm_driver`
```python
def _platform_to_napalm_driver(self, platform: Platform) -> str | None:
    explicit = getattr(platform, "napalm_driver", None)
    if explicit:
        return str(explicit)
    name = (platform.name or "").lower()
    if "cisco" in name or "ios" in name:
        return "ios"
    if "arista" in name or "eos" in name:
        return "eos"
    return None
```
#### What's Happening?
This function checks if the Nautobot Platform object has an explicit napalm_driver set—if so, it uses that. Otherwise, it infers the driver from the platform name (case-insensitive). For names containing "cisco" or "ios", it returns "ios"; for "arista" or "eos", it returns "eos". If no match, it returns None for unsupported platforms.NAPALM needs a specific driver string (like "ios" or "eos") to connect and gather facts such as OS version and model. These facts are crucial for matching against CVE databases. This helper ensures a reliable fallback by inferring from the platform name.

#### Caveats
*   Currently supports Cisco IOS/IOS-XE and Arista EOS; NX-OS isn't mapped yet, but the structure allows easy extensions.
*   Uses getattr(platform, "napalm_driver", None) for compatibility across Nautobot versions or custom models.
*   Lowercases the name for flexible, case-insensitive matching (e.g., "Cisco IOS" or "cIsCo").

### `_map_platform_to_cisco_ostype`
```python
def _map_platform_to_cisco_ostype(self, device: Device) -> str | None:
    name = (device.platform.name or "").lower() if device.platform else ""
    if "ios xe" in name or "ios-xe" in name or "xe" in name:
        return "iosxe"
    if "ios" in name:
        return "ios"
    return None
```
#### What's Happening?
It normalizes device.platform.name to a standard Cisco OS type. If the name includes "ios xe", "ios-xe", or "xe", it returns "iosxe". If it just has "ios", it returns "ios". Otherwise, None.Cisco's CVE/PSIRT APIs require standardized OS identifiers (e.g., "iosxe", "nxos"). This mapping ensures accurate queries and relevant advisories, preventing mismatches or irrelevant data.

#### Caveats
*   Cisco-specific; returns None for non-Cisco platforms, allowing fallbacks to generic sources like NVD.
*   Substring-based matching is permissive—watch for edge cases in custom names. For structured environments, consider adding deterministic logic.

### _device_host
   ```python
def _device_host(self, device: Device) -> str:
    try:
        if device.primary_ip and getattr(device.primary_ip, "address", None):
            return str(device.primary_ip.address.ip)
    except Exception:
        pass
    return device.name
```
#### What's Happening?
It returns the optimal connection host: the primary IP (without mask) if available, or falls back to the device name (hostname).IPs are more reliable than names (no DNS needed), but the fallback ensures connectivity in DNS-reliant setups. Tools like NAPALM/Netmiko require a solid host string.
#### Caveats
*   Relies on device.primary_ip (an IPAddress object); tolerant of missing attributes via try/except.
*   For IPv4/IPv6 splits, extend to prefer one or try both.

### _extract_version_token
```python
@staticmethod
def _extract_version_token(os_version_text: str) -> str | None:
    s = (os_version_text or "").strip()
    m = re.search(r"(\d{1,2}\.\d{1,2}\([^)]*\)[A-Za-z0-9]*)", s)
    if m:
        return m.group(1)
    m = re.search(r"(\d{1,2}\.\d{1,2}\.\d{1,2}[A-Za-z]?)", s)
    if m:
        return m.group(1)
    m = re.search(r"(\d{1,2}\.\d{1,2})", s)
    if m:
        return m.group(1)
    return None
```
#### What's Happening?
Devices report verbose OS versions (e.g., "Cisco IOS XE Software, Version 17.3.3a, RELEASE SOFTWARE (fc4)"). This extracts a clean token (e.g., "17.3.3a") for CVE matching, version comparisons, and storage.Steps:
*   Normalize input: Strip whitespace, handle empty/None.
    
*   Match patterns in priority order:
    
    1.  Parentheses-style (e.g., "12.2(55)SE7").
        
    2.  Triple-component with optional letter (e.g., "17.3.3a").
        
    3.  Major.minor fallback (e.g., "12.4").
        
*   Return first match or None.
    
Order prioritizes Cisco formats for precision.

#### Caveats
*   Limited to 1-2 digit segments; misses versions like "100.10.3".  
*   Non-Cisco (e.g., Junos "18.4R3-S8.2") may fail—add vendor-specific patterns as needed.
*   Substring matching can grab partials in complex strings.
   
### Software Model Handling for VulnerabilityLCM.software
```python
@staticmethod
def _model_has_fields(model, required: list[str]) -> bool:
    field_names = {f.name for f in model._meta.get_fields()}
    return all(name in field_names for name in required)
def _software_fk_target_model(self):
    try:
        field = VulnerabilityLCM._meta.get_field("software")
        return field.remote_field.model
    except Exception:
        return None
def _get_platform_field_name(self, model) -> str | None:
    field_names = {f.name for f in model._meta.get_fields()}
    if "platform" in field_names:
        return "platform"
    if "device_platform" in field_names:
        return "device_platform"
    return None
def _resolve_software_instance_for_vuln(self, sv_lcm: SoftwareLCM | SimpleNamespace, commit: bool):
    target_model = self._software_fk_target_model()
    if target_model is None:
        self.logger.warning("Could not resolve VulnerabilityLCM.software target model; skipping vulnerability link.")
        return None
    if target_model is SoftwareLCM:
        return sv_lcm if isinstance(sv_lcm, SoftwareLCM) else None
    fields = {f.name for f in target_model._meta.get_fields()}
    platform_field = self._get_platform_field_name(target_model)
    if platform_field and ("version" in fields):
        filter_kwargs = {
            platform_field: getattr(sv_lcm, "device_platform", None) or getattr(sv_lcm, "platform", None),
            "version": sv_lcm.version,
        }
        if not commit:
            exists = target_model.objects.filter(**filter_kwargs).exists()
            if exists:
                self.logger.info(f"[Dry-run] Would use existing {target_model.__name__} for {filter_kwargs}")
            else:
                self.logger.info(f"[Dry-run] Would create {target_model.__name__} for {filter_kwargs}")
            return None
        try:
            obj, _ = target_model.objects.get_or_create(**filter_kwargs)
            return obj
        except Exception as exc:
            self.logger.warning(f"Failed to get_or_create {target_model.__name__} with {filter_kwargs}: {exc}")
            return None
    if "software" in fields:
        if not isinstance(sv_lcm, SoftwareLCM):
            self.logger.warning("Cannot resolve 'software' FK without a SoftwareLCM instance.")
            return None
        obj = target_model.objects.filter(software=sv_lcm).first()
        if obj:
            return obj
        self.logger.warning(f"No {target_model.__name__} found for software='{sv_lcm}'. Skipping vulnerability link.")
        return None
    self.logger.warning(f"Unsupported VulnerabilityLCM.software FK model ({target_model.__name__}); skipping link.")
    return None
```
#### What's Happening?
What's Happening?These utilities resolve or create the "software" object linked to VulnerabilityLCM, adapting to different schemas:
*   Direct FK to SoftwareLCM.
    
*   Custom model with platform + version.
    
*   Custom model referencing SoftwareLCM via "software".
    
They detect the model shape at runtime and handle linking, with dry-run support.
*   _model_has_fields: Checks if a model has required fields.
    
*   _software_fk_target_model: Gets the model VulnerabilityLCM.software points to.
    
*   _get_platform_field_name: Normalizes "platform" vs. "device_platform".
    
*   _resolve_software_instance_for_vuln: Finds/creates the instance based on schema, logs actions.
    
This ensures consistent vulnerability linking across environments.

#### Caveats
*   Accepts SoftwareLCM or SimpleNamespace for flexibility.
    
*   Dry-run logs without DB changes; commit creates if needed.
   
### Associate CVE with 'Affected Software' M2M Where Supported
```python
def _associate_cve_with_affected_software(
    self,
    cve_obj,
    sv_lcm,
    software_target,
    commit: bool,
):
    m2m_fields = [f for f in cve_obj._meta.get_fields() if getattr(f, "many_to_many", False)]
    if not m2m_fields:
        self.logger.info(f"No compatible 'Affected Software' M2M on CVE {getattr(cve_obj, 'name', '?')}; skipping software association.")
        return
    candidates = []
    if sv_lcm is not None:
        candidates.append(sv_lcm)
    if software_target is not None and software_target is not sv_lcm:
        candidates.append(software_target)
    added_any = False
    for field in m2m_fields:
        remote_model = getattr(field.remote_field, "model", None)
        if remote_model is None:
            continue
        instance = next((c for c in candidates if isinstance(c, remote_model)), None)
        if instance is None:
            continue
        if not commit:
            self.logger.info(
                f"[Dry-run] Would add software '{getattr(instance, 'version', str(instance))}' to CVE {getattr(cve_obj, 'name', '?')} via field '{field.name}'"
            )
            added_any = True
            continue
        try:
            getattr(cve_obj, field.name).add(instance)
            self.logger.info(
                f"Added software '{getattr(instance, 'version', str(instance))}' to CVE {cve_obj.name} (field '{field.name}')"
            )
            added_any = True
        except Exception as exc:
            self.logger.warning(f"Failed to add affected software on CVE {cve_obj.name} via '{field.name}': {exc}")
    if not added_any:
        self.logger.info(f"No compatible 'Affected Software' target type on CVE {getattr(cve_obj, 'name', '?')}.")
```
#### What's Happening?
Links a CVE to affected software via M2M fields on the CVE model. Inspects fields, selects compatible candidates (sv_lcm or software_target), and adds relations—with dry-run previews.Supports reporting and automation by tying CVEs to software versions.

#### Caveats
*   Handles multiple M2M fields; idempotent adds.
    
*   Prioritizes sv_lcm in candidates.
   
### HardwareLCM Helpers (EoX)
```python
def _hardware_part_field_name(self) -> str | None:
    if not HAS_HARDWARE_LCM:
        return None
    field_names = {f.name for f in HardwareLCM._meta.get_fields()}
    for candidate in ("inventory_item_part_id", "part_number", "part_id", "inventory_part_id"):
        if candidate in field_names:
            return candidate
    return None
def _hardware_date_field_map(self) -> dict:
    # Map our canonical names to actual model fields (if present)
    if not HAS_HARDWARE_LCM:
        return {}
    field_names = {f.name for f in HardwareLCM._meta.get_fields()}
    mapping = {}
    mapping["release_date"] = "release_date" if "release_date" in field_names else None
    mapping["end_of_sale"] = "end_of_sale" if "end_of_sale" in field_names else None
    mapping["end_of_support"] = "end_of_support" if "end_of_support" in field_names else None
    mapping["end_of_sw_releases"] = "end_of_sw_releases" if "end_of_sw_releases" in field_names else None
    mapping["end_of_security_patches"] = "end_of_security_patches" if "end_of_security_patches" in field_names else None
    mapping["documentation_url"] = "documentation_url" if "documentation_url" in field_names else None
    mapping["comments"] = "comments" if "comments" in field_names else None
    return mapping
@staticmethod
def _parse_any_date(value) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    s = str(value).strip()
    # Try ISO
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except Exception:
        pass
    # Common formats from Cisco EoX
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%d-%b-%Y", "%b %d, %Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            continue
    # Extract YYYY-MM-DD substring
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except Exception:
            pass
    return None
def _eox_record_to_hardware_fields(self, record: dict) -> dict:
    """Map Cisco EoX fields to our HardwareLCM canonical dict."""
    # Cisco fields of interest:
    # EOXExternalAnnouncementDate, EndOfSaleDate, EndOfSWMaintenanceReleases,
    # EndOfSecurityVulSupportDate, LastDateOfSupport, LinkToProductBulletinURL (EOXExternalURL)
    return {
        "release_date": self._parse_any_date(record.get("EOXExternalAnnouncementDate")),
        "end_of_sale": self._parse_any_date(record.get("EndOfSaleDate")),
        "end_of_support": self._parse_any_date(record.get("LastDateOfSupport")),
        "end_of_sw_releases": self._parse_any_date(record.get("EndOfSWMaintenanceReleases")),
        "end_of_security_patches": self._parse_any_date(record.get("EndOfSecurityVulSupportDate")),
        "documentation_url": record.get("LinkToProductBulletinURL") or record.get("EOXExternalURL") or "",
        "comments": record.get("BulletinNumber") or "",
    }
```
#### What's Happening?
These normalize Cisco EoX data into HardwareLCM, handling schema variations:
*   _hardware_part_field_name: Discovers part identifier field.
    
*   _hardware_date_field_map: Maps canonical keys to model fields.
    
*   _parse_any_date: Robustly parses varied date formats.
    
*   _eox_record_to_hardware_fields: Transforms EoX record to canonical dict.
    
Gates on HAS_HARDWARE_LCM for graceful no-ops if unavailable.
#### Caveats
*   Preference order for fields; adjust if multiples exist.
    
*   Date parsing is permissive but not exhaustive—test unusual formats.

### Discovery via NAPALM -> SoftwareLCM
```python
def _get_or_create_software_lcm(self, platform: Platform, version: str, commit: bool) -> SoftwareLCM | SimpleNamespace | None:
    if not commit:
        exists = SoftwareLCM.objects.filter(device_platform=platform, version=version).exists()
        if exists:
            self.logger.info(f"[Dry-run] Would use existing SoftwareLCM '{version}' for platform '{platform.name}'")
        else:
            self.logger.info(f"[Dry-run] Would create SoftwareLCM '{version}' for platform '{platform.name}'")
        return SimpleNamespace(id=None, version=version, device_platform=platform)
    try:
        obj, created = SoftwareLCM.objects.get_or_create(
            device_platform=platform,
            version=version,
            defaults={"alias": version},
        )
        self.logger.info(f"{'Created' if created else 'Found'} SoftwareLCM '{version}' for platform '{platform.name}'")
        return obj
    except Exception as exc:
        self.logger.warning(f"Failed to get_or_create SoftwareLCM ({platform.name}, {version}): {exc}")
        return None
def discover_software(self, device: Device, group: SecretsGroup, commit: bool) -> SoftwareLCM | SimpleNamespace | None:
    if not device.platform:
        self.logger.warning(f"{device.name}: No platform set; skipping discovery.")
        return None
    driver_name = self._platform_to_napalm_driver(device.platform)
    if not driver_name:
        self.logger.warning(f"{device.name}: Unsupported platform for NAPALM; skipping.")
        return None
    # Pass device as obj so Secrets backends that scope by object can resolve properly
    username, password = self._get_net_credentials(group, obj=device)
    if not username or not password:
        return None
    host = self._device_host(device)
    try:
        driver = get_network_driver(driver_name)
        conn = driver(hostname=host, username=username, password=password, optional_args={})
        conn.open()
        try:
            facts = conn.get_facts()
        finally:
            try:
                conn.close()
            except Exception:
                pass
    except Exception as exc:
        self.logger.warning(f"{device.name}: NAPALM connection/get_facts failed: {exc}")
        return None
    raw_version = (facts or {}).get("os_version") or ""
    version_token = self._extract_version_token(raw_version)
    if not version_token:
        self.logger.warning(f"{device.name}: Could not parse a clean version from '{raw_version}'")
        return None
    sv_lcm = self._get_or_create_software_lcm(device.platform, version_token, commit=commit)
    if sv_lcm and version_token != raw_version.strip():
        self.logger.info(f"{device.name}: Normalized discovered version to '{version_token}' (from '{raw_version}')")
    return sv_lcm
```
#### What's Happening?
Connects via NAPALM, extracts/normalizes OS version, and creates/links SoftwareLCM—with dry-run support.
*   _get_or_create_software_lcm: Handles DB ops or simulation.
    
*   discover_software: Full flow from connection to normalized record.
    
Bridges live data to persisted records for CVE linking.

#### Caveats
*   Skips on missing platform/driver/credentials.
    
*   Dry-run uses placeholders for simulation.

## Conclusion
With these standardized helpers for connections, normalization, and schema adaptation, we eliminate brittle code and minimize errors. Dry-run mode enables safe previews, while runtime introspection ensures compatibility across setups. Hardware EoX handling makes lifecycle data as seamless as software vulns.T

he outcome? A scalable pipeline from device facts to linked CVEs and lifecycle info—vendor-agnostic and extensible. Next week, we'll integrate Cisco's PSIRT API, parse advisories (dates, CVSS), and persist everything in Nautobot for end-to-end automation.