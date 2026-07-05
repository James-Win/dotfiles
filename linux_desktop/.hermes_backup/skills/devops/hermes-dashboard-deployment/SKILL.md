---
name: hermes-dashboard-deployment
description: "Deploy the Hermes Agent web dashboard as a durable systemd user service on Linux. Covers dependency checks, stable auth secret, lingering, and PYTHONPATH workaround for local source installs."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, dashboard, systemd, deployment, linux]
    homepage: https://hermes-agent.nousresearch.com/docs/
---

# Hermes Dashboard Deployment

Deploy the Hermes web admin panel as a persistent systemd user service so it survives CLI session logout and reboots.

## Prerequisites

- Hermes installed (`~/.local/bin/hermes` or equivalent).
- User systemd available (`systemctl --user`).
- Dashboard intended for LAN access with basic_auth enabled.

## Steps

1. **Stable auth secret**
   ```bash
   hermes config set dashboard.basic_auth.secret "$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
   ```
   Without this, Hermes regenerates a random signing key per process; web sessions die on every restart.

2. **Missing dependency check**
   The dashboard needs `fastapi`, `uvicorn`, and `python-multipart`. Install any that are missing:
   ```bash
   python3 -m pip install --user --no-warn-script-location fastapi uvicorn python-multipart
   ```

3. **PYTHONPATH workaround**
   If the installed package version rejects the host Python or the dashboard fails with `ModuleNotFoundError: No module named 'hermes_cli.dashboard_auth'`, point at the live source tree:
   ```bash
   export PYTHONPATH="$HOME/.hermes/hermes-agent"
   ```
   Verify:
   ```bash
   PYTHONPATH="$HOME/.hermes/hermes-agent" python3 -c "import hermes_cli.dashboard_auth.routes"
   ```

4. **Systemd user unit**
   Create `~/.config/systemd/user/hermes-dashboard.service` using the template in `references/systemd-unit-template.md`. 
   *CRITICAL: Ensure the `ExecStart` command passes the `--no-open` flag to prevent headless Firefox ghost process leaks. Without this, the background service will quietly spawn hundreds of zombie browser instances.*
   Then:
   ```bash
   systemctl --user daemon-reload
   systemctl --user enable --now hermes-dashboard.service
   ```

5. **Linger**
   Start at boot without a login session:
   ```bash
   sudo loginctl enable-linger "$USER"
   ```

6. **Verify**
   ```bash
   systemctl --user status hermes-dashboard.service
   curl -I http://127.0.0.1:9119/   # expect 302 to /auth/login
   ```

## Troubleshooting

See `references/lan-troubleshooting-pitfalls.md` for fixing Fedora/RHEL `firewalld` blocks on port 9119, bypassing the June 2026 `--insecure` auth hardening by using `hermes dashboard register` OAuth, routing around the Nous portal IP restriction with SSH Port Forwarding, and suppressing `firefox` ghost processes in background units.

- **`ModuleNotFoundError: No module named 'hermes_cli.dashboard_auth'`**
  Source tree mismatch; set `PYTHONPATH=%h/.hermes/hermes-agent` in the unit.

- **`RuntimeError: Form data requires "python-multipart" to be installed.`**
  Install `python-multipart`.

- **`Web UI dependencies not installed (need fastapi + uvicorn).`**
  Install `fastapi` and `uvicorn`.

- **Firefox: "no video with supported format and MIME type found" on `/desktop/`**
  The error is misleading — it can mean either a missing system codec or the
  dashboard's auth middleware returning 500. Diagnose in this order:

  1. Check Firefox journalctl for `Couldn't open avcodec` — if present, the
     local system lacks FFmpeg codec libraries (see
     `references/fedora44-ffmpeg-rename.md` for package names).
  2. If no codec errors, check dashboard logs for `BasicAuthProvider` /
     `NotImplementedError` — this means `/desktop/` is returning 500 before
     the SPA loads. Root cause: `GET /auth/login?provider=basic` calls
     `start_login()` on the basic provider, but basic auth is password-only
     and only supports `POST /auth/password-login`. This usually happens when
     a middleware or redirect rewrites to `?provider=basic`. Check the
     dashboard's auth prefix/middleware routes. Hard-refresh Firefox
     (Ctrl+Shift+R) to clear cached error state after the backend fix.

- **Service flaps**
  Check `journalctl --user -u hermes-dashboard.service --since '10 min ago'` and confirm `PYTHONPATH` and dependencies are correct.
