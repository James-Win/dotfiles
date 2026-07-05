# Fedora Linux Desktop & Apps Troubleshooting Reference

## Lutris & Flatpak
- **Lutris umu-run Flatpak bug**: The Flatpak version of Lutris `0.5.22` currently has a silent sandbox failure where `umu-run` crashes (return code 0) without unzipping installers / prefixes (resulting in cascade file missing errors like `Battle.net Launcher.exe could not be found`). The log provides a clue: `FileNotFoundError: Environment variable not set or is empty: PROTONPATH`.
**Workaround Steps**:
1. Ensure the user's local Steam compat tools folder exists: `mkdir -p ~/.local/share/Steam/compatibilitytools.d`
2. Download and extract a GE-Proton release (e.g., `GE-Proton8-25`) into that directory.
3. Relaunch the Lutris installer. `umu-run` will detect the local Proton installation and successfully create the prefix, bypassing the Flatpak sandbox restriction that caused the initial crash.