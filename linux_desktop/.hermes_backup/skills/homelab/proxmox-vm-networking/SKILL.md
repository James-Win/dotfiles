---
name: proxmox-vm-networking
description: Safely reason about James's Proxmox host networking, VM inventory, OPNsense VM passthrough, management access, and VM connectivity.
version: 1.0.0
platforms: [linux]
metadata:
  hermes:
    category: homelab
    tags:
      - proxmox
      - vm
      - bridge
      - pci-passthrough
      - opnsense
      - x520
      - x550
      - vfio
      - networking
      - management-access
---

# Proxmox VM Networking Skill

## Purpose

Use this skill when James asks about Proxmox, VM networking, VM IDs, bridges, PCI passthrough, OPNsense VM 100 networking, Proxmox management access, 10G migration, VM reachability, or safe host networking changes.

Primary duty: preserve Proxmox access and avoid breaking OPNsense VM 100.

## Current Proxmox Host

```text
Host: existing Proxmox host `pve` / machine one
Management IP: 192.168.0.2/24
Gateway: 192.168.0.1
Bridge: vmbr0
```

Current known state after 10G migration:

```text
vmbr0: 192.168.0.2/24
vmbr0 bridge port: nic2
nic2: X520 spare port, PCI 0000:04:00.1
nic2 link: 10000Mb/s full duplex, link detected yes
default route: 192.168.0.1 via vmbr0
persistent service: bind-x520-spare-to-proxmox.service
checkpoint path: /root/network-checkpoints/after-proxmox-10g-migration
```

Do not assume old Realtek management path is still live. Verify before changing networking.

## VM Inventory

```text
VM 100: OPNsense router/firewall
VM 110: Pi-hole, 192.168.0.53
VM 120: media-repo, 192.168.0.20, Samba/Jellyfin
VM 130: Home Assistant
VM 140: desktop-dl, private/lightweight browsing/download desktop
VM 150: hermes, 192.168.0.160, Hermes Agent
```

Do not reuse VM ID 130 because James corrected it is Home Assistant.

## OPNsense VM 100 NIC Context

Current intended physical NIC use:

```text
WAN: Intel X550 RJ45 port, PCI 27:00.0
LAN: Intel X520 SFP+ port, PCI 04:00.0
Reserved/future: X550 27:00.1
Host/Proxmox 10G management: X520 04:00.1 / nic2
```

Do not pass through the Proxmox management NIC.

Known OPNsense interface names from earlier state:

```text
LAN: ix0
WAN: ix2
Temporary VirtIO: vtnet0
```

Historical outage:

```text
OPNsense WAN was accidentally assigned to temporary VirtIO vtnet0 on 192.168.0.249/24 instead of physical WAN ix2.
Reassigning WAN to ix2, MAC ec:e7:a7:1d:8b:38, restored internet.
```

Future cleanup:

```text
Remove/disable temporary vtnet0 from VM 100 only after confirming stable WAN/LAN and after James explicitly approves.
```

Never remove VM 100 NICs blindly.

## Critical Safety Rules

Before changing Proxmox networking or passthrough:

1. Confirm James has local console or a known rollback path.
2. Confirm current Proxmox management interface and IP.
3. Confirm OPNsense VM 100 is not dependent on the interface being changed.
4. Capture current config.
5. Change one thing at a time.
6. Do not reboot or restart networking remotely unless James understands lockout risk.

Do not:

```text
- Change /etc/network/interfaces blindly.
- Restart networking remotely after bridge edits without console access.
- Pass through nic2 or the live Proxmox management interface.
- Remove VM 100 NICs without explicit confirmation.
- Delete VM 100 temporary vtnet0 without confirming current WAN/LAN stability.
- Create nested pve2 for the main router.
- Move OPNsense to another physical node unless James explicitly changes the plan.
```

Preferred strategy remains:

```text
Keep OPNsense directly as VM 100 on existing `pve`.
Do not create nested pve2 for the main router.
```

