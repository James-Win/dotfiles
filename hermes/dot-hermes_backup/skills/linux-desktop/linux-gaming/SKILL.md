---
name: linux-gaming
description: Troubleshooting and configuring Linux gaming environments (Lutris, Wine, Flatpaks).
category: linux-desktop
---

# Linux Gaming & Launcher Troubleshooting

## Trigger
When the user is trying to install or run games, game launchers (like Battle.net, Steam), or compatibility layers (Proton, Wine, Lutris) on Linux.

## Pitfalls and Known Quirks

### Lutris Flatpak: `umu-run` Prefix Creation Crashes
- **Symptoms**: 
  - Missing executable errors (e.g., `Battle.net Launcher.exe could not be found`).
  - In the Lutris CLI/debug logs, `umu-run` crashes silently: `Umu exited unexpectedly during prefix creation (return code: 0)`.
  - Heavy DLL linking failures (`dxgi.dll`, `d3d11.dll`) immediately follow because the Wine prefix (`drive_c/`) was never fully bootstrapped.
  - Or, an explicit error: `FileNotFoundError: Environment variable not set or is empty: PROTONPATH`.
- **Root Cause**: The Flatpak version of Lutris (`net.lutris.Lutris`) strictly sandboxes runners. The default `umu` runner often fails silently if the `~/.local/share/Steam/compatibilitytools.d/` folder is empty or missing a valid Proton GE release, as it expects to use Steam's Proton installation.
- **Fix / Workaround**:
  1. Manually download a GE-Proton release (e.g. 8-25) directly into the compatibility tools folder:
     ```bash
     mkdir -p ~/.local/share/Steam/compatibilitytools.d/
     cd /tmp && wget "https://github.com/GloriousEggroll/proton-ge-custom/releases/download/GE-Proton8-25/GE-Proton8-25.tar.gz"
     tar -xzf GE-Proton* -C ~/.local/share/Steam/compatibilitytools.d/
     ```
  2. Initiate the game installer (e.g., `flatpak run net.lutris.Lutris -d lutris:install/battlenet`).
  3. The `umu` runner will now find Proton and successfully bootstrap the prefix.

### Wine Socket Polling Crash (`complete_async_poll` Assertion)
- **Symptoms**:
  - The Battle.net (or similar) installer crashes mid-download with `wineserver: ../src-wine/server/sock.c:1153: complete_async_poll: Assertion 'output->count == signaled_count' failed.`
  - `wine client error: Bad file descriptor`
- **Root Cause**: The Battle.net updater opens dozens of parallel download threads rapidly, triggering an assertion bug in the network socket polling of newer Wine-GE / Proton servers (e.g., 8-26+).
- **Fix / Workaround**:
  1. Clean the broken prefix directory (e.g. `rm -rf ~/Games/battlenet`).
  2. Download the specific `wine-lutris-GE-Proton8-25-x86_64` runner directly into Lutris' runner directory, as it uses an older, stable socket polling mechanism:
     ```bash
     mkdir -p ~/.var/app/net.lutris.Lutris/data/lutris/runners/wine/
     wget "https://github.com/GloriousEggroll/wine-ge-custom/releases/download/GE-Proton8-25/wine-lutris-GE-Proton8-25-x86_64.tar.xz"
     tar -xf wine-lutris-GE-Proton8-25-x86_64.tar.xz -C ~/.var/app/net.lutris.Lutris/data/lutris/runners/wine/
     ```
  3. Re-run the installer via Lutris but manually override the runner to `lutris-GE-Proton8-25-x86_64` in the install configuration prompt.

### Harmless Cosmetic Hardware Scans
- **Symptoms**:
  - `/usr/lib/i386-linux-gnu/GL/default/share/libdrm/amdgpu.ids: No such file or directory` spamming the terminal.
- **Root Cause**: Flatpak container environments with hybrid architectures (e.g., AMD iGPU + Nvidia dGPU) trigger Mesa checks that look for hardware IDs through the 32-bit `i386` subsystem, which don't map neatly.
- **Fix / Workaround**: Ignore entirely. It does not crash the installer or affect final performance.

## CLI Tooling Reference
- **Lutris (Flatpak)**: 
  - List versions: `flatpak run net.lutris.Lutris --list-wine-versions`
  - Install runner: `flatpak run net.lutris.Lutris --install-runner wine`
  - Run installer: `flatpak run net.lutris.Lutris -d lutris:install/<slug>` (This opens the GUI for the user to complete).