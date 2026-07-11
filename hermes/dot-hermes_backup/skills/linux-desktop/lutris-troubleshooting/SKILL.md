---
name: lutris-troubleshooting
description: Troubleshooting Lutris, Flatpak sandboxing, and Wine/Proton runners for Windows games (e.g., Battle.net) on Linux.
---

# Lutris & Wine Troubleshooting

## 1. Trigger Conditions
- Diagnosing game installer failures or prefix creation issues in Lutris (especially the Flatpak version `net.lutris.Lutris`).
- Wine or Proton runners (like `umu` or `wine-ge`) silently crashing.
- Web-based specific launchers (like Battle.net, Epic Games, EA App) freezing or crashing during setup or login due to CEF (Chromium Embedded Framework) or network bugs.

## 2. Common Pitfalls & Fixes

### UMU Runner Silent Crashes
- **Symptom:** Installer stops working immediately. Lutris logs show `Umu exited unexpectedly during prefix creation (return code: 0)` and subsequently fails to find game executables.
- **Cause:** The `umu` runner sandbox assumes a Steam Proton installation exists. In Flatpak or fresh OS setups, `~/.local/share/Steam/compatibilitytools.d` might be entirely missing or empty, leading to a silent `PROTONPATH` `FileNotFoundError`.
- **Fix:** Manually create `~/.local/share/Steam/compatibilitytools.d/` and extract a `GE-Proton` release directly into it before launching `umu`-backed installers.

### Wine Socket Polling Crashes (Aggressive Installers)
- **Symptom:** Wine server logs spam `complete_async_poll: Assertion 'output->count == signaled_count' failed` followed by `Bad file descriptor` wine client errors. The install progress halts.
- **Cause:** A known regressions in certain Wine-GE 8.x+ branches. Aggressive parallel download managers (like Battle.net's `Agent.exe`) open too many sockets and break the async polling mechanism in the newer wineserver.
- **Fix:** Roll back the specific game's runner to a known stable iteration (e.g., `lutris-GE-Proton8-25-x86_64`) that has the older, unaffected socket polling implementation.

### Web/CEF Launcher UI Freezes (Hardware Acceleration / Network Polls)
- **Symptom:** Battle.net or similar CEF-based launchers display a blue spinning wheel, launch to a black screen, or freeze entirely after setup. Logs may indicate `WSALookupServiceBegin failed with: 0`.
- **Cause:** The CEF UI triggers hardware-level network change detectors or DXVK pipeline paths that hang the Wine translation layer.
- **Fix:** Disable hardware acceleration for the launcher UI. Add `--disable-gpu-compositing --no-sandbox` (or `--disable-gpu --disable-hardware-video-decoding`) to the "Arguments" field in Lutris Game config. Disable `DisableHardwareAcceleration` in regedit if needed. 

### Dual GPU (AMD+Nvidia) Vulnerabilities / CEF Breakage
- **Symptom:** Flatpak or standard Wine throws `Internal Vulkan error (-7)` mapping to AMD devices or `eglInitialize SwANGLE failed`, rendering a black UI screen.
- **Fix:** Force explicit ICD overrides for Nvidia: add `VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json` and `WINE_DO_NOT_CREATE_DXGI_DEVICE_MANAGER=1` to the environment block.
- **Ultimate Fallback:** If all manual Lutris and Proton configurations result in CEF crashes/hangs, bypass them natively via Bottles (`com.usebottles.bottles`). Bottles custom `soda` and `caffe` runners bundle exact multi-GPU logic and sandbox fixes internally.

### Bypassing Flatpak Lutris GUI Portal Bugs
- **Symptom:** The user clicks the file picker `...` button for the "Executable" or "Working Directory" in Lutris to configure a manual game, but nothing happens due to broken Flatpak `xdg-desktop-portal` permissions.
- **Fix:** Bypass the UI entirely. Close Lutris and manually edit the YAML configurations directly inside the Flatpak container structure:
  `~/.var/app/net.lutris.Lutris/data/lutris/games/<game_slug>.yml`
  Modify `exe:`, `working_dir:`, and `args:` manually, then relaunch Lutris.