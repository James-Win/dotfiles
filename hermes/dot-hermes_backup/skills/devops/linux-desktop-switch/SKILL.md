---
name: linux-desktop-switch
description: >
  Replace or swap a Linux desktop environment / window manager, including DM
  selection, D-Bus/polkit cleanup, package removal, and bootloader refresh.
  Works for any source DE and any target WM/DE; the references/ subdir keeps
  distro-specific gotchas decoupled from the main procedure.
  Use when: switching from KDE/GNOME/Xfce to i3/sway/hyprland/another DE.
  Load `systematic-debugging` first if the DM fails to start.
---

# Linux Desktop Switch

Replacing a full desktop stack on an RPM-based Linux system. Not just
"install i3" — covers running login path, DM transition, clean uninstall of
the old DE, and avoiding the distro meta-package traps.

---

## Pre-flight (do this before installing anything)

1. Record current state:
   ```
   echo "DE: $XDG_CURRENT_DESKTOP"
   echo "SESSION: $XDG_SESSION_TYPE"
   rpm -qa | grep -iE '^(plasma|gnome-session|xfce|cinnamon|mate|budgie)' | head -20
   systemctl get-default
   ls -la /etc/systemd/system/display-manager.service
   ```
2. Identify login path:
   - GDM / SDDM / LightDM unit installed? `systemctl list-unit-files | grep -E 'gdm|sddm|lightdm'`
   - Auto-login? `ls /etc/systemd/system/*.wants/ | grep getty`
   - startx user? `ls -la ~/.xinitrc ~/.xsession 2>/dev/null`
3. Note the current DM's display-manager.service symlink — you will need to
   repoint it.

---

## Step 1 — Choose and install a display manager

| DM | Notes |
|---|---|
| GDM | Fedora default. Heavy GNOME dependencies. Zero Qt/KDE baggage, owns D-Bus name cleanly. |
| SDDM | Lightweight, Qt-based. Fine choice, but the Qt stack may pull plasma-adjacent libs on Fedora. |
| LightDM | Lightest. **Pitfall on Fedora+former-KDE**: the `plasmalogin` package ships a D-Bus system policy that restricts `org.freedesktop.DisplayManager` ownership to root only. LightDM runs as the `lightdm` user and cannot own that bus name — it aborts before X starts. Fix options: (A) patch the D-Bus xml to add a `<policy user="lightdm">` block (temporary, will be cleaned up when plasmalogin package is purged); (B) use GDM or SDDM instead. |

**Install:**
```
sudo dnf install -y <dm-package> <dm-gtk|greeter-package>
```

**Repoint the DM symlink if needed:**
```
sudo rm -f /etc/systemd/system/display-manager.service
sudo ln -s /usr/lib/systemd/system/<dm>.service /etc/systemd/system/display-manager.service
sudo systemctl daemon-reload
```

A package's `%post` may fail to preset the symlink if another DM already
owns it — this manual step is normal and expected.

---

## Step 2 — Install the new WM/DE + minimal apps

Install the target stack and a terminal, file manager, editor:
```
sudo dnf install -y <wm-package> i3status dmenu <terminal> <fm> <editor>
```

Enable and start the new DM before removing anything:
```
sudo systemctl enable --now <dm>
```

Verify it starts:
```
systemctl is-active <dm>
```

If it fails and LightDM is the DM, the `plasmalogin` D-Bus policy described
in Step 1 is the likely cause.

---

## Step 3 — Remove the old DE packages

### Fedora-specific meta-package rule (CRITICAL)

Never remove these Fedora desktop identity meta-packages:
- `fedora-release-kde-desktop`
- `fedora-release-identity-kde-desktop`
- (GNOME variant: `fedora-release-identity-workstation`, etc.)

They satisfy `system-release` requirements. Removing them breaks `dnf`
dependency resolution for core packages like `setup`.

`dnf remove` will fail with conflicting requests rather than a clear error
here — leave them in place; they are harmless without the actual DE stack.

### Bypassing protected_packages

Fedora protects `plasma-desktop` from removal by default. Override:
```
sudo dnf -y remove --setopt=protected_packages= <pkg-list>
```

Leaving `protected_packages` completely empty is safe for this one-shot
transaction; dnf reloads defaults on the next run.

