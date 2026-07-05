# Hermes Dashboard: Bare-Metal / LAN Troubleshooting

When deploying `hermes-dashboard.service` to a bare-metal Linux host, typical connectivity and auth issues arise:

### 1. Zombie Browser Processes (Systemd Loop)
When `hermes dashboard` starts, it attempts to `xdg-open` your default browser. Running inside a systemd background service, this behavior spawns invisible, frozen browser instances (e.g., Firefox `contentproc` zombies) which consume massive RAM and stick around forever.
**Fix:** You **MUST** append the `--no-open` flag to the `ExecStart` line in the service file.

### 2. Nous OAuth Localhost Restriction (redirect_uri_mismatch)
The Nous Portal enforces `127.0.0.1` as the return authorized URI for self-hosted apps to prevent token-theft. Using a raw LAN IP (e.g., `192.168.0.242:9119`), even with `public_url` configured, will result in a `redirect_uri_mismatch`. 
**Fix:** You cannot authenticate directly against the LAN IP. Establish an SSH tunnel from the client (`ssh -L 9119:127.0.0.1:9119 user@host`) and visit `http://127.0.0.1:9119` in the browser to log in correctly.

### 3. Firewalld Blocking 
By default, Fedora/RHEL `firewalld` blocks custom ports. 
**Fix:** Run `sudo firewall-cmd --add-port=9119/tcp --permanent && sudo firewall-cmd --reload`

### 4. Broken Redirect Caching 
If dashboard authentication is toggled or broken, the browser aggressively caches the `302` redirect to `/auth/login` (even resulting in `NotImplementedError` if Basic Auth misfires).
**Fix:** Disable auth securely, then hard-refresh the cache via an Incognito window or manually truncating the path back to the root `9119/`.