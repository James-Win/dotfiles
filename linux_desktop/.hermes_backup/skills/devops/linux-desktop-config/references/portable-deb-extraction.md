# Portable Linux GUI App Install

Observed on this system: Fedora 44, NVIDIA RTX 3060 LHR, X11 + i3wm, dnf/rpmfusion repos, sudo not available in this shell context, flatpak remote unavailable without manual setup.

## Reproducible recipe

Obsidian 1.8.9 deb install, portable:

```bash
mkdir -p ~/Applications && cd ~/Applications
curl -L -o obsidian.deb \
  "https://github.com/obsidianmd/obsidian-releases/releases/download/v1.8.9/obsidian_1.8.9_amd64.deb"
mkdir -p ~/Apps/obsidian && cd ~/Apps/obsidian
ar x ~/Applications/obsidian.deb
tar -xf data.tar.xz
```

Desktop entry requires full path:
```
Exec=/home/james/Apps/obsidian/opt/Obsidian/obsidian %U
Icon=/home/james/.local/share/icons/hicolor/256x256/apps/obsidian.png
```

Recommended launch flags on X11:
```
--no-sandbox --ozone-platform=x11 --disable-gpu-sandbox --disable-setuid-sandbox
```

## Observed failures / why they happened

- `sudo apt install ...` → Fedora does not ship `apt`.
- `sudo dnf install ...` → sudo password unavailable in this shell context.
- Moving to `/opt/` via `sudo` failed for the same password reason.
- `dpkg-deb` was not installed; `ar` + `tar` was the working substitute.
- `which` checks sometimes returned empty lists and exited non-zero.
- `terminal(background=true)` with `&` inside was rejected; use background mode with `notify_on_complete=true` instead.

## Version used in session

- Obsidian 1.8.9 (debian package)
- Picom 0:13-1.fc44
- Rofi 0:2.0.0-2.fc44
- Dunst 1.13.2 (compiled 2026-03-19)
