---
title: Nautobot Workshop Blog Series - Part 16 - Nautobot Device Lifecycle Management - Part 3
date: 2025-10-02 0:00:00
categories: [Nautobot, Ansible, Automation]
tags: [NetworkAutomation, NetworkSourceOfTruth, nautobot, AutomationPlatform, NautobotTutorials]
image:
  path: /assets/img/nautobot_workshop/light_title_image-50.webp
---

# From Live Advisories to Persisted CVEs: Cisco PSIRT, Arista, and EoX
This week we wire the pipeline into real vendor sources. You’ll see how the job authenticates to Cisco PSIRT, maps OS versions to what Cisco expects, scrapes Arista advisories, normalizes dates and CVSS, and finally persists CVEs and Vulnerabilities in Nautobot’s DLM models. We’ll also pull Cisco EoX (hardware lifecycle) for devices and tie it all together with a run() orchestration that supports dry-run safely.

> Pulling the Cisco EoX API has been difficult to figure out what Credentials are required for this, so for now it doesn't work because the API calls are failing.
{: .prompt-tip }

## Cisco PSIRT OAuth: Getting a Token
```python
def get_cisco_token(self) -> str | None:
    client_id, client_secret = self._get_cisco_credentials()
    if not client_id or not client_secret:
        self.logger.warning("Missing Cisco API credentials in env: CISCO_CLIENT_ID and CISCO_CLIENT_SECRET.")
        return None

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    okta_url = "https://id.cisco.com/oauth2/default/v1/token"
    for data in (
        {"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret, "audience": "https://api.cisco.com"},
        {"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
    ):
        try:
            r = requests.post(okta_url, data=data, headers=headers, timeout=30)
            if r.ok:
                token = r.json().get("access_token")
                if token:
                    return token
            else:
                self.logger.warning(f"Cisco token (Okta) attempt failed: {r.status_code} {r.text[:200]}")
        except Exception as exc:
            self.logger.warning(f"Cisco token request error (Okta): {exc}")

    legacy_url = "https://cloudsso.cisco.com/as/token.oauth2"
    try:
        r = requests.post(legacy_url, data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret}, headers=headers, timeout=30)
        if r.ok:
            token = r.json().get("access_token")
            if token:
                return token
        else:
            self.logger.warning(f"Cisco token fetch failed (legacy): {r.status_code} {r.text[:200]}")
    except Exception as exc:
        self.logger.warning(f"Cisco token request error (legacy): {exc}")
    return None
```

get_cisco_token negotiates a bearer token using Cisco’s Okta OAuth endpoint, then falls back to the legacy CloudSSO if needed.
- Tries Okta first (id.cisco.com/oauth2/default/v1/token), with and without an audience param.
- Falls back to legacy (cloudsso.cisco.com/as/token.oauth2) as a last resort.
- Uses environment-provided credentials (CISCO_CLIENT_ID, CISCO_CLIENT_SECRET).
- Logs partial response text on failure for debugging (first 200 chars).

### What’s Happening?
- The method posts x-www-form-urlencoded credentials for grant_type=client_credentials.
- Any working response yields an access_token string.
- Errors are non-fatal; the job continues without Cisco data if token retrieval fails.

### Caveats
- Make sure the credentials are valid and have PSIRT API access enabled in your Cisco developer account.
- Timeouts are set to 30s; adjust if your environment is proxy-constrained.
- Prefer Okta; legacy endpoint remains as compatibility fallback.

