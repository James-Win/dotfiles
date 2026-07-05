# Running Battle.net & Lutris on Fedora (Dual GPU)

Battle.net on Linux is highly temperamental, especially on dual-GPU Fedora systems (AMD iGPU + Nvidia discrete). Here are proven fixes for the recurring failure modes:

## 1. Flatpak vs Native Lutris
Flatpak Lutris often fails to properly enumerate Vulkan drivers on dual-GPU setups, resulting in `Vulkan error (-7)` or `failed to create dri2 screen` when the Chromium UI tries to draw.
- **Fix:** Avoid the Flatpak. Install Lutris natively (`sudo dnf install lutris`) to give it unobstructed access to the system Mesa and Nvidia drivers.
- **Workaround:** If Flatpak is strictly required, manually force the ICD path: `env VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json` and set `WINE_DO_NOT_CREATE_DXGI_DEVICE_MANAGER=1`.

## 2. "Update Agent went to sleep" (Infinite Loop)
`Agent.exe` relies on aggressive network polling to wake up. On Wine, this sometimes crashes if the OS environment is reported improperly.
- **Fix 1:** Force Wine to report Windows 10 for the components via registry:
  ```bash
  wine reg add "HKCU\Software\Wine\AppDefaults\Agent.exe" /v "Version" /t REG_SZ /d "win10" /f
  wine reg add "HKCU\Software\Wine\AppDefaults\Battle.net.exe" /v "Version" /t REG_SZ /d "win10" /f
  ```
- **Fix 2:** Ensure Lutris synchronization is set to `Fsync` instead of `Esync`, which handles the polling threads better.
- **Fix 3:** Delete the corrupted agent cache at `drive_c/ProgramData/Battle.net/Agent/` and let it rebuild.

## 3. UI Freezes or Black Screens
The Chromium Embedded Framework (CEF) in the launcher often crashes its own renderer or sandbox.
- **Fix:** Launch `Battle.net.exe` with the arguments: `--disable-gpu-compositing --no-sandbox`.
- **Registry fallback:** In `HKCU\Software\Blizzard Entertainment\Battle.net\System`, set `DisableHardwareAcceleration` to `1`. This bypasses Vulkan entirely for the launcher UI.

## 4. "write: Bad file descriptor" (sock.c:1153 Assertion)
A known regression in newer GE-Proton 8 builds (e.g. 8-26) causes Wine server socket polling assertions during aggressive Battle.net update downloads.
- **Fix:** Pin the runner to `lutris-GE-Proton8-25-x86_64`, which retains the older, stable polling implementation for Battle.net.