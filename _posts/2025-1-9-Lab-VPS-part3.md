---
title: "Access Without Exposure: How This Lab Platform Keeps Proxmox Hidden"
date: 2026-1-9
categories: [Homelab, Networking, Virtualization]
tags: [cloudflare, proxmox, novnc, security, tunnels]
lab_vps_banner: true
excerpt: "How I provide SSH and console access to lab VMs without exposing Proxmox, public IPs, or the underlying infrastructure — and why keeping access mediated by the application matters."
image:
  path: /assets/img/vps_series/lab-vps-thumbnail.webp
---


**TL;DR:** This platform gives users full SSH and console access to their lab VMs without ever exposing Proxmox, public IPs, or the underlying infrastructure.

---

In Part 2, I laid out the architecture of this platform — the control plane, the application plane, and the customer plane — and why those boundaries exist.

This post focuses on where the boundaries are:

**user access.**

Not billing.  
Not provisioning.  
Access.

It’s the place where shortcuts feel justified, temporary workarounds become permanent, and suddenly your hypervisor is a few firewall rules away from the internet.

From the beginning, I made one rule non-negotiable:

**Users never connect directly to Proxmox.**

Everything in this post flows from that decision — how SSH works, how console access works, and how the platform enforces boundaries without relying on public IPs or brittle network rules.

---

## The Rule That Shapes Everything

There is one rule that shows up everywhere in the code:

**Users never connect directly to Proxmox.**

Not for SSH.  
Not for VNC.  
Not through a “temporary” workaround that becomes permanent six months later.

Proxmox is a private control plane. The only thing allowed to talk to it is the orchestrator.

Once you commit to that rule, a lot of design decisions stop being debates. They become constraints — and those constraints simplify everything else.

---

## Why Public IPs Were a Non-Starter

The most obvious way to give someone access to a VM is to assign it a public IP and poke a few holes in a firewall.

That works — briefly.

Very quickly, it introduces problems:

- Public IPv4 is scarce and expensive  
- Firewall rules become brittle as the platform grows  
- A single mistake can expose far more than intended  
- Access control leaks into the network layer  

More importantly, it tightly couples user access to infrastructure details.

I wanted the opposite: **access as an application concern**, not a networking one.

I did not want someone to rent a VM that hosts a service that has the potential to expose me to something unlawful, not use the VM for its state purpose, allowing you to lab a virtual environment.

---

## Cloudflare Tunnels as the Default Access Mechanism

Every VM gets its own Cloudflare Tunnel.

There are no inbound firewall rules.  
There are no exposed hypervisors.  
Each VM initiates its own outbound connection.

From the user’s perspective, they get a stable hostname they can SSH to. From the platform’s perspective, nothing is listening on the internet.

Here’s the core of that logic from the main JavaScript code:

```js
async function ensureTunnelAndDns({ vmId, includeEveHttp = false }) {
  const sshHostname = `ssh-${vmId}.${process.env.BASE_DOMAIN}`;
  const eveHostname = includeEveHttp ? `eve-${vmId}.${process.env.BASE_DOMAIN}` : null;

  const tunnelName = `vm-${vmId}-tunnel`;

  const ingress = [{ hostname: sshHostname, service: "ssh://localhost:22" }];
  if (includeEveHttp && eveHostname) {
    ingress.push({ hostname: eveHostname, service: "http://localhost:80" });
  }
  ingress.push({ service: "http_status:404" });

  // Tunnel and DNS creation omitted for brevity
}
```

A few things are worth calling out:
- SSH access is explicitly defined — nothing else is implied
- EVE-NG web access is optional and deliberate
- Anything not explicitly routed returns a 404
There’s no “default allow” behavior hiding underneath.

---

## Tunnels Are Created Just-in-Time

Tunnels aren’t preallocated or reused.

They’re created only after a VM has been successfully provisioned and is ready to boot. If provisioning fails, the tunnel is never exposed. If a VM is destroyed, the tunnel is torn down.

