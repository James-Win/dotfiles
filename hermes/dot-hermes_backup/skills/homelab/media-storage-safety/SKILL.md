---
name: media-storage-safety
description: Safely manage and troubleshoot James's media-repo VM, Samba, Jellyfin, Samba-Manager, UFW, media disks, and old VeraCrypt source drives.
version: 1.0.0
platforms: [linux]
metadata:
  hermes:
    category: homelab
    tags:
      - media-repo
      - samba
      - smb
      - jellyfin
      - samba-manager
      - ufw
      - storage
      - veracrypt
      - disks
      - data-safety
---

# Media and Storage Safety Skill

## Purpose

Use this skill when James asks about media-repo, Samba/SMB, Jellyfin, Samba-Manager, UFW on the media server, media folders, media disks, old drives, VeraCrypt containers, disk identification, copying media, or storage migration.

Primary duty: protect data. Do not wipe, format, pool, initialize, or modify disks unless the exact target is identified and James explicitly confirms.

## Current Media Repository VM

```text
VM ID: 120
Hostname: media-repo
OS: Debian 13
IP: 192.168.0.20
Local DNS: media-repo.home.arpa
Role: Samba/SMB file server and Jellyfin media server
```

Service URLs:

```text
Jellyfin: http://media-repo.home.arpa:8096
SMB: smb://media-repo.home.arpa/media
Samba-Manager: http://media-repo.home.arpa:5000
```

Samba/SMB works with password-protected access for user `james`.

Jellyfin is installed, library scan completed, and playback works.

## Samba-Manager

```text
Service: samba-manager.service
Install path: /opt/samba-manager
URL: http://media-repo.home.arpa:5000
```

Known troubleshooting history:

```text
Initial systemd status=203/EXEC failure was fixed by rebuilding the Python venv under /opt/samba-manager.
Login POST returning HTTP 200 and staying on the login page was fixed by visiting /register and creating the first admin account.
```

If login breaks later:

```text
Check /opt/samba-manager/users.json.
Resetting that file to {} and restarting samba-manager.service resets only Samba-Manager web UI users.
It does not reset Linux user james, Samba users, shares, or media data.
```

Do not reset users.json without James's confirmation.

Known Samba rollback backup:

```text
/root/samba-backup-before-manager
```

Recommended snapshot:

```text
after-samba-manager-working
```

## Current UFW Safety Posture on media-repo

UFW was configured with default deny incoming.

Known intended rules:

```text
Allow 5000/tcp only from James's admin Mac 192.168.0.186
Allow SSH 22 only from 192.168.0.186
Allow Cockpit 9090 only from 192.168.0.186
Allow Jellyfin 8096 from 192.168.0.0/24
Allow Samba from 192.168.0.0/24:
  - 445/tcp
  - 139/tcp
  - 137/udp
  - 138/udp
Deny 5000/tcp from anywhere else and IPv6
```

Verify with:

```bash
sudo ufw status verbose
```

Do not expose Samba, Samba-Manager, SSH, Cockpit, or Jellyfin to WAN without explicit discussion.

## Storage Safety Context

James has old HDDs/SSDs containing media, mostly in VeraCrypt container files.

Critical rule:

```text
Treat old media drives as source/archive drives.
Do not format, initialize, pool, add to ZFS, add to LVM, add to RAID, or modify them prematurely.
```

VeraCrypt context:

```text
Most encrypted media is stored in VeraCrypt container files, not full-disk encrypted volumes.
```

Preferred migration strategy:

```text
1. Mount old media/VeraCrypt content read-only first.
2. Copy contents into the new media repository.
3. Verify copied data.
4. Only then consider reusing old drives.
5. Reusing or formatting old drives requires explicit confirmation.
```

Never advise wiping a disk unless the exact model, serial, path, and purpose are confirmed.

## Known Disk Safety Rules

Do not identify disks only by `/dev/sdX` when performing destructive operations. Device names can change across boots.

Always verify with:

```bash
lsblk -o NAME,SIZE,MODEL,SERIAL,TYPE,FSTYPE,MOUNTPOINT
ls -l /dev/disk/by-id/
```

For health checks:

```bash
sudo smartctl -a /dev/sdX
```

Before formatting anything, require:

```text
- exact device path
- model
- serial
- size
- current filesystem/partition state
- intended purpose
- explicit confirmation from James that data loss is acceptable
```

## Current Folder Plan

The media repository may use folders like:

```text
/srv/media/movies
/srv/media/tv
/srv/media/music
/srv/media/photos
/srv/media/documents
/srv/media/imports
/srv/media/unsorted
```

Do not rename or restructure shares without checking current Samba config and Jellyfin library paths.

## Workflow: Jellyfin Not Reachable

Expected:

```text
http://media-repo.home.arpa:8096
http://192.168.0.20:8096
```

From client:

```bash
ping -c 4 192.168.0.20
dig media-repo.home.arpa
```

On media-repo:

```bash
systemctl status jellyfin --no-pager
ss -tulpn | grep 8096
sudo ufw status verbose
```

Expected UFW allows Jellyfin 8096 from LAN:

```text
192.168.0.0/24
```

Do not expose Jellyfin externally unless James explicitly asks.

## Workflow: SMB Not Reachable

Expected:

```text
smb://media-repo.home.arpa/media
smb://192.168.0.20/media
```

On media-repo:

```bash
systemctl status smbd --no-pager
testparm -s
sudo ufw status verbose
ss -tulpn | grep -E '445|139'
```

Expected Samba ports:

```text
445/tcp
139/tcp
137/udp
138/udp
```

Before changing Samba config:

```bash
sudo cp -a /etc/samba /root/samba-backup-$(date +%F-%H%M%S)
```

Do not change file ownership recursively on media folders without verifying the target path.

## Workflow: Samba-Manager Not Reachable

Expected:

```text
http://media-repo.home.arpa:5000
```

This should only be reachable from:

```text
192.168.0.186
```

On media-repo:

```bash
systemctl status samba-manager --no-pager
sudo ufw status verbose
ss -tulpn | grep 5000
```

If `status=203/EXEC` appears, suspect broken venv/path under `/opt/samba-manager`.

If login stays on the login page with HTTP 200, check whether first admin registration was completed at:

```text
/register
```

Do not reset `/opt/samba-manager/users.json` without explicit confirmation.

## Workflow: Identify a New or Old Disk

Use read-only commands first:

```bash
lsblk -o NAME,SIZE,MODEL,SERIAL,TYPE,FSTYPE,MOUNTPOINT
ls -l /dev/disk/by-id/
sudo blkid
```

Ask James to paste output.

Interpret carefully:

```text
Empty destination disk:
  OK candidate only after model/serial confirmation.

Old media/source disk:
  Treat read-only/source-first.

Unknown disk:
  Do not mount read-write, format, or add to storage pools.

Proxmox system disk:
  Do not touch.

VM disk/LVM member:
  Do not touch.
```

## Workflow: Copy from VeraCrypt Source

High-level safe pattern:

```text
1. Identify source drive.
2. Identify VeraCrypt container file.
3. Mount source read-only if possible.
4. Open/mount VeraCrypt container carefully, preferably read-only first.
5. Copy to /srv/media/imports or organized media folders.
6. Verify copy.
7. Keep original intact until verification is complete.
```

Do not automate deletion of source files.

## Response Template

When helping James with media/storage:

```text
Known state:
- media-repo is 192.168.0.20.
- Jellyfin is on port 8096.
- SMB share is smb://media-repo.home.arpa/media.
- Old media drives may contain VeraCrypt container files and must be protected.

Goal:
- Identify whether this is service, firewall, DNS, permission, disk, or data issue.

Risk:
- Storage mistakes can permanently destroy data.

Steps:
1. Use read-only checks.
2. Identify exact paths/devices.
3. Back up configs before changing services.
4. Ask for confirmation before destructive changes.

Next:
- Recommend the smallest reversible step.
```
