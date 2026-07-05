---
name: fedora-linux-triage
description: Triage and resolve Fedora issues with dnf, systemd, journalctl, SELinux, and firewalld-aware guidance.
metadata:
  source: LobeHub github-awesome-copilot-fedora-linux-triage v1.0.1
  github: https://github.com/github/awesome-copilot/blob/main/skills/fedora-linux-triage/SKILL.md
---

# Fedora Linux Triage

Diagnose and resolve Fedora issues using Fedora-appropriate tooling and practices.

## When to Use

Use this skill for Fedora Linux issues involving:

- Failed package installs or dependency conflicts
- Broken services after updates
- Boot, kernel, or initramfs regressions
- SELinux access denials or mislabeled files
- `firewalld` connectivity issues
- `dnf`, `rpm`, `systemd`, or `journalctl` troubleshooting

## Inputs to Gather

- Fedora release: `cat /etc/fedora-release`
- Kernel: `uname -r`
- Problem summary: exact symptom and when it started
- Constraints: no sudo, offline, production machine, cannot reboot, etc.
- Recent updates: `dnf history list --reverse | tail -20`

## Instructions

1. Confirm Fedora release and environment assumptions.
2. Provide a step-by-step triage plan using `systemctl`, `journalctl`, and `dnf`.
3. Offer remediation steps with copy-paste-ready commands.
4. Include verification commands after each major change.
5. Address SELinux and `firewalld` considerations where relevant.
6. Provide rollback or cleanup steps.

## Output Format

- **Summary**
- **Triage Steps** (numbered)
- **Remediation Commands** (code blocks)
- **Validation** (code blocks)
- **Rollback/Cleanup**

## Core Diagnostic Commands

### Release and system state

```bash
cat /etc/fedora-release
uname -r
systemctl --failed
systemctl get-default
```

### Package management

```bash
dnf history list --reverse | tail -20
dnf history info <ID>
dnf repoquery --unsatisfied
sudo dnf check
rpm -Va
```

Use `dnf history undo <ID>` or `dnf history rollback <ID>` only after reviewing the transaction and confirming scope.

### Systemd services

```bash
systemctl status <unit> --no-pager
journalctl -u <unit> -b --no-pager
journalctl -xe --no-pager
systemctl list-dependencies <unit>
```

### SELinux

```bash
getenforce
sudo ausearch -m AVC,USER_AVC -ts recent
sudo sealert -a /var/log/audit/audit.log
ls -Z <path>
```

Prefer durable context fixes such as `semanage fcontext` + `restorecon` instead of disabling SELinux. Temporary `setenforce 0` is diagnostic only and requires explicit user confirmation.

### firewalld

```bash
sudo firewall-cmd --state
sudo firewall-cmd --get-active-zones
sudo firewall-cmd --list-all
sudo firewall-cmd --list-services
sudo firewall-cmd --list-ports
```

## Remediation Principles

- Start read-only: collect logs, service status, package history, and SELinux AVCs before changing state.
- Explain why each command matters; avoid command dumps.
- Make one major change at a time and verify it before continuing.
- Prefer Fedora-native package and service management (`dnf`, `rpm`, `systemctl`, `journalctl`, `restorecon`, `semanage`).
- Do not permanently disable SELinux or firewall protections as a fix.
- For destructive or broad changes (`dnf rollback`, package removals, service masks, firewall permanent changes, reboots), ask for confirmation.

## Rollback/Cleanup Examples

```bash
# Inspect before rollback
dnf history info <ID>

# Undo a specific transaction after confirmation
sudo dnf history undo <ID>

# Re-enable a service if masking was temporary
sudo systemctl unmask <unit>
sudo systemctl enable --now <unit>

# Restore SELinux labels after policy/path changes
sudo restorecon -Rv <path>
```

## Verification Checklist

- [ ] Fedora release and kernel identified
- [ ] Logs captured for the failing service or subsystem
- [ ] Recent `dnf` transactions checked when issue followed an update
- [ ] SELinux AVCs checked when permissions look suspicious
- [ ] `firewalld` checked when network access is involved
- [ ] Each remediation has a validation command
- [ ] Rollback/cleanup path documented
- [ ] For Flatpak apps and games (like Lutris/Battle.net), check the `references/lutris-battlenet-troubleshooting.md` document for known dual-GPU, sandbox, and runner workarounds.
