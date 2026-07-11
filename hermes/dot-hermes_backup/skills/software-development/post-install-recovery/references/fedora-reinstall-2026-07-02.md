# fedora-reinstall-2026-07-02

Session date: 2026-07-02. Distro: Fedora 44. Hermes: 0.15.2. Python: 3.14.3.

## Observed state at start of session
- `~/.hermes/` fully intact (config.yaml, state.db, sessions/, skills/, memories/, auth.json)
- `~/.local/bin/hermes` present; `pip show hermes-agent` returned nothing because python3 -m pip was missing
- Shell rc: only `~/.bashrc` needed
- Discord bridge `~/discord-hermes-bot`: not present; off-limits per user.

## systemd user unit BEFORE fix
Path: `/home/james/.config/systemd/user/hermes-dashboard.service`

Problems:
1. `Linger=no` -- user services die after logout/reboot.
2. No `Environment=PATH=...` -- `env hermes` could not find `~/.local/bin/hermes` from non-interactive context, exit 127.

## Commands run (successful)
```bash
sudo dnf install -y python3-pip
python3 -m pip install --user click
loginctl enable-linger james
systemctl --user daemon-reload
systemctl --user restart hermes-dashboard.service
```

## Verification
```
Active: active (running) since Jul 02 13:56:47
HTTP 302 on 127.0.0.1:9119
LISTEN 0.0.0.0:9119 users:(hermes,pid=17962,fd=7)
URL: http://192.168.0.176:9119
```

## Root-cause notes
- `EXECMAINSTATUS=127` + `env: 'hermes': No such file or directory` = PATH problem, not Python-dep.
- `EXECMAINSTATUS=127` + `ImportError: No module named 'click'` = Python-dep. Check journal to distinguish.
- Fedora 44 reinstall removed `python3-pip`. Hermes 0.15.2 wheels need `click`; pip metadata was wiped.