### Target only the old DE's own packages

Do not aggressively glob `qt6-*` or `*qt6*` — non-KDE apps share Qt6 libs.
Use the package list captured in pre-flight and filter to the old DE's
specific packages (e.g., `^plasma`, `^kde-`, `^kf6-`, `^libplasma`,
`^libkdepim`, `akonadi`, `baloo`, `dolphin`, `konsole`, `ark`, `elisa`,
`okular`, `kate`, `polkit-kde`, `xdg-desktop-portal-kde`, etc.).

---

## Step 4 — Cleanup

1. Remove the old DM (LightDM if you installed GDM, etc.) to reclaim its
   deps (lightdm pulls `libxklavier`, `desktop-backgrounds-compat`, etc.):
   ```
   sudo dnf remove -y <old-dm>
   ```
2. Clean up any leftover D-Bus/polkit files — they usually go away with the
   package, but verify:
   ```
   ls /usr/share/dbus-1/system.d/ | grep -i <old-de>
   ls /usr/share/polkit-1/rules.d/ | grep -i <old-de>
   ```
   The `plasmalogin` D-Bus policy disappears with the `plasmalogin` package,
   but confirm if the DM change happened before the full purge.
3. Update GRUB (local bootloader, safe):
   ```
   # Detect UEFI vs BIOS
   [ -d /sys/firmware/efi ] && EFI=1 || EFI=0
   if [ $EFI -eq 1 ]; then
     # On UEFI Fedora the only valid target is /boot/grub2/grub.cfg
     sudo grub2-mkconfig -o /boot/grub2/grub.cfg
   else
     sudo grub2-mkconfig -o /boot/grub2/grub.cfg
   fi
   ```
   **Do NOT write to `/boot/efi/EFI/fedora/grub.cfg`** — that is a wrapper
   and grub2-mkconfig will refuse to overwrite it.

---

## Step 5 — Verify

```
systemctl is-active <new-dm>
systemctl get-default
rpm -qa | grep -iE '^plasma|^kde-|^kf6-|^libplasma|^libkdepim|^akonadi' || echo 'clean'
XDG_CURRENT_DESKTOP=  # should be empty or 'i3' after login
```

Reboot, select the new DE/WM session from the DM's session chooser, confirm
the panel/tiling behavior.

---

## Notes

### fedora-kde-plasmalogin reference (formerly references/fedora-kde-plasmalogin.md)

Symptom observed in this session: LightDM immediately exits with
`Failed to use bus name org.freedesktop.DisplayManager`.
Root cause: `plasmalogin` D-Bus policy restricts ownership to root only;
LightDM runs as user `lightdm` and cannot acquire the bus name.
Fix options: (A) patch the D-Bus xml to add a `<policy user="lightdm">`
block — this file is removed when plasmalogin package is purged, so treat
it as transient; (B) use GDM (unaffected, but pulls GNOME-Shell stack
~70–80 MB); (C) use SDDM (Qt-based, smaller than GDM).

Verify:
```
sudo dbus-send --system --print-reply --dest=org.freedesktop.DBus \
  /org/freedesktop/DBus org.freedesktop.DBus.ListNames | grep -i display
# should show: string "org.freedesktop.DisplayManager"
systemctl status lightdm.service
# Active: active (running)
```

Cleanup after KDE purge:
```
ls /usr/share/dbus-1/system.d/ | grep plasmalogin
```
If anything remains, remove it manually.

---

### dnf-protected-packages reference (formerly references/dnf-protected-packages.md)

`dnf remove` blocks removal of `plasma-desktop` by default on Fedora.
Override with `--setopt=protected_packages=`. Do NOT include
`fedora-release-identity-kde-desktop` or `fedora-release-kde-desktop` in
the removal list — they are the distro identity metapackages required by
`setup → system-release`. Removing them breaks dnf dependency resolution.

---

### grub-uefi-note reference (formerly references/grub-uefi-note.md)

On Fedora 44 UEFI the only valid grub2-mkconfig target is
`/boot/grub2/grub.cfg`. Writing to `/boot/efi/EFI/fedora/grub.cfg` fails
with "will overwrite the GRUB wrapper." Detect UEFI with
`[ -d /sys/firmware/efi ] && echo UEFI || echo BIOS`.
