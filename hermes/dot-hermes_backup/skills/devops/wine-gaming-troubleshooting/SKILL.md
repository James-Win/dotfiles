---
name: wine-gaming-troubleshooting
category: devops
description: "Troubleshooting Windows games and launcher clients (Lutris, Wine, Proton) on Linux, specifically Battle.net, multi-GPU issues, and CEF sandbox crashes."
---

# Wine & Lutris Gaming Troubleshooting

This skill covers diagnosing and fixing common crashes when running Windows game launchers (like Battle.net) on Linux via Wine, Proton, or Lutris.

## Golden Rule for Launchers: Native over Flatpak
If a launcher fails persistently inside the **Flatpak** version of Lutris (especially with Chromium Embedded Framework (CEF) sandbox access errors, missing dependencies like `PROONPATH`, or hardware mapping faults), **switch to the native host package** (`dnf install lutris`, `apt install lutris`). Native versions bypass Flatpak portal/sandbox restrictions that interfere with CEF and multi-GPU Vulkan ICDs.

## 1. Battle.net: "Update Agent Went to Sleep" Infinite Loop
**Symptoms:** The Blizzard Update Agent hangs indefinitely or fails to start, displaying the "Attempting to wake it up" dialog.
**Fixes:**
1. **Clear Corrupt Lockfiles:** Kill ghost processes (`killall -9 Agent.exe Battle.net.exe wine wineserver`). Delete `drive_c/ProgramData/Battle.net/Agent/Agent.9700` (or similar numbered cache folder) and `Agent.dat`. Let it rebuild from scratch.
2. **Force Windows 10 Mode:** The Agent parses obsolete Windows API version reports and hangs. Force the registry for both executing binaries:
   ```bash
   WINEPREFIX="/path/to/prefix" wine reg add "HKCU\Software\Wine\AppDefaults\Agent.exe" /v "Version" /t REG_SZ /d "win10" /f
   WINEPREFIX="/path/to/prefix" wine reg add "HKCU\Software\Wine\AppDefaults\Battle.net.exe" /v "Version" /t REG_SZ /d "win10" /f
   ```
*(Note: Always point the Lutris executable to `Battle.net.exe`, not `Battle.net Launcher.exe` which is just a vulnerable wrapper script).*

## 2. Network Polling Crash (`complete_async_poll`)
**Symptoms:** Wine crashes with `wineserver: ../src-wine/server/sock.c:1153: complete_async_poll: Assertion 'output->count == signaled_count' failed.`
**Fix:** This is a known regression with aggressive downloaders under certain wine-server updates. Manually downgrade the runner to **`lutris-GE-Proton8-25-x86_64`** (or a known stable equivalent). This specific older version's polling implementation does not assert out under Battle.net's concurrent network threading.

## 3. Chromium/CEF Freezes and Black Screens
**Symptoms:** The launcher logs show `WSALookupServiceBegin failed` or `network_sandbox.cc Failed to grant sandbox access`. The UI is blank, completely black, or entirely unresponsive but audio/processes are running.
**Fix:** Pass these arguments to the executable (`Battle.net.exe`) via Lutris Game Options -> Arguments:
*   `--no-sandbox` (Prevents wine/flatpak path collision on cache generation which breaks the UI)
*   `--disable-gpu-compositing` (Fixes black layering without entirely disabling hardware rendering)
*   *Fallback:* If it still freezes, completely fallback to software rendering: `--disable-gpu --disable-hardware-video-decoding`

## 4. Multi-GPU Vulkan Initialization Crash
**Symptoms:** Systems with an iGPU (AMD) + dGPU (NVIDIA). Logs show `Internal Vulkan error (-7): A requested extension is not supported in RendererVk.cpp`.
**Fix:** Bnet `RendererVk.cpp` grabs the wrong GPU and fails. Force Wine to bind strictly to the dGPU's Vulkan ICD by setting Lutris Environment Variables:
*   `VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json` (or your specific hardware JSON)
*   `WINE_DO_NOT_CREATE_DXGI_DEVICE_MANAGER=1`