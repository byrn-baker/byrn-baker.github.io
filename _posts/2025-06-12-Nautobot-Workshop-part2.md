---
title: Nautobot Workshop Blog Series - Part 2 Review the Network Topology
date: 2025-06-12 9:00:00 --6
categories: [Nautobot,Ansible,Automtation]
tags: [NetworkAutomation,NetworkSourceOfTruth,nautobot,AutomationPlatform,NautobotTutorials]
image:
  path: /assets/img/nautobot_workshop/light_title_image-50.webp
---

# Nautobot Workshop Blog Series
"Nautobot Workshop" is a blog series that guides you through building a fully automated network lab using Nautobot, Containerlab, and Docker. Starting from environment setup on Ubuntu, each post will walk through deploying Nautobot with nautobot-docker-compose, modeling network topologies with Containerlab and vrnetlab-based routers, and populating Nautobot with real device data using Ansible. You'll also learn how to use Nautobot’s GraphQL API for dynamic inventory, generate device configurations with Jinja2 templates, and enforce configuration compliance using the Golden Config plugin. This series is ideal for network engineers looking to integrate source of truth, automation, and lab simulation into a streamlined workflow.

## Part 2: Review the Network Topology
<div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; height: auto;">
  <iframe src="https://www.youtube.com/embed/Hcs-D0lAFEs" 
          frameborder="0" 
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
          allowfullscreen 
          style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;">
  </iframe>
</div>

[▶️ Watch the video](https://youtu.be/Hcs-D0lAFEs)

Overview:
<img src="/assets/img/nautobot_workshop/Nautobot Workshop-Overview.webp" alt="">

In this workshop we will be working with a pared-down replication of a service provider network connecting two data centers together. This is a multi-vendor topology that includes both Cisco IOL routers (for core/MPLS) and Arista cEOS devices (for data center fabric). Using Nautobot as our Source of Truth, we will generate full configurations via Ansible for each device, establishing a core backbone using BGP, OSPF, and MPLS, while implementing a Spine-Leaf L3 Fabric in each DC that supports L3VPNs across sites.

Provider:
<img src="/assets/img/nautobot_workshop/Nautobot Workshop-Backbone.webp" alt="">
1. Core Devices:
   - RR1 (Route Reflector)
   - P1, P2, P3, P4 (Provider routers)
   - PE1, PE2, PE3 (Provider Edge routers)
   - These routers will form the MPLS-only core (AS65000), and will use:
     - OSPF as IGP
     - LDP for label distribution
     - MP-BGP for VPNv4/IPv6 route exchange (on PEs and RR)
2. MPLS Configuration Requirements:
   - OSPF must run between all P and PE routers
   - MPLS LDP must be enabled on all core links (100.0.x.x/24)
   - MP-BGP must be configured between PE routers and RR1
   - Loopbacks used for BGP peering and label binding
   - PE routers will connect to CE1/CE2 and extend VRFs
3. Interface & IP Plan:
   - IPv4: 100.0.x.x/24 used for P2P core links
   - IPv6: 2001:db8:100:x::/64 used optionally for dual-stack MPLS
   - Loopbacks: Lo0 assigned for routing/BGP identifiers

Datacenters:
1. CE & Data Center Edge:
   - CE1 connects to West-Spine01/02
   - CE2 connects to East-Spine01/02
   - These are where L3VPN instances terminate and redistribute into the DC fabric
2. Spine-Leaf Architecture (Arista) — eBGP Clos Fabric with MPLS L3VPN Backhaul
   - Each data center (East and West) uses a Layer 3 Spine-Leaf Clos fabric built on Arista cEOS switches
   - All Leaf and Spine switches run eBGP with distinct ASNs per device
   - Leaf↔Spine sessions form a full-mesh underlay
   - Loopbacks advertised with next-hop-self, update-source, and EBGP-MULTIHOP as needed
   - CE1 and CE2 (Cisco IOL) are the customer edge for each DC and peer with the leaf layer over eBGP in separate VRFs
   - PE1–PE3 connect the CEs to the MPLS core and handle L3VPN route exchange using MP-BGP (AFI/SAFI VPNv4)
   - P routers are label-switching only — no VRF or VPN awareness
   - All VRF routes from East and West DCs are carried via MPLS labels through the backbone, enabling:
     - Inter-DC VRF segmentation
     - End-to-end reachability between DC workloads in the same VRF (via L3VPN)
   - This enables true multi-tenant Layer 3 separation across the WAN
  
  - East Data Center <img src="/assets/img/nautobot_workshop/Nautobot Workshop-East DataCenter.webp" alt="">
  - West Data Center <img src="/assets/img/nautobot_workshop/Nautobot Workshop-West DataCenter.webp" alt="">

## Conclusion
At this stage of the Nautobot Workshop, we've focused on architecting the lab environment. We've defined a realistic, multi-vendor topology that mirrors a service provider core interconnecting two data centers—complete with an MPLS-enabled backbone, L3VPN capabilities, and eBGP-based Clos fabrics within each DC. Using diagrams and a clear design strategy, we’ve established the blueprint for how Nautobot, Ansible, Cisco IOL, and Arista EOS will come together in later phases. With the architecture locked in, join in for Part 3: Adding Devices to Nautobot using Ansible.