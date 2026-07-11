---
name: glances-monitoring-setup
description: How to configure and run Glances as a persistent Web Server/API daemon using systemd.
version: 1.0.0
platforms: [linux]
metadata:
  hermes:
    category: devops
    tags:
      - glances
      - systemd
      - monitoring
      - devops
---

# Glances Persistent Monitoring Setup

## Purpose
Use this skill when setting up `glances` as a persistent background service (e.g. on Proxmox or Fedora) so it automatically serves a web dashboard and API on port 61208/61209.

## Common Pitfalls & Solutions

### Server Mode vs Web Server Mode
- Running `glances -s` starts the **REST API / XML-RPC Server**. 
  - This allows CLI clients to connect via `glances -c <ip>`, but it is no longer the recommended way to view Glances in a web browser in newer versions.
- Running `glances -w` starts the **Web Server Mode**. 
  - This serves the full Web UI (HTML/JS) directly. You don't use `glances -c` anymore; you view it in Chrome/Firefox at `http://<ip>:61208`.

### Port Binding (`0.0.0.0` vs `127.0.0.1`)
- By default, or if misconfigured, Glances restricts itself to localhost (`127.0.0.1`).
- To allow other computers on the LAN to see the dashboard, you must explicitly bind to all interfaces: `-B 0.0.0.0`.

## Quick Install (Systemd Service)

Use a heredoc to avoid interactive editor (`nano`) issues, especially on headless Debian/Proxmox systems without `term-info` packages for modern terminal emulators (like `xterm-kitty`).

```bash
cat << 'EOF' > /etc/systemd/system/glances.service
[Unit]
Description=Glances Web Server
After=network.target

[Service]
ExecStart=/usr/bin/glances -w -B 0.0.0.0
# If you genuinely need the XML-RPC server for CLI clients, use:
# ExecStart=/usr/bin/glances -s -B 0.0.0.0
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now glances.service
```

## Verification

Check if it is listening on all interfaces:
```bash
ss -tulpn | grep glances
```
Expected output: `tcp LISTEN 0 0.0.0.0:61208 0.0.0.0:*` (or 61209 if the port was auto-incremented during a quick restart).