That lifecycle discipline matters. Orphaned access paths are how platforms slowly accumulate risk without realizing it.

---

## Cloud-Init Is the Trust Boundary

Once the tunnel exists, the platform needs to hand off access details to the guest.

That handoff happens exactly once, via cloud-init.

Here’s where the cloud-init configuration is rendered:

```javascript
function renderCloudInitTemplate({ tunnelToken, sshHostname, vmUsername, vmPassword }) {
  const tmpl = fs.readFileSync("views/cloudinit/user-data.ejs", "utf8");

  return ejs.render(tmpl, {
    tunnelToken,
    sshHostname,
    vmUsername,
    vmPasswordB64: Buffer.from(vmPassword).toString("base64"),
  });
}
```

And later, during provisioning:

```javascript
await uploadCloudInitSnippetToProxmox({ snippetFilename, userDataYaml });
await attachCloudInitSnippetToVm({ vmId, snippetFilename });
```

After this point, the platform is done configuring the guest.

It never SSHs into the VM.
It never runs post-provision scripts remotely.
It never needs long-lived credentials.

That separation is deliberate.

The platform controls lifecycle.
The guest controls itself.

---

## Why the Platform Never SSHs Into Customer VMs

It would be easy to justify “just one SSH connection” to finish setup.

That shortcut doesn’t stay small for long.

The moment your application can SSH into customer VMs, you’ve erased a boundary that’s very hard to restore. You now have to think about credential storage, auditing, blast radius, and what happens if that access leaks.

This design avoids all of that by simply refusing to cross the boundary in the first place.

---

## Console Access Without Proxmox Exposure

SSH isn’t always enough. Sometimes you need a console.

But the rule still applies: users never talk to Proxmox.

When a user opens a console from the dashboard, the application brokers the session using short-lived Proxmox VNC tickets:

```javascript
async function getVncProxy({ node, vmId }) {
  const { ticket, csrf } = await getPveAuth();

  const res = await fetch(
    `/nodes/${node}/qemu/${vmId}/vncproxy`,
    {
      method: "POST",
      headers: {
        Cookie: `PVEAuthCookie=${ticket}`,
        CSRFPreventionToken: csrf,
      },
      body: "websocket=1",
    }
  );

  return { vncticket: data.ticket, port: data.port };
}
```

Those tickets expire quickly.
They’re scoped to a single VM.
They never expose node names or internal IPs.

From the user’s perspective, they clicked Console and got a console window. Everything else stays hidden.

---

## Suspending Access Is Boring — and That’s a Feature

When billing fails, the response is immediate and intentionally uneventful:

```javascript
async function suspendVmAccess({ vmId, userId }) {
  await Vm.updateOne(
    { userId, vmId },
    { $set: { status: "suspended" } }
  );

  await stopVmOnProxmox({ vmId });
}
```

No firewall updates.
No DNS juggling.
No partial access states.

Because access is mediated by the application, enforcement becomes just another state transition.

That boringness is a sign the boundary is in the right place.

---

## What This Design Optimizes For

This access model isn’t the cheapest or the simplest possible solution.

It adds:
- Cloudflare API dependencies
- Tunnel lifecycle management
- More orchestration logic

In exchange, it buys:
- Zero exposed control plane
- No public IP management
- Short-lived, scoped credentials
- Clear, predictable failure modes

For a platform meant to host long-running lab environments, that tradeoff is worth making.

---

## This Is Really About Blast Radius

At the end of the day, this design optimizes for one thing:

**blast radius reduction**.

If a VM is compromised, it doesn’t expose Proxmox.
If a user account is compromised, it doesn’t expose other VMs.
If the application misbehaves, it still can’t hand out raw infrastructure access.

Every layer knows only what it needs to know — and nothing more.

---

## What’s Next

In the next post, I’ll step into the VMs themselves — how the EVE-NG and Containerlab templates are built, what’s baked in, and what I intentionally leave out.

This is still the platform as it exists today — shaped by real constraints, real mistakes, and the reality of running labs that people expect to be there tomorrow.