# Dashboard systemd unit template

Drop-in unit file for `~/.config/systemd/user/hermes-dashboard.service`.

```ini
[Unit]
Description=Hermes Dashboard
After=network.target

[Service]
Type=simple
WorkingDirectory=%h
Environment=HOME=%h
Environment=USER=%u
Environment=PYTHONPATH=%h/.hermes/hermes-agent
ExecStart=%h/.local/bin/hermes dashboard --host 0.0.0.0 --insecure --port 9119
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

Notes:
- `%h` and `%u` are portable systemd specifiers for home and user.
- Remove `PYTHONPATH` once official packaging supports the host Python version.
- If local `hermes` wrapper scripts live elsewhere, update `ExecStart` to the verified absolute path (`readlink -f ~/.local/bin/hermes`).