## Read-Only Proxmox Checks

Use these before any networking or passthrough change:

```bash
ip -br addr
ip route
cat /etc/network/interfaces
bridge link
qm list
qm config 100
qm config 110
qm config 120
qm config 130
qm config 140
qm config 150
systemctl status networking --no-pager
systemctl status bind-x520-spare-to-proxmox.service --no-pager
lspci -nnk
```

For link status:

```bash
ethtool nic2
```

Expected for current 10G management:

```text
Speed: 10000Mb/s
Duplex: Full
Link detected: yes
```

## Workflow: Proxmox Access Problem

Expected access:

```text
https://192.168.0.2:8006
```

From a client:

```bash
ping -c 4 192.168.0.2
```

From Proxmox console or SSH:

```bash
ip -br addr
ip route
cat /etc/network/interfaces
bridge link
systemctl status networking --no-pager
systemctl status bind-x520-spare-to-proxmox.service --no-pager
```

Interpretation:

```text
No 192.168.0.2 on vmbr0:
  Proxmox management IP/bridge issue.

No default route:
  Proxmox cannot reach outside LAN.

vmbr0 bridge port wrong or down:
  physical management link/bridge issue.

bind-x520 service failed:
  spare X520 port may not have rebound to ixgbe/nic2.
```

Do not restart networking until James has console access or accepts the risk.

## Workflow: Verify VM 100 Before OPNsense NIC Changes

Run:

```bash
qm config 100
```

Look for:

```text
hostpci entries
net entries
bridge references
temporary VirtIO adapter
```

Before suggesting removal of any VM 100 NIC:

1. Confirm which OPNsense interface is WAN.
2. Confirm which OPNsense interface is LAN.
3. Confirm current internet works.
4. Confirm Proxmox access works.
5. Confirm James explicitly approves removal.

## Workflow: VM Reachability

Known expected VM/service reachability:

```text
VM 110 Pi-hole:      192.168.0.53
VM 120 media-repo:   192.168.0.20
VM 130 Home Assistant
VM 140 desktop-dl
VM 150 hermes:       192.168.0.160
```

From Proxmox:

```bash
qm list
```

From a client:

```bash
ping -c 4 192.168.0.53
ping -c 4 192.168.0.20
ping -c 4 192.168.0.160
```

DNS checks:

```bash
dig pi-hole.home.arpa
dig media-repo.home.arpa
dig hermes.home.arpa
```

## Recommended Checkpoint Practice

For major Proxmox changes, create checkpoints/snapshots first when appropriate.

Known checkpoint:

```text
/root/network-checkpoints/after-proxmox-10g-migration
```

For VM milestones:

```text
after-hermes-setup-minimal-working
after-samba-manager-working
```

Before risky edits, capture:

```bash
mkdir -p /root/network-checkpoints/<checkpoint-name>
cp /etc/network/interfaces /root/network-checkpoints/<checkpoint-name>/interfaces
qm config 100 > /root/network-checkpoints/<checkpoint-name>/qm-100.conf
ip -br addr > /root/network-checkpoints/<checkpoint-name>/ip-addr.txt
ip route > /root/network-checkpoints/<checkpoint-name>/ip-route.txt
bridge link > /root/network-checkpoints/<checkpoint-name>/bridge-link.txt
lspci -nnk > /root/network-checkpoints/<checkpoint-name>/lspci-nnk.txt
```

## Response Template

When helping James with Proxmox:

```text
Known state:
- Proxmox should be 192.168.0.2 on vmbr0.
- Current management path is believed to be nic2 / X520 04:00.1.
- OPNsense VM 100 provides the gateway at 192.168.0.1.

Goal:
- Verify the live state before changing anything.

Risk:
- Proxmox bridge or passthrough mistakes can lock out management or break the router VM.

Steps:
1. Run read-only checks.
2. Paste output.
3. Interpret before changing.

Next:
- Only recommend the smallest reversible change.
```
