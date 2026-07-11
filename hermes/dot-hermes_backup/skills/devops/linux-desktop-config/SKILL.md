---
name: linux-desktop-config
description: Guide for setting up a reproducible, Git-trackable Linux desktop configuration with an Obsidian documentation vault.
metadata:
  author: james
  version: "0.1"
---

# Linux Desktop Config

Guide for setting up a reproducible, Git-trackable Linux desktop configuration with an Obsidian documentation vault.

## When to load

Load this skill when the user asks to:
- Configure their desktop manager / window manager
- Create or maintain a config repo structure
- Set up Obsidian documentation for their system configs
- Add visual polish (compositor, launcher, bar, notifications, wallpaper)
- Mount extra drives via fstab
- Install GUI tools portably without root

## Standard workflow

1. Survey existing configs: read `~/.config/`, `~/.gtkrc-2.0`, `~/.config/xsettingsd/`, etc.
2. Identify the active session: `XDG_CURRENT_DESKTOP`, `DESKTOP_SESSION`, `XDG_SESSION_TYPE`.
3. Create repo at `~/desktop-setup/` with directories per subsystem (`i3/`, `gtk/`, `xsettingsd/`, `picom/`, `rofi/`, `dunst/`, etc.).
4. Write an `install.sh` that symlinks everything into place (idempotent, backs up `.bak`).
5. Install packages via system package manager (`dnf`/`apt`).
6. Document everything in `~/ObsidianVault/` with numbered markdown files linking back to the repo with `file:///` URIs.
7. Sync live configs back to the repo after each change.
8. Keep unfinished work as todos, do not block the session.

## Repo layout

```
~/desktop-setup/
├── README.md
├── scripts/
│   └── install.sh
├── i3/config
├── gtk/
├── xsettingsd/xsettingsd.conf
├── picom/picom.conf
├── rofi/theme.rasi
└── dunst/dunstrc
```

## Obsidian vault layout

```
~/ObsidianVault/
├── README.md              — hub page (Obsidian vault-relative wikilinks)
├── 01-Setup.md            — DE, WM, theme, keyboard decisions
├── 02-Configs-Overview.md — line-by-line breakdown of every config file + apply commands
├── 03-TODO-Features.md    — prioritized feature backlog
├── Hermes-Reference.md    — assistant behavior, privacy, session model
├── Notes/
├── Archive/
├── Templates/
└── Resources/
```

Use `file:///home/james/...` URIs inside Obsidian so links are clickable from the vault.

## Obsidian Sources/ — edit live configs inside Obsidian

Create symlinks back to real configs so Obsidian edits are live immediately:

```
mkdir -p ~/ObsidianVault/Sources/{i3,picom,rofi,dunst,gtk,xsettingsd}

ln -s ~/.config/i3/config                                    ~/ObsidianVault/Sources/i3/config
ln -s ~/desktop-setup/picom/picom.conf                       ~/ObsidianVault/Sources/picom/picom.conf
ln -s ~/desktop-setup/rofi/theme.rasi                        ~/ObsidianVault/Sources/rofi/theme.rasi
ln -s ~/desktop-setup/dunst/dunstrc                          ~/ObsidianVault/Sources/dunst/dunstrc
ln -s ~/.config/gtk-3.0/settings.ini                        ~/ObsidianVault/Sources/gtk/gtk-3-settings.ini
ln -s ~/.config/gtk-4.0/settings.ini                        ~/ObsidianVault/Sources/gtk/gtk-4-settings.ini
ln -s ~/.gtkrc-2.0                                           ~/ObsidianVault/Sources/gtk/gtk-2.0-settings
ln -s ~/.config/xsettingsd/xsettingsd.conf                  ~/ObsidianVault/Sources/xsettingsd/xsettingsd.conf
ln -s ~/.config/obsidian/obsidian.json                       ~/ObsidianVault/Sources/obsidian-obsidian.json
```

Obsidian file explorer may hide non-markdown files by default. Tell the user to turn on **show all files** in Settings → Files & Links. Record apply commands in README so changes don’t sit unapplied.

## fstab — mounting extra disks

This is the reusable recipe for additional NVMe, USB, or other data drives.

1. Identify devices and filesystems:
   ```
   lsblk -dpno NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT
   sudo blkid | grep -E 'TYPE="(ext4|xfs|ntfs|btrfs|vfat)"'
   ```
2. Create mount points under `/mnt/` as `root:root`:
   ```
   sudo mkdir -p /mnt/<label> /mnt/<label2>
   ```
