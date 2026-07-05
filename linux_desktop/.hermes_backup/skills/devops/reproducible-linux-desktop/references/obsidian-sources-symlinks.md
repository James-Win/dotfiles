# Obsidian Sources/ symlink workflow

Let the user edit real config files inside Obsidian.

## Pattern

Create `~/ObsidianVault/Sources/` and symlink real config files into subsystem folders by `ln -s /real/target ~/ObsidianVault/Sources/<subsystem>/<name>`.

## Example layout

```
Sources/
├── i3/config -> ~/.config/i3/config
├── picnic/picom.conf -> ~/desktop-setup/picom/picom.conf
├── rofi/theme.rasi -> ~/desktop-setup/rofi/theme.rasi
├── dunst/dunstrc -> ~/desktop-setup/dunst/dunstrc
├── gtk/gtk-3-settings.ini -> ~/.config/gtk-3.0/settings.ini
├── gtk/gtk-4-settings.ini -> ~/.config/gtk-4.0/settings.ini
├── gtk/gtk-2.0-settings -> ~/.gtkrc-2.0
├── xsettingsd/xsettingsd.conf -> ~/.config/xsettingsd/xsettingsd.conf
└── obsidian-obsidian.json -> ~/.config/obsidian/obsidian.json
```

## Verification

Check target readability after linking: `[ -r "$f" ]` per new link.

## Apply cycle

After editing in Obsidian:
- i3: `Mod+Shift+C`
- picom: `killall picom && picom --config ~/desktop-setup/picom/picom.conf`
- **dunst:** `killall dunst && dunst -config ~/desktop-setup/dunst/dunstrc`
- rofi/GTK: next open/applies automatically

## Repo sync

Keep `~/desktop-setup/` copies in sync with live configs when needed for git.
