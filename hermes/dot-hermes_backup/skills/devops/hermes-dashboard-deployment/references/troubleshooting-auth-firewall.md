# Dashboard Authentication & Firewall Pitfalls

## 1. Firewalld Blocking Port 9119 (Fedora/RHEL)
When deploying the dashboard on bare metal Linux instances (like Fedora/RHEL) rather than internal VMs, the `0.0.0.0:9119` bind will be silently blocked from external LAN access by `firewalld` even if the service is running perfectly.
**Fix:**
```bash
sudo firewall-cmd --add-port=9119/tcp --permanent
sudo firewall-cmd --reload
```

## 2. June 2026 Hardening - Auth Required on 0.0.0.0
The `--insecure` flag no longer bypasses authentication when `hermes dashboard` binds to a public or LAN interface (`0.0.0.0`). The dashboard *strictly requires* an OAuth or basic auth provider. 

Attempting to disable auth (via `REQUIRE_DASHBOARD_AUTH=false`) while a stale `basic_auth` block still exists in `config.yaml` will result in the dashboard UI crashing with a `NotImplementedError` when it hits the `/auth/login` redirect.

**Proper Resolution (Nous OAuth):**
Instead of fighting the underlying basic auth config or attempting to strip it, the cleanest resolution for LAN deployments is to register the dashboard with the Nous Portal to seamlessly enable OAuth:
```bash
hermes dashboard register
systemctl --user restart hermes-dashboard.service
```

### 2a. OAuth Redirect URI Mismatch (IP vs localhost)
If the user accesses the newly OAuth-registered dashboard via a LAN IP (e.g. `http://192.168.0.242:9119`), the Nous Portal will block the sign-in with `redirect_uri_mismatch` because `hermes dashboard register` defaults to whitelisting `127.0.0.1` as the callback.
**Fix:** Tell Hermes the actual public network IP, then re-register:
```bash
hermes config set dashboard.public_url "http://192.168.0.242:9119"
hermes dashboard register
```

## 3. The Browser Cache Redirect Loop
Browser caching handles HTTP redirects aggressively. If you fix the auth configuration (or remove auth entirely), the user may still be instantly redirected to a broken `/auth/login` page because their browser cached the previous redirect.
**Fix:** Instruct the user to open an Incognito/Private window, or manually delete the `/auth/login` path from their address bar and press Enter.

## 4. Runaway "Ghost" Firefox Processes inside Systemd
`hermes dashboard` defaults to popping open the host's web browser upon successful boot. When run as a systemd background/headless user service, this results in the agent spawning dozens of invisible, frozen `firefox -contentproc` PIDs that soak up system memory and stall the dashboard. 
**Fix:** Ensure the systemd unit file appends the `--no-open` flag:
`ExecStart=/.../hermes dashboard --host 0.0.0.0 --port 9119 --no-open`