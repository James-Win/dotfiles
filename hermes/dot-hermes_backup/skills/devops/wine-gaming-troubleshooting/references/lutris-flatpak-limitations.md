# Lutris Flatpak vs. Native (Battle.net)

When troubleshooting a game launcher (like Battle.net or EA App) inside the **Flatpak** version of Lutris, the container sandbox frequently causes cascading failures that look like deep Wine/Proton bugs but are actually Flatpak permission/dependency missing issues.

## Common Flatpak-Induced Failures:
1.  **Missing `PROTONPATH` for `umu-run`:** The automated Flatpak `umu` game installer scripts look for Proton installs inside `~/.local/share/Steam/compatibilitytools.d/`. Flatpak sandboxing often isolates these paths or ships them empty, causing installer scripts (`Battle.net-Setup.exe`) to crash out immediately *before* downloading the actual executable.
2.  **`amdgpu.ids: No such file or directory`:** Harmless warning related to Flatpak's Mesa layer searching internally for GPU text IDs.
3.  **Vulkan ICD binding failures:** Multi-GPU systems (iGPU + dGPU) often fail to route properly inside the Flatpak GL extensions. Flatpak will report `failed to create dri2 screen` and `pci id driver (null)` because it isolates native host display drivers.

## Ultimate Recommendation
If heavy UI / CEF configuration tweaking (`--disable-gpu`, `--no-sandbox`) and Runner injection (`GE-Proton8-25`) fails to get the launcher to display properly inside the Flatpak container, **switch to native Lutris**.

Native packages (`sudo dnf install lutris`) bypass the sandbox portal entirely, giving the launcher direct, raw access to external Vulkan extensions, `corefonts`, and un-sandboxed caching directories.