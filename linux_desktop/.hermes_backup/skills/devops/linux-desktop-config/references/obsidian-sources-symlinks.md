# Config editing from Obsidian

Obsidian should be the editor of record for config changes.

## Sources/ layout

Place symlinks under `~/ObsidianVault/Sources/`, one subdirectory per subsystem:

```
Sources/
├── i3/config -> ~/.config/i3/config
├── picom/picom.conf -> ~/desktop-setup/picom/picom.conf
├── rofi/theme.rasi -> ~/desktop-setup/rofi/theme.rasi
├── dunst/dunstrc -> ~/desktop-setup/dunst/dunstrc
├── gtk/gtk-3-settings.ini -> ~/.config/gtk-3.0/settings.ini
├── gtk/gtk-4-settings.ini -> ~/.config/gtk-4.0/settings.ini
├── gtk/gtk-2.0-settings -> ~/.gtkrc-2.0
└── xsettingsd/xsettingsd.conf -> ~/.config/xsettingsd/xsettingsd.conf
```

## Routine

1. Edit inside Obsidian under `Sources/`.
2. Apply by reloading the target component:
   - i3: `Mod+Shift+C`
   - picom: `killall picom && picom --config ~/desktop-setup/picom/picom.conf`
   - dunst: `killall dunst && dunst`
   - rofi/GTK: next app open applies theme
3. After verification, sync repo copies if needed: cp back into `~/desktop-setup/...`

## Adding new links

```bash
ln -s /real/target ~/ObsidianVault/Sources/<subsystem>/<name>
```
