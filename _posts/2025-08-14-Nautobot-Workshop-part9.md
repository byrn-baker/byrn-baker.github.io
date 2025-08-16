---
title: Nautobot Workshop Blog Series - Part 9 - Nautobot Golden Configuration - Practical Configuration Compliance
date: 2025-08-14 09:00:00
categories: [Nautobot, Ansible, Automation]
tags: [NetworkAutomation, NetworkSourceOfTruth, nautobot, AutomationPlatform, NautobotTutorials]
image:
  path: /assets/img/nautobot_workshop/light_title_image-50.webp
---

## Nautobot Workshop Blog Series - Part 9 - Nautobot Golden Configuration: Configuration Compliance
<div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
  <iframe src="https://www.youtube.com/embed/v2KgkAlu7b0" 
          frameborder="0" 
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
          allowfullscreen 
          style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
  </iframe>
</div>

[▶️ Watch the video](https://youtube.com/shorts/v2KgkAlu7b0)

In the realm of network automation, configuration compliance serves as a foundational pillar, ensuring alignment between the intended device configurations—derived from templated sources and authoritative data repositories—and the operational state of network devices. This alignment is paramount for maintaining network reliability, security, and operational efficiency.This installment delves into the practical implications of configuration compliance, elucidates common pitfalls leading to non-compliance, outlines the setup and execution of compliance jobs within Nautobot, and imparts best practices to integrate compliance seamlessly into your network operations framework.

## The Essence of Configuration Compliance in Network Automation
Fundamentally, configuration compliance entails a rigorous comparison between two artifacts:
- **Intended Configuration**: This is synthesized through automation pipelines, typically by rendering structured data from a source-of-truth (SoT) system like Nautobot against Jinja2 templates to produce device-specific configurations.
- **Actual Configuration**: This represents the live running configuration extracted from the device and archived in a backup repository.

The compliance engine enforces a stringent line-by-line exact match criterion. For instance, abbreviations such as ```int g0/0``` versus the expanded``` interface GigabitEthernet0/0``` are deemed incongruent, despite semantic equivalence. This uncompromising precision is essential for automated systems to detect deviations with high fidelity, mitigating risks associated with subtle discrepancies.

## Prevalent Causes of Compliance Failures
Non-compliance can arise from a multitude of factors, often rooted in operational, data, or tooling inconsistencies:
1. **Omitted Configuration Elements**: Templates may fail to generate requisite lines due to incomplete logic, or manual interventions might excise critical segments.
2. **Superfluous Configuration**: Manual overrides, residual legacy artifacts, or ad-hoc troubleshooting remnants frequently introduce extraneous elements.
3. **Stale Source-of-Truth Data**: Discrepancies in Nautobot's inventory or device metadata can yield mismatched intended configurations.
4. **Template Anomalies**: Syntactic errors, logical flaws, or inconsistencies in Jinja2 templates may propagate erroneous outputs.
5. **Backup and Parsing Artifacts**: Imperfections in configuration retrieval tools or platform-specific idiosyncrasies can induce false positives during parsing.

Notably, the compliance mechanism operates agnostically, flagging any textual divergence without inferring contextual intent or applying remedial transformations.

## Configuring and Executing Compliance Assessments in Nautobot
To operationalize configuration compliance in Nautobot, prerequisite components include:
- A Git repository housing intended configurations, dynamically generated from Nautobot's SoT data and associated templates.
- A complementary Git repository for device backups, populated with periodically harvested running configurations.
- Properly defined ```intended_path_template``` and ```backup_path_template``` parameters within the Golden Config application settings to reference these repositories accurately.

With these in place, proceed as follows:
1. Access the **Golden Config → Home** interface in Nautobot.
2. Initiate the process via the Execute button, selecting Compliance.
3. Specify the target devices or scope for evaluation.
4. Execute the job and scrutinize the resultant compliance report.

## Establishing Compliance Rules
Compliance rules delineate the comparative scope, typically segmented by platform and functional domain—e.g., interface configurations on IOS or BGP peering on EOS.
- Assign a concise, descriptive feature name to facilitate intuitive dashboard interpretation.
- Define the Config to Match anchor: For CLI-based configurations, this specifies prefix strings; for JSON formats, it identifies root keys.
- Associate the rule with a supported platform network driver.
- Circumscribe the comparison to pertinent configuration subsections.

<img src="/assets/img/nautobot_workshop/compliance-features.webp" alt="Compliance Features">
<img src="/assets/img/nautobot_workshop/compliance-rules.webp" alt="Compliance Rules">

Adopt an incremental approach: Prioritize mission-critical sections and progressively broaden rule coverage.

## Best Practices and Insights from Implementation
- **Meticulous Failure Analysis**: Differentiate genuine issues from artifacts like parser quirks or data obsolescence; avoid precipitous remediation.
- **Iterative Refinement**: Leverage compliance outcomes to enhance templates and SoT data integrity.
- **Detection Over Correction**: Compliance tools identify variances but defer resolution to orchestrated human or automated processes.
- **Scoped Evaluations**: Employ tags or groupings to tailor checks in heterogeneous, multi-vendor topologies.
- **Routine Scheduling**: Automate periodic executions to preemptively detect configuration drift.
- **Visualization Leverage**: Utilize dashboards and per-device views for actionable insights into compliance trends.

## Illustrative Compliance Scenarios
Assuming a fully configured environment, consider a compliance report highlighting failures in Interface and BGP rules across multiple routers. Focusing on device CE1, navigation to its detailed view reveals granular non-compliance details.
<img src="/assets/img/nautobot_workshop/compliance-report.webp" alt="Compliance Report Overview">

Examining the INTF rule exposes subtle mismatches. A side-by-side diff (e.g., via VS Code) of backup and intended configurations elucidates these:
<img src="/assets/img/nautobot_workshop/compliance-not-compliant.webp" alt="Non-Compliant Status">
<img src="/assets/img/nautobot_workshop/compliance-interfaces.webp" alt="Interface Compliance Details">

Key discrepancies include the absence of ```no shutdown``` in the backup, capitalization variances in IPv6 addresses (e.g., Cisco's uppercase rendering), and omission of the loopback interface in the intended config—necessitating template scrutiny. These textual mismatches precipitate compliance failure.
<img src="/assets/img/nautobot_workshop/compliance-diff.webp" alt="Configuration Diff">

## Integrating Compliance into NetDevOps Pipelines
Configuration compliance functions as a sentinel within NetDevOps workflows, validating the fidelity of SoT-driven configurations against deployed states.
- Trigger notifications or remediation pipelines based on compliance metrics.
- Correlate compliance data with change management and audit trails for comprehensive traceability.
- Embed compliance gates in CI/CD pipelines to intercept anomalies pre-deployment.

## Conclusion
Configuration compliance transcends mere functionality; it embodies a rigorous discipline that fortifies network assurance through exacting standards. By meticulously curating compliance rules, enforcing regular assessments, and harnessing insights for perpetual enhancement, Nautobot's Golden Config empowers practitioners to sustain impeccable network congruence.

Project artifacts for this series are accessible via the associated GitHub repository.

Next week we will dive into Config Remediation and Custom Compliance.