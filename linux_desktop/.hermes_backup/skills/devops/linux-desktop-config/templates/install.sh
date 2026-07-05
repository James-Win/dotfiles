#!/usr/bin/env bash
set -euo pipefail
# desktop-setup bootstrap
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOME_DIR="${HOME}"
link_or_copy() {
  local src="$1"
  local dst="$2"
  if [ -e "$dst" ] && [ ! -L "$dst" ]; then
    echo "Backing up existing $dst to ${dst}.bak"
    mv "$dst" "${dst}.bak"
  fi
  mkdir -p "$(dirname "$dst")"
  ln -sf "$src" "$dst"
  echo "Linked $src -> $dst"
}
# i3
link_or_copy "${SCRIPT_DIR}/../i3/config" "${HOME_DIR}/.config/i3/config"
# GTK
link_or_copy "${SCRIPT_DIR}/../gtk/gtk-2.0-settings" "${HOME_DIR}/.gtkrc-2.0"
link_or_copy "${SCRIPT_DIR}/../gtk/gtk-3-settings.ini" "${HOME_DIR}/.config/gtk-3.0/settings.ini"
link_or_copy "${SCRIPT_DIR}/../gtk/gtk-4-settings.ini" "${HOME_DIR}/.config/gtk-4.0/settings.ini"
# X root settings
link_or_copy "${SCRIPT_DIR}/../xsettingsd/xsettingsd.conf" "${HOME_DIR}/.config/xsettingsd/xsettingsd.conf"
# picom
link_or_copy "${SCRIPT_DIR}/../picom/picom.conf" "${HOME_DIR}/.config/picom.conf"
# rofi
mkdir -p "${HOME_DIR}/.config/rofi"
link_or_copy "${SCRIPT_DIR}/../rofi/config.rasi" "${HOME_DIR}/.config/rofi/config.rasi"
link_or_copy "${SCRIPT_DIR}/../rofi/theme.rasi" "${HOME_DIR}/.config/rofi/theme.rasi"
# dunst
mkdir -p "${HOME_DIR}/.config/dunst"
link_or_copy "${SCRIPT_DIR}/../dunst/dunstrc" "${HOME_DIR}/.config/dunst/dunstrc"
echo "Done. Reload i3 with Mod+Shift+C or restart session."