## Mapping Device Versions to Cisco’s Expected Versions
```python
@staticmethod
  def _parse_version_tuple(version_text: str) -> tuple[int | None, int | None, int | None]:
      s = version_text.strip()
      m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", s)
      if not m:
          return (None, None, None)
      major = int(m.group(1))
      minor = int(m.group(2))
      patch = int(m.group(3)) if m.group(3) else None
      if patch is None:
          m2 = re.search(r"\(\s*(\d+)\s*\)", s)
          if m2:
              patch = int(m2.group(1))
      return (major, minor, patch)

  @staticmethod
  def _parse_available_version_tuple(v: str) -> tuple[int | None, int | None, int | None]:
      m = re.match(r"^\s*(\d+)\.(\d+)(?:\.\s*(\d+))?", v.strip())
      if not m:
          m = re.match(r"^\s*(\d+)\.(\d+)(?:\.(\d+))?", v.strip())
      if not m:
          return (None, None, None)
      return (int(m.group(1)), int(m.group(2)), int(m.group(3)) if m.group(3) else None)

  def _select_best_available_version(self, desired: tuple[int | None, int | None, int | None], available: list[str]) -> str | None:
      dmaj, dmin, dpat = desired
      if dmaj is None or dmin is None:
          return None
      candidates = []
      for v in available:
          maj, minr, pat = self._parse_available_version_tuple(v)
          if maj == dmaj and minr == dmin:
              candidates.append((pat if pat is not None else -1, v))
      if not candidates:
          return None
      if dpat is not None:
          exacts = [v for (p, v) in candidates if p == dpat]
          if exacts:
              return sorted(exacts)[-1]
      candidates.sort(key=lambda x: (x[0], x[1]))
      return candidates[-1][1]

  def _get_cisco_versions(self, token: str, ostype: str) -> list[str]:
      if not hasattr(self, "_cisco_versions_cache"):
          self._cisco_versions_cache = {}
      if ostype in self._cisco_versions_cache:
          return self._cisco_versions_cache[ostype]
      url = "https://apix.cisco.com/security/advisories/v2/OS_version/OS_data"
      headers = {"Authorization": f"Bearer {token}", "Accept": "application/json", "User-Agent": "nautobot-vendor-cve-job"}
      versions = set()
      try:
          resp = requests.get(url, headers=headers, params={"OSType": ostype}, timeout=30)
          resp.raise_for_status()
          data = resp.json()
      except Exception as exc:
          self._cisco_versions_cache[ostype] = []
          self.logger.warning(f"Cisco OS_version list request error for {ostype}: {exc}")
          return []
      def _walk(x):
          if isinstance(x, str):
              if re.match(r"^\d+\.\d+(?:\.\d+)?[A-Za-z0-9.\-()]*$", x):
                  versions.add(x)
          elif isinstance(x, list):
              for y in x:
                  _walk(y)
          elif isinstance(x, dict):
              for v in x.values():
                  _walk(v)
      _walk(data)
      sorted_versions = sorted(
          versions,
          key=lambda vs: (
              tuple(val if val is not None else -1 for val in self._parse_available_version_tuple(vs)),
              vs,
          )
      )
      self._cisco_versions_cache[ostype] = sorted_versions
      return sorted_versions

  def _map_version_for_cisco(self, token: str, ostype: str, sw_version: str) -> tuple[str | None, str]:
      desired = self._parse_version_tuple(sw_version)
      versions = self._get_cisco_versions(token, ostype)
      best = self._select_best_available_version(desired, versions)
      if best:
          return best, f"Mapped device '{sw_version}' -> '{best}' for OSType {ostype}"
      dmaj, dmin, _ = desired
      if dmaj is not None and dmin is not None:
          fallback = f"{dmaj}.{dmin}"
          return fallback, f"No exact {dmaj}.{dmin}.* match found. Falling back to '{fallback}' for OSType {ostype}"
      return None, "Could not parse a usable version from device; skipping Cisco query."
```

Cisco’s API requires versions formatted exactly as Cisco enumerates them per OSType (e.g., iosxe). These helpers normalize device-reported versions to the “closest” Cisco-recognized value.

### key pieces:
- _parse_version_tuple: Pulls major, minor, and a patch-like number. For Cisco IOS “parentheses” releases (e.g., 12.2(55)), it treats the number in parentheses as patch if no - dotted patch exists.
- _get_cisco_versions: Calls OS_version/OS_data and walks the returned JSON to collect all version strings Cisco recognizes for that OSType. Results are cached per OSType for - reuse.
- _select_best_available_version: Given a desired (major, minor, patch) and a list of available strings, picks the best candidate:
  - Only considers same major.minor.
  - Prefers an exact patch match. If none, chooses the highest patch in that branch.
- _map_version_for_cisco: Orchestrates the above:
  - Returns the selected best match.
  - If none found, falls back to “major.minor” (e.g., 16.12).
  - Logs a human-readable mapping message for transparency.

### Caveats
- Version parsing is heuristic; weird strings can slip through. The code errors on being permissive, then degrades to major.minor.
- The OS_version/OS_data endpoint is a “catalog” of acceptable versions, not advisories; we use it to avoid 404s and mismatches later.
- Maintain a consistent User-Agent and caching to reduce rate-limit exposure.

