---
name: homelab-inventory-map
description: Current topology, IP inventory, local DNS names, roles, and healthy baseline for James's OPNsense/Proxmox/Pi-hole homelab.
version: 1.0.0
platforms: [linux]
metadata:
  hermes:
    category: homelab
    tags:
      - homelab
      - network-inventory
      - topology
      - dns
      - dhcp
      - opnsense
      - proxmox
      - pihole
      - mikrotik
      - omada
      - jellyfin
      - samba
---

# Homelab Inventory Map

## Purpose

Use this skill whenever James asks for the current network map, IP inventory, device roles, local hostnames, service URLs, or a sanity check of how the homelab is supposed to be connected.

This skill is descriptive and read-only. It should not perform changes. It should help the assistant avoid guessing and keep the current network model consistent.

## Current High-Level Topology

Current intended path:

```text
Sonic / ISP / Internet
        ↓
Modem / ONT
        ↓
OPNsense VM 100 on existing Proxmox host `pve`
        ↓
MikroTik CSS610-8P-2S+IN main LAN switch
        ↓
Omada APs, wired clients, servers, IoT devices, VMs, media services
```

OPNsense is the only intended active router/firewall/DHCP/NAT device.

The old TP-Link router has been removed from the routing path. Do not include it in the current topology unless James says he reintroduced it.

## Core Devices and Services

### OPNsense

```text
Role: Main router, firewall, DHCP authority, NAT gateway
VM ID: 100
Host: Proxmox host `pve`
LAN gateway IP: 192.168.0.1
Local DNS name: opnsense.home.arpa
Web UI: https://opnsense.home.arpa
```

Known successful routing baseline after TP-Link removal:

```text
client → 192.168.0.1 / opnsense.internal → Sonic / ISP → internet
```

### Proxmox

```text
Role: Virtualization host
Hostname: pve
Management IP: 192.168.0.2/24
Gateway: 192.168.0.1
Bridge: vmbr0
```

Current known management path after 10G migration:

```text
vmbr0: 192.168.0.2/24
vmbr0 bridge port: nic2
nic2: X520 spare port, PCI 0000:04:00.1
nic2 link: 10000Mb/s full duplex, link detected yes
default route: 192.168.0.1 via vmbr0
persistent service: bind-x520-spare-to-proxmox.service
checkpoint path: /root/network-checkpoints/after-proxmox-10g-migration
```

Always verify current live state before making Proxmox networking assumptions.

### Pi-hole

```text
Role: DNS/ad-blocking/local DNS
VM ID: 110
Hostname: pi-hole
IP: 192.168.0.53
Local DNS name: pi-hole.home.arpa
Admin UI: http://pi-hole.home.arpa/admin
```

Pi-hole is the intended LAN DNS server. OPNsense DHCP should hand out Pi-hole as DNS.

Confirmed healthy client DNS baseline:

```text
dig example.com
SERVER: 192.168.0.53#53
```

### MikroTik CSS610

```text
Role: Main LAN switch
Device: MikroTik CSS610-8P-2S+IN
Management IP: 192.168.0.134
Local DNS name: mikrotik-css.home.arpa
```

The MikroTik is a switch, not a router. It should not run DHCP/NAT.

### Omada AP

```text
Role: Wireless access point
Management IP: 192.168.0.113
Local DNS name: omada-ap-1.home.arpa
```

The Omada device should be an AP behind OPNsense, not a router.

### Media Repository VM

```text
Role: Samba/SMB file server and Jellyfin media server
VM ID: 120
Hostname: media-repo
IP: 192.168.0.20
Local DNS name: media-repo.home.arpa
Jellyfin URL: http://media-repo.home.arpa:8096
SMB URL: smb://media-repo.home.arpa/media
Samba-Manager URL: http://media-repo.home.arpa:5000
```

### Home Assistant

```text
Role: Home automation VM
VM ID: 130
Status: Reserved/currently treated as Home Assistant
```

Do not reuse VM ID 130 for other projects.

### Download Desktop VM

```text
Role: Private/lightweight browsing and download desktop VM
VM ID: 140
Hostname/name: desktop-dl
Access: Mac-only for now
RDP: Works from James's Mac
```

Phone RDP access is intentionally deferred.

### Hermes Agent VM

```text
Role: Dedicated Hermes Agent AI experimentation VM
VM ID: 150
Hostname: hermes
FQDN: hermes.home.arpa
IP: 192.168.0.160
OS: Debian 13
Resources: 8 GB RAM, 2 vCPU, 64 GB disk
Primary user: james
Hermes status: Installed and minimally configured
Provider: Nous Portal
Enabled tools: web search/extract only
Terminal backend: local VM backend
```

Do not give Hermes privileged integrations yet.

## Current IP and DNS Inventory

```text
192.168.0.1     opnsense.home.arpa        OPNsense router/firewall/DHCP/gateway
192.168.0.2     pve / proxmox             Proxmox host management
192.168.0.20    media-repo.home.arpa      Debian media repo, Samba, Jellyfin
192.168.0.53    pi-hole.home.arpa         Pi-hole DNS/ad-blocking
192.168.0.113   omada-ap-1.home.arpa      Omada AP management
192.168.0.134   mikrotik-css.home.arpa    MikroTik CSS610 switch management
192.168.0.160   hermes.home.arpa          Hermes Agent VM
192.168.0.186   jamess-mac-mini.home.arpa James's Mac mini admin client
```

Known admin Mac:

```text
Device: James's Mac mini over Wi-Fi
Reserved IP: 192.168.0.186
MAC: 0a:9d:13:05:b4:4a
Hostname: jamess-mac-mini.home.arpa
Role: Primary admin client
```

Important warning: this MAC begins with `0a`, suggesting macOS Private Wi-Fi Address may be enabled. If James toggles Private Wi-Fi Address or changes Wi-Fi identity, the DHCP reservation and admin firewall alias may no longer match.

## Healthy Baseline

A healthy current network should look like:

```text
- Clients receive 192.168.0.x addresses.
- Client gateway is 192.168.0.1.
- Client DNS server is 192.168.0.53.
- OPNsense is reachable at 192.168.0.1 and opnsense.home.arpa.
- Proxmox is reachable at 192.168.0.2.
- Pi-hole is reachable at 192.168.0.53 and pi-hole.home.arpa.
- Normal DNS queries use Pi-hole.
- Direct external DNS bypass fails from normal LAN clients.
- Internet traffic routes through OPNsense.
- Jellyfin works at media-repo.home.arpa:8096.
- SMB works at smb://media-repo.home.arpa/media.
- MikroTik CSS610 is reachable at 192.168.0.134.
- Omada AP is reachable at 192.168.0.113.
- Hermes VM is reachable at 192.168.0.160 / hermes.home.arpa.
```

## Suggested Response Pattern

When James asks for the map, answer in this form:

```text
Core:
- OPNsense: 192.168.0.1, router/firewall/DHCP
- Proxmox: 192.168.0.2, virtualization host
- Pi-hole: 192.168.0.53, DNS/ad-blocking

Infrastructure:
- MikroTik CSS610: 192.168.0.134, switch
- Omada AP: 192.168.0.113, wireless AP

Servers/VMs:
- media-repo: 192.168.0.20, Samba/Jellyfin
- Home Assistant: VM 130
- desktop-dl: VM 140
- hermes: 192.168.0.160, Hermes Agent

Admin:
- James's Mac mini: 192.168.0.186, admin client
```

Note that scans are point-in-time evidence and should be verified before firewall, DHCP, DNS, VLAN, passthrough, or management changes.
