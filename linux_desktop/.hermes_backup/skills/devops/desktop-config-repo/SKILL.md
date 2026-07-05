---
name: desktop-config-repo
description: >
  Scaffold a version-controlled Linux desktop config repo from an existing
  running session. Covers surveying wm/gtk/session state, copying existing
  configs into a portable repo layout, adding a README and idempotent install
  script, and extending the repo with documentation tools like Obsidian.
  Trigger: "set up my desktop config repo", "desktop setup for github",
  or any request to version-control or document an existing Linux WM/DE config.
---

# Desktop Config Repo

## When to use

Load this when the user asks to turn their current desktop configuration
into a GitHub-ready repo.

## Preferred repo layout

```
<repo-root>/
├── README.md
├── install.sh                          # idempotent symlink installer
├── i3/
│   └── config
├── gtk/
│   ├── gtk-2.0-settings
│   ├── gtk-3-settings.ini
│   └── gtk-4-settings.ini
├── xsettingsd/
│   └── xsettingsd.conf
└── <extension>/
    └── ...
```

Keep the in-repo paths flat/known so `install.sh` can predict destinations.

## Step 1 - Survey current desktop state

Preferred probe order:

1. `echo "$XDG_CURRENT_DESKTOP" "$DESKTOP_SESSION" "$XDG_SESSION_TYPE" "$XDG_WM"`
2. `ls -la ~/.config/`
3. Read existing config sources: `~/.config/i3/config`, `~/.config/gtk-3.0/settings.ini`,
   `~/.gtkrc-2.0`, `~/.config/xsettingsd/*`, `~/.config/gtk-4.0/settings.ini`
4. Detect companions: `which i3 i3status dmenu xss-lock i3lock rofi polybar picom ...`

Survey before copying. Do not assume the user has a config dir tree until `ls` confirms it.

## Step 2 - Scaffold repo and copy existing configs

1. `mkdir -p <repo-root>/{i3,gtk,xsettingsd,scripts,etc}`
2. `cp` each existing config into the flat in-repo path
3. Write a README with: session type, current theme/font/launcher/bar/lock stack,
   install command, and a customization checklist
4. Write `scripts/install.sh` as an idempotent symlink installer that backs up
   existing files to `.bak` before linking

## Step 3 - install.sh requirements

- Shebang: `#!/usr/bin/env bash` + `set -euo pipefail`
- Resolve repo root from `SCRIPT_DIR` so the script works from any cwd
- Symlink, do not copy, so the repo remains the source of truth
- If the destination exists and is not a symlink, move it to `dst.bak` first
- Be explicit about each destination being installed

## Step 4 - Extend with documentation tools

Common extensions when the user asks for documentation:

### Obsidian vault

Preferred layout:
```
<vault-root>/
├── README.md
├── Vault-Setup.md
├── Desktop-Setup.md
├── Notes/
├── Archive/
├── Templates/
└── Resources/
```

See `references/obsidian-portable-linux.md` for the portable install sequence.

### Markdown note conventions

- Use `.md` with YAML frontmatter when the note is a top-level doc
- Link related notes with `[[WikiLink]]` syntax
- Prefer `patch` for anchored edits; prefer `write_file` for whole-note creation

## Step 5 - Verify

After writing install.sh, run it once in dry-thought and confirm:
- every destination exists and is a symlink
- the original file is preserved under `.bak` if it existed beforehand

After installing Obsidian or other GUI tools:
- confirm process visibility: `ps aux | grep <app>`
- for Electron apps on X11, required flags: `--no-sandbox --ozone-platform=x11 --disable-gpu-sandbox --disable-setuid-sandbox`

## Pitfalls

- **Diving into installs before surveying state.** Many `~/.config/<wm>` dirs do not exist yet; always `ls` + read first.
- **Copying instead of symlinking.** If `install.sh` copies, the repo stops being the source of truth.
- **Forgotten `.bak` handling.** Without backing up existing files, the user loses their prior config on first install.
- **Hardcoded `cwd` assumptions.** `install.sh` should compute repo root from `SCRIPT_DIR`, not assume it runs from a particular directory.
- **Obsidian vault registration.** Obsidian only recognizes a folder as a vault when the user opens it via the app UI or launches the binary with the folder path as the first argument; pre-creating the folder is not enough.
- **Electron sandboxing on minimal installs.** On X11 + user-space installs, `--no-sandbox` etc. are almost always required.
- **sudo in scripts for user-space tools.** If the user lacks sudo, prefer a portable install under `~/Apps/` and point the `.desktop` entry to that path rather than fighting with `dpkg`/`apt`.
- **Desktop entries from user-local paths.** When the `.desktop` `Exec=` points outside `/opt` or `/usr/bin`, also hardcode an absolute `Icon=` path instead of a theme name so it renders in dmenu/rofi.