## Cisco Advisories: Pulling CVEs By OSType + Version
```python
def pull_cisco_cves(self, software: SoftwareLCM | SimpleNamespace, device: Device) -> list[dict]:
    token = self.get_cisco_token()
    if not token:
        return []
    ostype = self._map_platform_to_cisco_ostype(device)
    if not ostype:
        self.logger.info(f"{device.name}: Platform '{device.platform.name if device.platform else ''}' not mapped to a Cisco OSType; skipping Cisco PSIRT.")
        return []
    mapped_version, mapping_msg = self._map_version_for_cisco(token, ostype, software.version)
    if not mapped_version:
        self.logger.warning(f"{device.name}: {mapping_msg}")
        return []
    self.logger.info(f"{device.name}: {mapping_msg}")

    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json", "User-Agent": "nautobot-vendor-cve-job"}
    base_url = f"https://apix.cisco.com/security/advisories/v2/OSType/{ostype}"
    try:
        resp = requests.get(base_url, headers=headers, params={"version": mapped_version}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        self.logger.warning(f"Cisco API v2 failed ({ostype}, v={mapped_version}): {exc}")
        return []
    advisories = data.get("advisories", []) or []
    self.logger.info(f"Cisco API v2 returned {len(advisories)} advisories for {device.name} ({ostype} v={mapped_version}).")
    return advisories
```

pull_cisco_cves drives the PSIRT call once we have a token, an OSType (e.g., iosxe), and a mapped version.

### What’s Happening?
- OSType is derived from platform via last week’s _map_platform_to_cisco_ostype helper.
- Version is mapped through the logic above to Cisco’s expectation.
- Calls https://apix.cisco.com/security/advisories/v2/OSType/{ostype}?version= ...
- Returns a list of advisory dictionaries (data["advisories"]) and logs the count.

### Caveats
- If platform isn’t Cisco-like, or token fails, it returns an empty list cleanly.
- Network and API errors are caught and logged; the job continues on other devices.

## Arista Advisories: Lightweight Scrape
```python
def pull_arista_cves(self, software: SoftwareLCM | SimpleNamespace) -> list[dict]:
    url = "https://www.arista.com/en/support/advisories-notices/security-advisories"
    try:
        resp = requests.get(url, headers={"User-Agent": "nautobot-vendor-cve-job"}, timeout=30)
        if not resp.ok:
            self.logger.warning(f"Arista scrape failed: {resp.status_code}")
            return []
    except Exception as exc:
        self.logger.warning(f"Arista advisories request error: {exc}")
        return []
    soup = BeautifulSoup(resp.text, "lxml")
    advisories = []
    for item in soup.select(".advisory-item, .item, article, li"):
        title_el = item.find(["h2", "h3", "a"])
        para_el = item.find("p")
        title = title_el.get_text(strip=True) if title_el else ""
        desc = para_el.get_text(strip=True) if para_el else ""
        text = f"{title}\n{desc}"
        if software.version in text:
            cve_ids = set(re.findall(r"CVE-\d{4}-\d{4,7}", text))
            for cve_id in cve_ids:
                advisories.append(
                    {
                        "advisoryIdentifier": cve_id,
                        "summary": title or desc or "Arista security advisory",
                        "cves": [cve_id],
                        "publicationUrl": url,
                        "firstPublished": None,
                        "lastUpdated": None,
                        "severity": "Unknown",
                    }
                )
    return advisories
```

Arista doesn’t provide a comparable JSON API, so pull_arista_cves performs a simple, targeted scrape.

### What’s Happening?
- Downloads https://www.arista.com/en/support/advisories-notices/security-advisories.
- Parses the page with BeautifulSoup and scans item-like elements for text blobs.
- If the discovered software.version appears in the text, extracts CVE IDs with a regex.
- Returns advisories that look similar to the Cisco schema (advisoryIdentifier, summary, cves, etc.) so downstream code can be vendor-agnostic.

### Caveats
- This is intentionally conservative to avoid false positives. It may miss advisories that don’t spell out the version plainly.
- HTML structure can change; keep an eye on selectors.
- Treats severity and dates as unknown when not present; enrichment can fill gaps later.

