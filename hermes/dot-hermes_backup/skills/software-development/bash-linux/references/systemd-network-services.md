# Systemd Network Service Patterns & Pitfalls

## 1. Binding Interface (0.0.0.0 vs 127.0.0.1)
When wrapping network tools (like monitoring agents) in a systemd service, verify the bind address. Many tools default to `127.0.0.1` (localhost only) when run securely, making them unreachable over the LAN even if the `systemctl status` shows active.
**Fix:** Explicitly pass the global network bind flag (e.g., `-B 0.0.0.0`).

## 2. Server Mode Protocols (Web vs XML-RPC)
Tools often have mutually exclusive server modes that clients must perfectly match.
Example with `glances`:
- `glances -s`: Starts an **XML-RPC** server. The CLI client (`glances -c <ip>`) specifically expects this. A web browser pointed here will encounter 501 Unsupported Method or XML-RPC faults.
- `glances -w`: Starts a **REST/Web** server. Web browsers can access the UI here. The CLI client won't work, failing with `<Fault 1: 'method "core" is not supported'>`.

Always ensure the service's `ExecStart` protocol matches the exact interface the user expects to use.