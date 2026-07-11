---
name: reproducible-linux-desktop
description: >
  Transform a Linux X11 desktop into a reproducible config-as-code setup:
  symlink-based dotfiles repo, portable app installs, and an Obsidian
  documentation vault linked back to the repo.
  Trigger: user asks to organize, back up, GitHub-ify, or repoint their
  i3/sway/Openbox session; set up a documentation vault; install portable
  apps like Obsidian; or "make my desktop look nice."
  Load `linux-desktop-switch` first if the user is switching DEs/WMs.
---

# Reproducible Linux Desktop

Turn an existing i3 (or similar) session into a tracked, portable, and
documented desktop. Everything is symlink-based so config edits flow from one
repo to `~/.config` and into an Obsidian vault.

---



## Step 1 — Survey the live session

```bash
echo "DE: $XDG_CURRENT_DESKTOP / $DESKTOP_SESSION"
echo "TYPE: $XDG_SESSION_TYPE"
ls ~/.config/
ls ~/.config/i3/ ~/.config/gtk-{3,4}.0/ ~/.config/xsettingsd/ ~/.config/dunst/ 2>/dev/null
cat ~/.config/i3/config ~/.config/xsettingsd/xsettingsd.conf 2>/dev/null | wc -l
find ~/.config -maxdepth 1 -type l 2>/dev/null | wc -l
which dmenu rofi picom compton dunst feh i3lock i3status
```

Record the session as the source of truth. Don't blindly regenerate from guides;
copy actual live values.

---



## Step 2 — Create the repo structure

Use real directories, not markdown-only scaffolding:

```
~/desktop-setup/
├── README.md
├── scripts/
│   └── install.sh
├── i3/
├── gtk/
├── xsettingsd/
├── picom/
├── dunst/
├── rofi/
└── etc/
```

Copy only real files:

```bash
cp ~/.config/i3/config ~/desktop-setup/i3/config
cp ~/.config/xsettingsd/xsettingsd.conf ~/desktop-setup/xsettingsd/xsettingsd.conf
cp ~/.config/gtk-3.0/settings.ini ~/desktop-setup/gtk/gtk-3-settings.ini
cp ~/.config/gtk-4.0/settings.ini ~/desktop-setup/gtk/gtk-4-settings.ini
cp ~/.gtkrc-2.0 ~/desktop-setup/gtk/gtk-2.0-settings
```

---



## Step 3 — Write `install.sh`

Symlink everything into place. The `link_or_copy` pattern survives re-clones
and makes the repo the single source of truth.

```bash
link_or_copy() {
  local src="$1"
  local dst="$2"
  if [ -e "$dst" ] && [ ! -L "$dst" ]; then
    echo "Backing up existing $dst to ${dst}.bak"
    mv "$dst" "${dst}.bak"
  fi
  mkdir -p "$(dirname "$dst")"
  ln -sf "$src" "$dst"
  echo "Linked $src → $dst"
}
```

Add a step for every new config directory you create. Idempotent: safe to
re-run after a pull.



## Step 4 — Add each visual/functional layer

Order matters: compositor before bar/launcher so the window rules make sense.

### A. picom (compositor)

1. `sudo dnf install -y picom` (Fedora) or distro equivalent.
2. Write `picom/picom.conf` — shadows, fading, terminal transparency, rounded corners.
   Required: `backend = "glx";` and under it `vsync = true;` for tear-free rendering.
3. Add `exec --no-startup-id picom --config ~/desktop-setup/picom/picom.conf` to the **top** of `i3/config`, before `xss-lock`.
4. Add the picom symlink step to `scripts/install.sh`.
5. Reload with `Mod+Shift+C`.
6. Verify: `pgrep -c picom` should be 1; `--diagnostics` should show `Use Overlay: Yes`.

**Modern picom requirement:** `backend` must be set explicitly in `picom.conf`. If omitted, picom exits with `Failed to create new session`. Remove deprecated `!gibberish` prefixes and `@:32c` / Format `32` specifiers from shadow excludes.

### B. rofi (launcher)

1. `sudo dnf install -y rofi` or build from source.
2. Replace dmenu keybind with:
   ```
   bindsym $mod+d exec --no-startup-id rofi -modi drun,run -show drun
   ```
3. Add `name = 'rofi'` to `shadow-exclude` and `fade-exclude` in `picom.conf`.

### C. dunst (notifications)

1. `sudo dnf install -y dunst`.
2. Copy `/usr/share/dunst/dunstrc` to `~/desktop-setup/dunst/dunstrc`.
3. Edit: position, font, urgency colors, icon theme.
4. Add `exec --no-startup-id dunst` to `i3/config`.
5. Add `name = 'dunst'` exclusions in `picom.conf`.

### D. feh (wallpaper)