## Dates: Normalizing Published and Last-Modified
```python
def _extract_date_from_keys(self, advisory: dict, keys: list[str], default: date | None = None) -> date | None:
    value = None
    for key in keys:
        if key in advisory and advisory[key]:
            value = advisory[key]
            break
    if isinstance(value, str):
        s = value.strip()
        try:
            s2 = s.replace("Z", "+00:00")
            dt = datetime.fromisoformat(s2)
            return dt.date()
        except Exception:
            pass
    # try common formats and substrings
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%d-%b-%Y", "%b %d, %Y"):
        try:
            return datetime.strptime(str(value), fmt).date()
        except Exception:
            continue
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", str(value or ""))
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except Exception:
            pass
    return default

def _extract_published_date(self, advisory: dict) -> date:
    d = self._extract_date_from_keys(
        advisory,
        ["firstPublished", "firstPublishedDate", "publicationDate", "advisoryPublicationDate", "published"],
        default=None,
    )
    return d or date.today()

def _extract_last_modified_date(self, advisory: dict, fallback: date | None) -> date | None:
    d = self._extract_date_from_keys(
        advisory,
        ["lastUpdated", "lastModified", "lastModifiedDate", "advisoryLastUpdatedDate"],
        default=None,
    )
    return d or fallback
```

APIs and scrapes return dates in many shapes. These helpers standardize for DLM fields.
- _extract_date_from_keys: Given an advisory and a list of candidate keys, tries to parse ISO and several common formats; also scans for YYYY-MM-DD substrings.
- _extract_published_date: Prefers keys like firstPublished; defaults to today if none found.
- _extract_last_modified_date: Prefers lastUpdated-style keys; defaults to the published date.

### Caveats
- Parsing is best-effort; unexpected formats will fall back cleanly.
- If you need timezone-aware storage, adapt before assignment.

## CVSS: Pulling v2, v3, and Base Scores
```python
@staticmethod
def _to_float(val) -> float | None:
    try:
        return float(val)
    except Exception:
        return None

def _extract_cvss_for_cve(self, advisory: dict, cve_id: str) -> tuple[float | None, float | None, float | None]:
    cvss_base = cvss_v2 = cvss_v3 = None
    if isinstance(advisory.get("cve"), list):
        for c in advisory["cve"]:
            if isinstance(c, dict) and c.get("id") == cve_id:
                for k in ["cvssBaseScore", "baseScore", "cvss_score", "cvss"]:
                    val = c.get(k)
                    if isinstance(val, dict) and "baseScore" in val:
                        cvss_base = self._to_float(val["baseScore"]) or cvss_base
                    else:
                        cvss_base = self._to_float(val) or cvss_base
                for k in ["cvssV3BaseScore", "cvss_v3", "cvssV3"]:
                    val = c.get(k)
                    if isinstance(val, dict) and "baseScore" in val:
                        cvss_v3 = self._to_float(val["baseScore"]) or cvss_v3
                    else:
                        cvss_v3 = self._to_float(val) or cvss_v3
                for k in ["cvssV2BaseScore", "cvss_v2", "cvssV2"]:
                    val = c.get(k)
                    if isinstance(val, dict) and "baseScore" in val:
                        cvss_v2 = self._to_float(val["baseScore"]) or cvss_v2
                    else:
                        cvss_v2 = self._to_float(val) or cvss_v2
                break
    if cvss_base is None:
        for k in ["cvssBaseScore", "baseScore", "cvss_score", "cvss"]:
            val = advisory.get(k)
            if isinstance(val, dict) and "baseScore" in val:
                cvss_base = self._to_float(val["baseScore"])
            else:
                cvss_base = self._to_float(val)
            if cvss_base is not None:
                break
    if cvss_v3 is None:
        for k in ["cvssV3BaseScore", "cvss_v3", "cvssV3"]:
            val = advisory.get(k)
            if isinstance(val, dict) and "baseScore" in val:
                cvss_v3 = self._to_float(val["baseScore"])
            else:
                cvss_v3 = self._to_float(val)
            if cvss_v3 is not None:
                break
    if cvss_v2 is None:
        for k in ["cvssV2BaseScore", "cvss_v2", "cvssV2"]:
            val = advisory.get(k)
            if isinstance(val, dict) and "baseScore" in val:
                cvss_v2 = self._to_float(val["baseScore"])
            else:
                cvss_v2 = self._to_float(val)
            if cvss_v2 is not None:
                break
    if cvss_base is None:
        cvss_base = cvss_v3 if cvss_v3 is not None else cvss_v2
    return cvss_base, cvss_v2, cvss_v3
```

