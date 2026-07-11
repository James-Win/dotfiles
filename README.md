# Dotfiles

Personal desktop configuration managed with **GNU Stow**.

## Supported Environment
* **OS**: Fedora
* **WM**: i3 Window Manager
* **Terminal**: Kitty
* **Shell**: Bash & Zsh
* **Status Bar**: Polybar
* **Compositor**: Picom
* **Notifications**: Dunst

---

## Installation & Setup

### 1. Install Required Applications
To install the necessary desktop applications and dependencies on a fresh Fedora installation, run:

```bash
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
```

*Note: For the clipboard daemon (`greenclip`), you may need to download the binary manually and place it in your path (e.g., `~/.local/bin/greenclip`).*

### 2. Clone the Repository
Clone this repository directly into your home directory:

```bash
git clone <your-repository-url> ~/dotfiles
cd ~/dotfiles
```

### 3. Deploy Symlinks using GNU Stow
Use `stow` to link the configurations to your home directory. The `--dotfiles` flag will automatically rename files starting with `dot-` (e.g., `dot-bashrc`) to their hidden equivalents (e.g., `.bashrc`) in your home directory:

```bash
stow --dotfiles -v -R -t ~ bash zsh git i3 kitty polybar picom dunst mangohud thunar hermes
```

---

## Repository Structure

Each subdirectory at the root level acts as a "stow package":
* **`bash/`**: Bash profile and environment configurations (`.bashrc`, `.profile`, `.xprofile`).
* **`zsh/`**: Zsh shell configurations (`.zshrc`).
* **`git/`**: Git global configurations (`.gitconfig`, `.gitignore`).
* **`i3/`**: Window manager config and helper scripts (`lock.sh`, `start-polybar.sh`, `workspace-warden.py`).
* **`kitty/`**: Kitty terminal emulator styling.
* **`polybar/`**: Polybar status bar configs and monitor scripts.
* **`picom/`**: Compositor settings for window opacity, blurring, and shadows.
* **`dunst/`**: Desktop notification settings.
* **`mangohud/`**: Hardware monitoring overlay.
* **`thunar/`**: Custom user actions for the Thunar file manager.
* **`hermes/`**: Agent configurations and skills (`.hermes_backup`).

---

## Managing Changes

To make changes to a configuration file:
1. Simply edit the file inside your target home directory (e.g., `~/.config/i3/config`). Because it is a symlink, changes will write directly to the files in `~/dotfiles/`.
2. Commit and push the changes from the `~/dotfiles` repository:
   ```bash
   cd ~/dotfiles
   git status
   git add .
   git commit -m "update configuration"
   git push
   ```
