---
name: opnsense-firewall-dns
description: Safely troubleshoot and manage James's OPNsense, DHCP, Pi-hole DNS enforcement, firewall baseline, and local DNS behavior.
version: 1.0.0
platforms: [linux]
metadata:
  hermes:
    category: homelab
    tags:
      - opnsense
      - firewall
      - dns
      - dhcp
      - pihole
      - nat
      - gateway
      - troubleshooting
      - home-arpa
---

# OPNsense Firewall and DNS Skill

## Purpose

Use this skill when James asks about OPNsense, DHCP, DNS, Pi-hole, firewall rules, local hostnames, WAN/LAN connectivity, DNS bypass blocking, OPNsense web UI access, IPv6, or internet outages.

Primary duty: preserve working internet, DNS, and management access.

Do not make firewall, DHCP, DNS, WAN, LAN, or interface changes without explicit confirmation.

## Current Authority Model

### Router/firewall/DHCP

```text
Authority: OPNsense
VM ID: 100
Gateway/LAN IP: 192.168.0.1
Local DNS name: opnsense.home.arpa
Web UI: https://opnsense.home.arpa
```

OPNsense is the only intended active router/firewall/DHCP/NAT device.

### DNS

```text
Primary LAN DNS: Pi-hole
Pi-hole IP: 192.168.0.53
Pi-hole hostname: pi-hole.home.arpa
```

OPNsense DHCP should hand out Pi-hole as the IPv4 DNS server.

Expected client network settings:

```text
IP: 192.168.0.x
Gateway/router: 192.168.0.1
DNS server: 192.168.0.53
```

Preferred local domain:

```text
home.arpa
```

Do not replace `home.arpa` with `.local`, `.lan`, or a public-looking domain unless James explicitly requests a redesign.

## Known Local DNS Records

```text
opnsense.home.arpa      → 192.168.0.1
pi-hole.home.arpa       → 192.168.0.53
media-repo.home.arpa    → 192.168.0.20
mikrotik-css.home.arpa  → 192.168.0.134
omada-ap-1.home.arpa    → 192.168.0.113
hermes.home.arpa        → 192.168.0.160
```

Historical note: `opnsense.home.arpa` originally triggered an OPNsense DNS rebind warning. That was resolved by adding `opnsense.home.arpa` as an approved/alternate hostname in OPNsense under:

```text
System → Settings → Administration
```

## Current Firewall Baseline

### WAN

WAN should have no unnecessary user-defined allow rules.

Unsolicited WAN traffic should remain blocked by default.

Do not add WAN allow rules or port forwards unless James explicitly asks and understands the exposure risk.

### LAN DNS Enforcement

Known working DNS-control baseline:

```text
Allow TRUSTED_LAN_NET → PIHOLE on DNS_PORTS
Allow PIHOLE → any on DNS_PORTS
Block LAN DNS bypass around Pi-hole
```

This blocks normal LAN clients from sending direct DNS to non-Pi-hole servers such as:

```text
1.1.1.1
8.8.8.8
9.9.9.9
```

Expected client tests:

```bash
dig example.com
# Expected: SERVER: 192.168.0.53#53

dig @1.1.1.1 example.com
# Expected: timeout or failure, because direct DNS bypass is blocked
```

DNS-over-HTTPS and DNS-over-TLS are not yet fully blocked.

### OPNsense Web UI Lockdown

Known admin client:

```text
James's Mac mini: 192.168.0.186
Hostname: jamess-mac-mini.home.arpa
MAC: 0a:9d:13:05:b4:4a
```

Known aliases:

```text
ADMIN_CLIENTS: 192.168.0.186

MGMT_TARGETS:
  - 192.168.0.1
  - 192.168.0.2
  - 192.168.0.53
  - 192.168.0.134
  - 192.168.0.113
```

Known rule:

```text
Block non-admin access to OPNsense web UI
```

Behavior:

```text
Block IPv4 TCP
Source: not ADMIN_CLIENTS
Destination: This Firewall
Port: OPNSENSE_WEB_PORTS
Logging: enabled
```

The broad default LAN IPv4 allow rule may still exist. Do not assume all management interfaces are fully locked down just because `MGMT_TARGETS` exists.

### IPv6

Current posture is IPv4-first.

The default LAN IPv6 allow rule was disabled, and normal websites still loaded afterward.

IPv6 is not finalized. Do not design or enforce a new IPv6 policy without verifying current WAN/LAN IPv6 behavior.

## OPNsense Interface Context

Known intended physical NIC use for VM 100:

