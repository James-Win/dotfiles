# Glances Monitoring & Remote Setup Pitfalls

## Server Mode vs Web Mode
Glances has two distinct background server modes which are often confused:
* `-s` (XML-RPC Server): Legacy mode. Expects remote terminal connections from `glances -c <ip>`. **Does not serve a web UI**, and will throw `xmlrpc.client.Fault` if queried incorrectly.
* `-w` (Web Server): Modern mode. Serves the classic terminal UI directly into a web browser at `http://<ip>:61208`.

When writing a `systemd` service for a headless Proxmox node, prefer the web server mode (`-w`) and direct the user to access it via their web browser.

## The xterm-kitty Nano Crash
James uses the `kitty` terminal emulator locally. When SSHing into a standard Proxmox or Debian host, the `xterm-kitty` terminfo is missing. This causes text editors like `nano` to immediately crash on open with `Error opening terminal: xterm-kitty.`.

**Rule:** Never instruct the user to run `nano`, `vim`, or other interactive editors for remote file creation over SSH.
**Always provide `cat << 'EOF' > /path/to/file` blocks for painless, crash-free remote file creation.**