Vendors may place CVSS at different nesting levels.
- _extract_cvss_for_cve checks for a specific CVE within an “advisory.cve” list first, then falls back to top-level fields.
- Accepts numbers or dicts like {"baseScore": 8.8}.
- Returns (cvss_base, cvss_v2, cvss_v3), using v3 or v2 as the base if an explicit base is absent.

### Caveats
- Some advisories provide only qualitative severities; numeric CVSS will be None.
- This method is resilient by design—unknown shapes won’t break the job.

## Persistence: CVEs, Vulnerabilities, and Affected Software
```python
def _get_status_for_model(self, model, candidates: list[str]) -> Status | None:
    try:
        qs = Status.objects.get_for_model(model)
        for name in candidates:
            s = qs.filter(name__iexact=name).first()
            if s:
                return s
        return qs.first() if qs.exists() else None
    except Exception:
        return None

def create_cves_and_vulns_for_software(
    self,
    advisories: list[dict],
    sv_lcm: SoftwareLCM | SimpleNamespace,
    vendor: str,
    commit: bool,
):
    """Create/update CVEs and Vulnerabilities for the given software; associate Affected Software, not platform."""
    if not advisories:
        return

    open_status = self._get_status_for_model(VulnerabilityLCM, ["Open", "Active"]) if commit else None
    cve_status_default = self._get_status_for_model(CVELCM, ["Active", "Published"]) if commit else None

    software_target = self._resolve_software_instance_for_vuln(sv_lcm, commit=commit)
    if commit and software_target is None:
        self.logger.warning("Cannot resolve suitable software instance for VulnerabilityLCM.software; skipping vulnerability creation.")
    if not commit and software_target is None:
        self.logger.info("[Dry-run] Would link vulnerability to resolved software instance (skipped FK resolution).")

    created_cves = 0
    created_vulns = 0

    for adv in advisories:
        cve_ids = []
        if isinstance(adv.get("cves"), list):
            cve_ids = [c for c in adv["cves"] if isinstance(c, str)]
        elif isinstance(adv.get("cve"), list):
            cve_ids = [c.get("id") for c in adv["cve"] if isinstance(c, dict) and c.get("id")]
        elif isinstance(adv.get("advisoryIdentifier", ""), str) and adv["advisoryIdentifier"].startswith("CVE-"):
            cve_ids = [adv["advisoryIdentifier"]]

        description = adv.get("summary") or adv.get("advisoryTitle") or ""
        link = adv.get("publicationUrl") or adv.get("url") or ""
        severity = adv.get("severity") or adv.get("sir") or ""
        published_date = self._extract_published_date(adv)
        last_modified_date = self._extract_last_modified_date(adv, fallback=published_date)

        for cve_id in set(filter(None, cve_ids)):
            cvss_base, cvss_v2, cvss_v3 = self._extract_cvss_for_cve(adv, cve_id)

            if not commit:
                exists = CVELCM.objects.filter(name=cve_id).exists()
                self.logger.info(
                    f"[Dry-run] Would {'update' if exists else 'create'} CVE {cve_id} with "
                    f"published_date={published_date}, last_modified_date={last_modified_date}, link={link or '-'}, "
                    f"severity={severity or '-'}, cvss={cvss_base}, cvss_v2={cvss_v2}, cvss_v3={cvss_v3}, "
                    f"status={(adv.get('status') or getattr(cve_status_default, 'name', '')) or '-'}; "
                    f"and {'ensure' if exists else 'create'} Vulnerability (software='{getattr(sv_lcm, 'version', '?')}'), "
                    f"plus associate CVE->Affected Software."
                )
                self._associate_cve_with_affected_software(
                    cve_obj=SimpleNamespace(name=cve_id, _meta=CVELCM._meta),
                    sv_lcm=sv_lcm,
                    software_target=software_target,
                    commit=False,
                )
                continue

            try:
                cve_status_obj = None
                adv_status_name = adv.get("status")
                if adv_status_name:
                    cve_status_obj = self._get_status_for_model(CVELCM, [str(adv_status_name)])
                if not cve_status_obj:
                    cve_status_obj = cve_status_default

                defaults = {
                    "published_date": published_date,
                    "last_modified_date": last_modified_date,
                    "severity": severity or "",
                    "cvss": cvss_base,
                    "cvss_v2": cvss_v2,
                    "cvss_v3": cvss_v3,
                    "status": cve_status_obj,
                }
                if description:
                    defaults["description"] = description[:1024]
                if link:
                    defaults["link"] = link

                cve_obj, created = CVELCM.objects.get_or_create(name=cve_id, defaults=defaults)
                if created:
                    created_cves += 1
                    self.logger.info(f"Created CVE {cve_id} from {vendor}")
                else:
                    patch_needed = False
                    if not getattr(cve_obj, "published_date", None):
                        cve_obj.published_date = published_date
                        patch_needed = True
                    if last_modified_date and not getattr(cve_obj, "last_modified_date", None):
                        cve_obj.last_modified_date = last_modified_date
                        patch_needed = True
                    if link and not getattr(cve_obj, "link", ""):
                        cve_obj.link = link
                        patch_needed = True
                    if description and not getattr(cve_obj, "description", ""):
                        cve_obj.description = description[:1024]
                        patch_needed = True
                    if severity and not getattr(cve_obj, "severity", ""):
                        cve_obj.severity = severity
                        patch_needed = True
                    if cvss_base is not None and getattr(cve_obj, "cvss", None) in (None, 0):
                        cve_obj.cvss = cvss_base
                        patch_needed = True
                    if cvss_v2 is not None and getattr(cve_obj, "cvss_v2", None) in (None, 0):
                        cve_obj.cvss_v2 = cvss_v2
                        patch_needed = True
                    if cvss_v3 is not None and getattr(cve_obj, "cvss_v3", None) in (None, 0):
                        cve_obj.cvss_v3 = cvss_v3
                        patch_needed = True
                    if cve_status_obj and not getattr(cve_obj, "status", None):
                        cve_obj.status = cve_status_obj
                        patch_needed = True
                    if patch_needed:
                        cve_obj.save()

                # Associate "Affected Software" on the CVE when supported
                self._associate_cve_with_affected_software(
                    cve_obj=cve_obj,
                    sv_lcm=sv_lcm,
                    software_target=software_target,
                    commit=True,
                )

                if software_target is None:
                    continue

                vuln_defaults = {}
                if open_status:
                    vuln_defaults["status"] = open_status

                vuln, v_created = VulnerabilityLCM.objects.get_or_create(
                    cve=cve_obj,
                    software=software_target,
                    defaults=vuln_defaults,
                )
                if v_created:
                    created_vulns += 1
                    self.logger.info(
                        f"Created vulnerability {cve_id} for software {getattr(software_target, 'version', getattr(sv_lcm, 'version', '?'))}"
                    )
            except Exception as exc:
                self.logger.warning(
                    f"Failed to persist CVE/Vulnerability for {cve_id} on software {getattr(sv_lcm, 'version', '?')}: {exc}"
                )

    suffix = "[Dry-run] " if not commit else ""
    self.logger.info(
        f"{suffix}Persisted CVEs: +{created_cves}, Vulnerabilities: +{created_vulns} for software {getattr(sv_lcm, 'version', '?')}"
    )
```

