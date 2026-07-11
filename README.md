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

### 2. Run the Bootstrap Script (Recommended)
You can automatically install all dependencies, enable the Starship prompt repository, deploy symlinks, and configure Git hooks using the provided bootstrap script:

```bash
git clone https://github.com/James-Win/dotfiles.git ~/dotfiles
cd ~/dotfiles
./setup.sh
```

---

### Manual Deployment Alternative

If you prefer to deploy files manually:

#### 1. Enable the Starship Prompt Repository
```bash
sudo dnf copr enable -y atim/starship
sudo dnf install -y starship
```

#### 2. Deploy Symlinks using GNU Stow
Use `stow` to link the configurations to your home directory. The `--dotfiles` flag will automatically rename files starting with `dot-` (e.g., `dot-bashrc`) to their hidden equivalents (e.g., `.bashrc`):

```bash
stow --dotfiles -v -R -t ~ bash zsh git i3 kitty polybar picom dunst mangohud thunar hermes rofi gtk xsettingsd starship
```

#### 3. Setup Pre-commit Hook
Copy the key scanner hook to your repository configuration:
```bash
mkdir -p .git/hooks
cp git-hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
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
* **`rofi/`**: Application search launcher config and theme.
* **`gtk/`**: GTK theme settings for GTK 2, 3, and 4 (`.gtkrc-2.0`, `settings.ini`).
* **`xsettingsd/`**: Desktop server configurations (`xsettingsd.conf`).
* **`starship/`**: Starship prompt layout settings (`starship.toml`).
* **`git-hooks/`**: Source scripts for Git hooks (like the credential scanning `pre-commit` hook).

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

*Note: The built-in pre-commit hook scans staged changes for potential credentials or private keys. If a commit is blocked due to a false positive, you can bypass the hook using:*
```bash
git commit --no-verify
```