```text
WAN: Intel X550 RJ45 port, PCI 27:00.0
LAN: Intel X520 SFP+ port, PCI 04:00.0
Reserved/future: X550 27:00.1
Host/Proxmox 10G management: X520 04:00.1 / nic2
```

Known OPNsense interface names from previous state:

```text
LAN: ix0
WAN: ix2
Temporary VirtIO: vtnet0
```

A previous outage happened because WAN was assigned to temporary VirtIO `vtnet0` on `192.168.0.249/24` instead of physical WAN `ix2`.

The fix was assigning WAN to:

```text
ix2, MAC ec:e7:a7:1d:8b:38
```

and rebooting OPNsense.

Future cleanup recommendation:

```text
Remove or disable temporary vtnet0 from VM 100 only after stable WAN/LAN operation is confirmed and James explicitly approves.
```

Never remove VM 100 NICs blindly.

## Safety Rules

Before changing OPNsense:

1. Confirm James still has OPNsense access.
2. Confirm James has Proxmox access if changing VM 100 networking.
3. Identify the exact rule/interface/alias being changed.
4. Note current settings or take screenshots.
5. Prefer adding a specific reversible rule over deleting existing rules.
6. Make one change at a time.
7. Verify internet, DNS, and management after each change.

Do not:

```text
- Disable DHCP without a replacement plan.
- Change LAN IP casually.
- Delete firewall rules casually.
- Add WAN allow rules casually.
- Expose Jellyfin, Samba, Pi-hole, Proxmox, or OPNsense to WAN.
- Enable UPnP without an explicit discussion.
- Change VLAN trunking without preserving management access.
- Remove vtnet0 or VM 100 NICs unless explicitly confirmed.
```

## Workflow: Client Has No Internet

Ask James to run from the affected client:

```bash
ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null
route -n get default
scutil --dns | grep nameserver
ping -c 4 192.168.0.1
ping -c 4 192.168.0.53
ping -c 4 1.1.1.1
dig example.com
dig @192.168.0.53 example.com
```

Interpretation:

```text
Can ping 192.168.0.1 but not 1.1.1.1:
  likely OPNsense WAN/routing/NAT/ISP issue.

Can ping 1.1.1.1 but dig fails:
  likely DNS/Pi-hole issue.

Can dig @192.168.0.53 but normal dig fails:
  client is not using Pi-hole as DNS.

Cannot ping 192.168.0.1:
  local LAN, Wi-Fi, switch, VLAN, DHCP, or client IP issue.
```

## Workflow: DNS Not Working

Expected:

```text
Client DNS server: 192.168.0.53
Gateway: 192.168.0.1
```

Ask James to run:

```bash
dig example.com
dig @192.168.0.53 example.com
dig opnsense.home.arpa
dig pi-hole.home.arpa
dig media-repo.home.arpa
```

Bypass test:

```bash
dig @1.1.1.1 example.com
```

Expected direct external DNS result:

```text
timeout or failure
```

If direct external DNS succeeds, the client may be outside the intended LAN path or the DNS bypass block may not be active.

## Workflow: Pi-hole Down

Symptoms:

```text
- Clients have internet by IP but DNS fails.
- Local names fail.
- dig @192.168.0.53 fails.
```

On Pi-hole VM:

```bash
ip -br addr
ip route
pihole status
systemctl status pihole-FTL --no-pager
dig @127.0.0.1 example.com
dig @192.168.0.53 example.com
```

Safe restart if appropriate:

```bash
sudo systemctl restart pihole-FTL
```

Do not change OPNsense DHCP away from Pi-hole unless James explicitly wants a temporary failover.

## Workflow: OPNsense Access Problem

Expected access:

```text
https://opnsense.home.arpa
https://192.168.0.1
```

From James's Mac:

```bash
ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null
ping -c 4 192.168.0.1
dig opnsense.home.arpa
```

If James's Mac is no longer `192.168.0.186`, the `ADMIN_CLIENTS` alias may no longer include his current IP. This can happen if macOS Private Wi-Fi Address changes the MAC/IP.

Do not modify firewall rules unless James has console or alternate access.

## Response Template

When helping James with OPNsense/DNS:

```text
Known state:
- OPNsense is 192.168.0.1.
- Pi-hole is 192.168.0.53.
- DHCP should hand clients 192.168.0.53 as DNS.

Goal:
- Identify whether this is LAN, WAN, DNS, DHCP, or firewall.

Risk:
- OPNsense/firewall changes can lock out management or break internet.

Steps:
1. Run read-only checks.
2. Paste output.
3. Interpret before changing anything.

Next:
- Only recommend the smallest reversible change after the output is understood.
```