create_cves_and_vulns_for_software takes a vendor’s advisories and writes them into DLM models, relying on last week’s schema-introspection helpers.

### What’s Happening?
- Resolves an appropriate software_target for VulnerabilityLCM.software, accommodating custom schemas.
- For each advisory:
  - Extracts all CVE IDs from “cves”, “cve”, or “advisoryIdentifier”.
  - Computes dates, severity, and CVSS.
  - Dry-run:
    - Logs whether it would create or update each CVE.
    - Simulates “Affected Software” M2M association.
  - Commit:
    - get_or_create CVELCM by name, with defaults for published/mod dates, link, description, severity, cvss.
    - Non-destructive updates: fills missing fields only, leaving existing populated fields intact.
    - Associates “Affected Software” via an M2M if present on the CVE model (idempotent).
    - Creates VulnerabilityLCM linking cve and software_target, with status defaulted to Open/Active when available.

### Caveats
- Status resolution is best-effort; if your Status choices differ, adjust the candidates list.
- The function is idempotent and additive—safe to re-run as advisories update over time.
- If the environment’s VulnerabilityLCM.software FK points to a custom model, linking still works via platform+version or software references.

## Cisco EoX: Hardware Lifecycle Notices
```python
def pull_cisco_eox_for_pid(self, pid: str) -> list[dict]:
    """Query Cisco EoX v5 API for a single product ID (PID)."""
    token = self.get_cisco_token()
    if not token:
        return []
    url = f"https://apix.cisco.com/supporttools/eox/rest/5/EOXByProductID/1/{pid}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json", "User-Agent": "nautobot-vendor-cve-job"}
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if not resp.ok:
            self.logger.warning(f"Cisco EoX API failed for PID={pid}: {resp.status_code} {resp.text[:200]}")
            return []
        data = resp.json() or {}
        # Records array can be under "EOXRecord" or similar top-level
        records = data.get("EOXRecord") or data.get("EOXRecords") or data.get("Records") or []
        if isinstance(records, dict):
            records = [records]
        return records
    except Exception as exc:
        self.logger.warning(f"Cisco EoX API request error for PID={pid}: {exc}")
        return []

def upsert_hardware_notice_for_device(self, device: Device, commit: bool):
    """Create/update HardwareLCM for device.device_type using its part number via Cisco EoX."""
    if not HAS_HARDWARE_LCM:
        self.logger.info("HardwareLCM not available in this DLM version; skipping hardware notices.")
        return

    if not device.device_type:
        self.logger.info(f"{device.name}: No DeviceType; skipping EoX.")
        return

    pid = getattr(device.device_type, "part_number", None) or getattr(device.device_type, "model", None)
    if not pid:
        self.logger.info(f"{device.name}: DeviceType has no part_number; skipping EoX.")
        return

    records = self.pull_cisco_eox_for_pid(pid)
    if not records:
        self.logger.info(f"{device.name}: No EoX records for PID={pid}.")
        return

    part_field = self._hardware_part_field_name()
    if not part_field:
        self.logger.info("Could not determine HardwareLCM part-number field; skipping.")
        return
    field_map = self._hardware_date_field_map()

    for rec in records:
        mapped = self._eox_record_to_hardware_fields(rec)

        # Build filter for get_or_create
        filter_kwargs = {"device_type": device.device_type, part_field: pid}

        if not commit:
            exists = HardwareLCM.objects.filter(**filter_kwargs).exists()
            action = "update" if exists else "create"
            self.logger.info(
                f"[Dry-run] Would {action} HardwareLCM for device_type='{device.device_type.model}' "
                f"part='{pid}' with dates: release={mapped['release_date']}, "
                f"eosale={mapped['end_of_sale']}, eosupport={mapped['end_of_support']}, "
                f"eosw={mapped['end_of_sw_releases']}, eosec={mapped['end_of_security_patches']}, "
                f"url={mapped['documentation_url'] or '-'}"
            )
            continue

        try:
            obj, created = HardwareLCM.objects.get_or_create(**filter_kwargs)
            # Update fields if present in model
            changed = False
            for key, model_field in field_map.items():
                if not model_field:
                    continue
                new_value = mapped.get(key)
                if new_value is None:
                    continue
                if getattr(obj, model_field, None) != new_value:
                    setattr(obj, model_field, new_value)
                    changed = True
            if changed:
                obj.save()
            self.logger.info(
                f"{'Created' if created else 'Updated'} HardwareLCM for device_type='{device.device_type.model}' part='{pid}'"
            )
        except Exception as exc:
            self.logger.warning(f"Failed to upsert HardwareLCM for {device.device_type} / {pid}: {exc}")
```

