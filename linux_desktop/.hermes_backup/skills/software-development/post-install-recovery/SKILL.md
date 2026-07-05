---
name: post-install-recovery
description: >
  Restore a working Hermes Agent setup after a Linux distro reinstall
  when /home/james is preserved intact. Covers: verifying ~/.hermes
  survival, fixing systemd user services (linger + PATH inheritance),
  reinstalling Python deps (click, pip itself), and relaunching the
  dashboard and CLI.
  Trigger: the user says they reinstalled Fedora/Ubuntu/etc. and kept the
  home directory, or reports hermes dashboard/service 127 after a reboot.
  Do NOT confuse this with "hermes setup" for fresh first-time installs.
---

# Post-install recovery (distro reinstall, home preserved)

## Symptoms
- `hermes --help` works but dashboard service spins exit 127
- systemctl --user shows enabled-but-not-running user services
- `hermes doctor` says "Reinstall entry point"
- `python3 -c "import click"` fails after a Fedora package reinstall

## Assumptions (verify, don't blindly trust)
- `~/.hermes/` is intact (config.yaml, state.db, sessions/, skills/)
- Shell rc files survive
- The actual binary was at `~/.local/bin/hermes`

## Step-by-step recovery (small, safe batches; ask for output)

1. **Check what survived** -- one focused inspection, do not flood.
   ```bash
   ls -la ~/.hermes && ls -la ~/.bashrc && systemctl --user list-unit-files --state=enabled
   ```

2. **Fix system dependencies**
   - Fedora: `sudo dnf install -y python3-pip`
   - Ubuntu/Debian: `sudo apt-get install -y python3-pip`
   Then: `python3 -m pip install --user click`

3. **Enable linger** (required so systemd user services run without an active login session):
   ```bash
   loginctl enable-linger james
   ```

4. **Fix the systemd user unit PATH** -- THE PITFALL:
   - systemd user services do **not** inherit your interactive shell PATH.
   - If ExecStart uses `env` or `hermes` directly, the service cannot find
     `~/.local/bin/hermes` and exits 127.
   - Always `Environment=PATH=...` in user unit files that rely on `~/.local/bin`.
   - Example unit line:
     ```
     Environment=PATH=/home/james/.local/bin:/home/james/bin:/usr/local/bin:/usr/bin:/bin
     ```
   - After editing: `systemctl --user daemon-reload && systemctl --user restart <unit>`

5. **Verify** -- do not assume success; check:
   ```bash
   systemctl --user status <unit> | tail -15
   curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:9119/
   ss -ltnp | grep :9119
   ```

## Off-limits during recovery
- Do **not** touch the Discord bot bridge (`discord-hermes-bot`) unless the user explicitly brings it up.
  If threatened with scope creep, pause and ask.

## Session evidence
For full command transcripts and root-cause notes from a successful Fedora 44 recovery,
see `references/fedora-reinstall-2026-07-02.md`.

## Verify-before-celebrate
- Active (running) is not proof; check HTTP 200/302 and `ss -ltnp`.
- Exit 127 in the journal = PATH/binary-not-found, not "needs driver deps".
