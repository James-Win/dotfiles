#!/usr/bin/env bash

# setup.sh - Bootstrap script for Fedora i3wm dotfiles
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}        Fedora i3wm Dotfiles Bootstrapper           ${NC}"
echo -e "${BLUE}====================================================${NC}"

# 1. OS Validation
if [ ! -f /etc/fedora-release ]; then
    echo -e "${RED}ERROR: This script is intended to be run on Fedora only.${NC}"
    exit 1
fi

echo -e "OS verified: Fedora Linux."

# 2. Check for Sudo Access
if ! sudo -v &>/dev/null; then
    echo -e "${RED}ERROR: Sudo access is required to install dependencies.${NC}"
    exit 1
fi

# Keep-alive sudo until the script has finished
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &

# 3. Install System Packages
echo -e "\n${BLUE}--- Phase 1: Installing System Dependencies via DNF ---${NC}"
sudo dnf install -y \
  stow \
  i3 \
  i3lock \
  maim \
  ImageMagick \
  xss-lock \
  polybar \
  picom \
  dunst \
  kitty \
  thunar \
  mangohud \
  zsh \
  zsh-autosuggestions \
  zsh-syntax-highlighting \
  fzf

# 4. Enable Starship COPR and Install
echo -e "\n${BLUE}--- Phase 2: Installing Starship Cross-Shell Prompt ---${NC}"
if ! rpm -q starship &>/dev/null; then
    echo "Enabling atim/starship COPR repository..."
    sudo dnf copr enable -y atim/starship
    sudo dnf install -y starship
else
    echo "Starship is already installed."
fi

# 5. Apply Symlinks using GNU Stow
echo -e "\n${BLUE}--- Phase 3: Applying Symlinks using GNU Stow ---${NC}"
DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Declare the packages to stow
PACKAGES=(
    "bash"
    "zsh"
    "git"
    "i3"
    "kitty"
    "polybar"
    "picom"
    "dunst"
    "mangohud"
    "thunar"
    "hermes"
    "rofi"
    "gtk"
    "xsettingsd"
    "starship"
)

# Move to the dotfiles directory
cd "$DOTFILES_DIR"

# Check for existing conflicting regular files in target dir (home)
# and rename them to backups if found
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$HOME/.dotfiles_migration_backup/setup-backup-$TIMESTAMP"

check_and_backup() {
    local file="$1"
    if [ -e "$file" ] && [ ! -L "$file" ]; then
        echo -e "Found conflicting file: $file. Moving to backup..."
        mkdir -p "$BACKUP_DIR"
        mv "$file" "$BACKUP_DIR/"
    fi
}

# Run backup checks for target paths
check_and_backup "$HOME/.bashrc"
check_and_backup "$HOME/.profile"
check_and_backup "$HOME/.xprofile"
check_and_backup "$HOME/.bash_profile"
check_and_backup "$HOME/.zshrc"
check_and_backup "$HOME/.gitconfig"
check_and_backup "$HOME/.gitignore"
check_and_backup "$HOME/.gtkrc-2.0"
check_and_backup "$HOME/.config/i3"
check_and_backup "$HOME/.config/kitty"
check_and_backup "$HOME/.config/polybar"
check_and_backup "$HOME/.config/picom"
check_and_backup "$HOME/.config/dunst"
check_and_backup "$HOME/.config/rofi"
check_and_backup "$HOME/.config/xsettingsd/xsettingsd.conf"
check_and_backup "$HOME/.config/gtk-3.0/settings.ini"
check_and_backup "$HOME/.config/gtk-4.0/settings.ini"

echo "Stowing packages..."
stow --dotfiles -v -R -t ~ "${PACKAGES[@]}"

echo -e "\n${GREEN}Setup completed successfully!${NC}"
echo -e "Symlinks deployed to home directory. Please restart your shell."