We also enrich the hardware side via Cisco’s EoX API by device type PID.
- pull_cisco_eox_for_pid: Queries EOXByProductID v5, returns Records (handles arrays and singletons).
- upsert_hardware_notice_for_device:
  - Derives the PID from DeviceType part_number or model.
  - Maps Cisco fields into our canonical HardwareLCM fields using last week’s helper map.
  - Dry-run: logs intended create/update with parsed dates.
  - Commit: get_or_create HardwareLCM by device_type and part number; updates only changed fields.

### Caveats
- Requires the optional HardwareLCM model; the code is gated by HAS_HARDWARE_LCM and no-ops otherwise.
- Dates use the same robust parsing as software.

## Orchestration: run() with Safe Dry-Run
```python
def run(self, data=None, commit=True, **kwargs):
    # Accept both legacy (data dict) and new-style keyword args
    def _param(key, default=None):
        if key in kwargs:
            return kwargs.get(key, default)
        return (data or {}).get(key, default)

    devices = _param("devices")
    secrets_group = _param("secrets_group")
    dry_run = bool(_param("dry_run", False))
    include_hw = bool(_param("include_hardware_notices", False))

    effective_commit = bool(commit) and not dry_run
    if not effective_commit:
        self.logger.info("Dry-run enabled: no changes will be written to the database.")

    if not isinstance(secrets_group, SecretsGroup):
        self.logger.error("You must choose a valid Secrets Group for credentials.")
        return

    # Devices queryset
    if devices:
        try:
            qs = devices
        except Exception:
            try:
                pks = [d.pk for d in devices]
            except Exception:
                pks = list(devices)
            qs = Device.objects.filter(pk__in=pks)
    else:
        active_status = Status.objects.get_for_model(Device).filter(name__iexact="Active").first()
        if not active_status:
            self.logger.warning("No 'Active' status found; processing all devices.")
            devices_qs = Device.objects.all()
        else:
            devices_qs = Device.objects.filter(status=active_status)
        qs = devices_qs.distinct()

    processed = 0
    for device in qs:
        plat_name = (device.platform.name or "").lower() if device.platform else ""
        is_cisco_like = any(s in plat_name for s in ("cisco", "ios", "nx", "asa"))
        is_arista_like = any(s in plat_name for s in ("arista", "eos"))

        # Software CVEs
        if is_cisco_like or is_arista_like:
            sv_lcm = self.discover_software(device, secrets_group, commit=effective_commit)
            if sv_lcm:
                if is_cisco_like:
                    advisories = self.pull_cisco_cves(sv_lcm, device)
                    self.create_cves_and_vulns_for_software(advisories, sv_lcm, vendor="Cisco", commit=effective_commit)
                if is_arista_like:
                    advisories = self.pull_arista_cves(sv_lcm)
                    self.create_cves_and_vulns_for_software(advisories, sv_lcm, vendor="Arista", commit=effective_commit)

        # Hardware notices (Cisco EoX)
        if include_hw and is_cisco_like:
            self.upsert_hardware_notice_for_device(device, commit=effective_commit)

        processed += 1

    self.logger.info(f"Processed {processed} devices. Tip: run the NIST CVE enrichment job separately for comprehensive coverage.")


register_jobs(VendorCVEDiscoveryJob)
```

