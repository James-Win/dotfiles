---
name: lutris-wine-troubleshooting
description: Troubleshooting Lutris, Flatpak sandboxing, Wine versions, Proton runners, and Battle.net/Blizzard game installations on Linux.
category: linux-gaming
---

# Lutris and Wine Gaming Troubleshooting

This skill covers common pitfalls, debugging paths, and established fixes for running Windows game launchers (specifically Battle.net) through Lutris on Linux, dealing with Wine/Proton compatibility issues, and bypassing Flatpak sandbox quirks.

## Triggers
- The user is trying to install Battle.net, Epic Games, or other heavy Windows launchers via Lutris.
- Lutris runners (`umu-run`, `wine-ge`) are crashing during prefix setup.
- The user is encountering "Update Agent went to sleep" loops or `complete_async_poll` Wine crashes.
- The Lutris Flatpak UI is failing to save executable paths.

## Known Pitfalls & Solutions

### 1. Battle.net: "Update Agent went to sleep" Loop
Battle.net gets stuck waiting for `Agent.exe` because the Wine environment reports an older/unsupported Windows API level by default, or the Agent cache gets corrupted during a failed update.
**Fix:**
1. Force kill all ghost processes: `killall -9 Battle.net.exe Agent.exe wineserver wine`
2. Clear the corrupted cache explicitly: `rm -rf <prefix>/drive_c/ProgramData/Battle.net/Agent/Agent.9700/` and `<prefix>/drive_c/ProgramData/Battle.net/Agent/Agent.dat`
3. Force the Wine prefix to report Windows 10 for those specific executables using `reg add` instead of just `winecfg`:
   ```bash
   env WINEPREFIX="/path/to/prefix" flatpak run --command=wine net.lutris.Lutris reg add "HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults\\Agent.exe" /v "Version" /t REG_SZ /d "win10" /f
   env WINEPREFIX="/path/to/prefix" flatpak run --command=wine net.lutris.Lutris reg add "HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults\\Battle.net.exe" /v "Version" /t REG_SZ /d "win10" /f
   ```

### 2. Wine socket poll crash (`complete_async_poll` / `sock.c`)
During the Battle.net initial installer/updater downloading phase, aggressively spawning parallel network threads can crash the Wine server in modern builds of GE-Proton 8.26+, resulting in `Bad file descriptor` and `signaled_count failed`.
**Fix:**
Downgrade the local Lutris runner to a known stable legacy GE release specifically for the installation phase (e.g., `lutris-GE-Proton8-25-x86_64`). Manually download the `.tar.xz` to `~/.var/app/net.lutris.Lutris/data/lutris/runners/wine/` and configure the game to use it.

### 3. Battle.net: CEF UI Freezes / WSALookupServiceBegin errors
Battle.net's Chromium UI (CEF) heavily polls hardware network APIs (`WSALookupServiceBegin`) causing hard UI lockups in Wine. Flatpak sandboxing can also trigger `network_sandbox.cc` permission crashes, resulting in a blank/black launcher frame.
**Fix:**
To prevent freezes, bypass the sandbox crash, and fix the black rendering frame, set these exact arguments in the Lutris game configuration:
`--no-sandbox --disable-gpu-compositing`
(Do *not* use `--disable-gpu`, as it will leave the UI completely un-drawn/black after successful login.)

*(Note: It is also safer to directly target `Battle.net.exe` instead of `Battle.net Launcher.exe` once installed.)*

### 5. UMU-Run Crashes on Empty PROTONPATH
If Lutris uses `umu-run` by default and crashes instantly with `Environment variable not set or is empty: PROTONPATH` or `GE-Proton or UMU-Proton not found in ~/.local/share/Steam/compatibilitytools.d`, it assumes Steam Proton is already present.
**Fix:**
Create `~/.local/share/Steam/compatibilitytools.d/` and download/extract a `GE-Proton` `.tar.gz` into it, which fulfills `umu-run`'s dependency check.

### 6. AMD iGPU / NVIDIA Multi-GPU Vulkan Ambiguity (Vulkan error -7)
On an AMD Ryzen CPU with an iGPU (e.g. 7800X3D) alongside a discrete NVIDIA card, Battle.net's rendering engine commonly crashes explicitly on window creation due to ambiguity (`-7 Internal Vulkan error` / `eglInitialize`).
**Fix:**
Force the `VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json` and `WINE_DO_NOT_CREATE_DXGI_DEVICE_MANAGER=1` environment variables inside the specific Lutris game YAML config (`~/.var/app/net.lutris.Lutris/data/lutris/games/`).