3. Append to `/etc/fstab` by UUID. Recommended defaults:
   - Linux filesystems: `defaults 0 0`
   - NTFS writable by user: `ntfs uid=1000,gid=1000,umask=0077,windows_names 0 0`
   - FAT/vfat: `vfat umask=0077,shortname=winnt 0 1`
4. Apply and verify:
   ```
   sudo systemctl daemon-reload
   sudo mount -a
   mount | grep <mount>
   ```
5. Every filesystem needs its own mount point. Multiple partitions must not share the same mount target.

## SELinux read-only data-drive pitfall

After `mount -a`, an ext4 drive under `/mnt/<name>` can reject normal-user writes even though `mount` shows `(rw,relatime)`. `touch` from a normal user returns Permission denied; root can write.

Diagnose:
```
mount | grep <mount>
ls -Zd /mnt/<name>
```

If the label is unusual for `/mnt/`, e.g. `system_u:object_r:boot_t:s0`, normalize it:
```
sudo restorecon -Rv /mnt/<name>
```

Verify with `touch` and `rm` from the target user. After SELinux relabeling, NTFS and Linux filesystems both allow normal-user writes.

When `sudo` fails or is unavailable, extract a `.deb` without installing:

```bash
mkdir -p ~/Apps/<app> && cd ~/Apps/<app>
ar x /path/to/<app>_*.deb
tar -xf data.tar.xz
```

Then point the `.desktop` `Exec=` line to the local binary path and copy the icon into `~/.local/share/icons/hicolor/256x256/apps/`.

## i3 config pattern

New autostart entries belong together near the top of the file as `exec --no-startup-id <tool>` lines.

When replacing a keybind, replace the old `bindsym` block in place instead of leaving commented duplicates.

## Verification

- `tcsetattr: Inappropriate ioctl for device` in background-job logs is harmless harness noise. Verify GUI processes with `pgrep -c <name>`.
- `picom --diagnostics` reports real compositor status; look for `Use Overlay: Yes`.
- Do not validate GUI launchers/themes by running them headless; use synthetic CLI checks instead.

## Templates and references

- `templates/install.sh` — bootstrap instead of writing by hand
- `templates/dunstrc` — version-safe starting point for dunst 1.13.x
- `references/portable-deb-extraction.md` — distro/package notes and minimal portable GUI install recipe
- `references/fstab-mounts.md` — fstab entry templates for common Linux/Windows/vfat partitions plus apply/verify checklist
- `references/obsidian-sources-symlinks.md` — vault-visible symlink layout so live configs are editable from Obsidian

## Recommended apply command table for README.md

Keep this short table in `~/ObsidianVault/README.md` so edits don’t sit unapplied:

| File | Apply change |
|---|---|
| `Sources/i3/config` | `Super+Shift+C` |
| `Sources/picom/picom.conf` | `killall picom && picom --config ~/desktop-setup/picom/picom.conf` |
| `Sources/dunst/dunstrc` | `killall dunst && dunst` |
| `Sources/rofi/theme.rasi` | next rofi open |
| `Sources/gtk/*` | usually instant; relog if not |
| `Sources/xsettingsd/xsettingsd.conf` | restart xsettingsd or relog |

## Pitfalls

- **picom v13**: avoid deprecated target specifiers like `_NET_WM_STATE@:32c`. The hidden-window exclude line can be dropped entirely.
- **dunst v1.13**: dropped/ignores keys such as `allow_markup`, `bounce_freq`, `geometry`, `startup_notification`, and `urgency_*` inside `[exec]`.
- **Rofi**: headless runs usually time out. A `Rofi-WARNING: Failed to parse theme: ...` is real and should be fixed from syntax, not by retrying background runs.
- **NVIDIA + picom**: prefer `backend = "xrender"` over `glx` on NVIDIA if rendering is wrong.
- **Obsidian first launch**: vault registration happens in the app UI. Create the folder first and open it via Settings; do not expect the arg form to always register it.
- **Obsidian file explorer**: hides non-markdown files by default. Tell the user to enable **show all files** in Settings → Files & Links.
- **SELinux on `/mnt/` data drives**: a mislabeled mount can stay `rw` in `mount` but deny normal-user writes. Normalize labels with `restorecon -Rv`.
- **fstab mount point uniqueness**: never map multiple partitions to the same mount point. Each entry needs a distinct `/mnt/<name>`.