The run method ties everything together, supporting both legacy data dict and keyword args.

### Flow
- Parameters:
  - devices: optional queryset/list of devices; defaults to all “Active” devices.
  - secrets_group: required, used to log into devices for discovery via NAPALM.
  - dry_run: if true, no DB writes (effective_commit = False).
  - include_hardware_notices: toggles the EoX step.
- For each device:
  - Detect “Cisco-like” or “Arista-like” via platform name.
  - Discover software version via NAPALM (last week’s discover_software).
  - Cisco-like: map version, pull PSIRT advisories, persist CVEs/Vulnerabilities.
  - Arista-like: scrape advisories, persist CVEs/Vulnerabilities.
  - If include_hardware_notices and Cisco-like: upsert EoX HardwareLCM.
- Logs a summary count and suggests running the NIST enrichment job separately for broader coverage.

### Caveats
- Requires a valid Secrets Group; the job exits early if missing.
- “Cisco-like”/“Arista-like” detection is name-based; refine if your platform names are custom.
- Dry-run is comprehensive—you get clear preview logs for create/update/link actions without touching the DB.

## Wrap-Up
At this point, the job connects to real vendor sources, maps versions correctly, normalizes data, and persists both software CVEs and hardware lifecycle notices—while remaining schema-aware and safe to dry-run. The design emphasizes:
- Normalization first: clean versions, dates, and scores to keep the DB consistent.
- Adaptability: introspection allows different DLM schemas to work out-of-the-box.
- Idempotency: re-runs enrich rather than overwrite.
Altogether, this is a concise, end-to-end example of using Nautobot fields, retrieving data from external APIs, normalizing the results, and persisting them back into Nautobot.