Keep it simple: one line in `i3/config`, e.g.
```
exec --no-startup-id feh --bg-fill ~/Pictures/wallpapers/current.jpg
```
Use a `current.jpg -> ../04-june/sunset.jpg` symlink if you want rotation
without changing the config.

---



## Step 5 — Keep the repo in sync

After changing live configs, copy back to the repo before closing the session:

```bash
cp ~/.config/i3/config ~/desktop-setup/i3/config
cp ~/.config/picom.conf ~/desktop-setup/picom/picom.conf
```

Make this a habit before you switch tasks or power off.

---



## Step 6 — Obsidian documentation vault

Location: `~/ObsidianVault/`

Subdirectories:

```
~/ObsidianVault/
├── README.md              — hub page (Obsidian vault-relative wikilinks)
├── 01-Setup.md            — DE, WM, theme, keyboard decisions
├── 02-Configs-Overview.md — line-by-line breakdown of every config file
├── 03-TODO-Features.md    — prioritized feature backlog
├── Notes/
├── Archive/
├── Templates/
└── Resources/
```

**Obsidian-launcher setup.** If distributing portable Electron apps from
`~/Apps/<name>/<suite>/binary`, write the `.desktop` file with absolute paths
under `~/.local/share/applications/` and the icon under
`~/.local/share/icons/hicolor/<size>/apps/`. Do not require `sudo` for
`/opt/Obsidian`; use `~/Apps/obsidian/` instead so the whole desktop stack is
user-owned.

**Cross-link.** In Markdown files inside `~/ObsidianVault/`, link to the live
config file with `file://` protocol so Obsidian resolves it directly:
`[i3 config](file:///home/james/desktop-setup/i3/config)`.

---



## Pitfalls

### KDE settings override xsettingsd

If `~/.config/kglobalshortcutsrc`, `kdeglobals`, or `plasma-localerc` exist and
the KDE session tools still run, they will overwrite `xsettingsd` and GTK font
settings at logout. Either remove KDElibs packages, or add `plasma-localed`
autostart blockers. Test with `xrdb -query | grep Xft` after a clean logout.

### Non-existent fonts in `dmenu` and GTK

Your i3 dmenu bind may reference a font not present on a fresh machine:
`-nf '#BBBBBB' -nb '#222222' -sb '#005577' -sf '#EEEEEE' -fn 'monospace-10'`.
`monospace-10` is resolved by fontconfig; verify with `fc-list | grep -i monospace`.
If it fails silently, dmenu falls back to the system default and colors can
vary by theme.

### Theme selection and validation

Rofi v2 on Fedora ships with verified themes under `/usr/share/rofi/themes/`
(e.g. `Arc-Dark.rasi`, `gruvbox-dark.rasi`). If a freshly written custom theme
fails with `Rofi-WARNING: Failed to parse theme`, copy a known-good system
theme into the repo first, then drift colors. Hand-rolled `* { font: ... }`
Rofi 1.x-style themes can silently fail on Rofi 2.

### Rofi is interactive — cannot be tested headlessly

`rofi -show drun` is a blocking GUI picker. `timeout N rofi ...` will always
report exit 124 from a non-interactive session. Cycle/exits only fire from real
keyboard input (Enter/Escape) or `xdotool`. Do not treat timeout or pidfile
warnings as a broken install.

---

Use `sudo` for dnf as normal. If the user does not have SUDO_PASSWORD,
fall back to portable `.deb` extraction via `ar x <deb> && tar -xf data.tar.xz`
into `~/Apps/`; this is how Obsidian was installed here and requires no root.

### Thunar on i3 needs thunar-volman

Thunar does not manage external volumes by default unless `thunar-volman` is installed, even with `udisks2` already running. After install, restart Thunar once; plug events and `/mnt` browsing work immediately.

### NTFS mounts on Fedora + SELinux

NTFS FUSE mounts are writable, but inherited directory labeling can block write from a normal user session. After creating `/mnt/...` mountpoints, verify with `ls -Zd`. If the label is not `mnt_t`, run `sudo restorecon -Rv /mnt/<mountpoint>` once; ownership then behaves normally.

### NTFS fstab

Use `ntfs-3g`-style FUSE options in `/etc/fstab` for NTFS: `uid=1000,gid=1000,umask=0077,windows_names`. This gives one trusted user ownership and avoids permission surprises.

For long-lived daemons (picom, dunst, etc.), use `terminal(background=true)` with
`notify_on_complete=true` so Hermes alerts on exit. Daemons that never exit
should omit notify_on_complete and be checked via `pgrep`. Never run them via
`&` in the foreground terminal — the harness rejects this pattern.

- **picom diagnostics, not daemon mode**

Sysadmins should not run picom directly from the user session as a background job
in the shell — it should be started via `i3/config` `exec --no-startup-id`. For
debugging, `picom --diagnostics` prints to stderr; `--help` exits 1

---