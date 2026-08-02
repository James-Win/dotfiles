# Dotfiles

Personal desktop configuration managed with **GNU Stow**.

## Supported Environment
* **OS**: Fedora
* **Compositor**: SwayFX (Wayland) — see the note below
* **Terminal**: Kitty
* **Shell**: Bash & Zsh
* **Status Bar**: Waybar
* **Launcher**: Fuzzel
* **Notifications**: SwayNotificationCenter
* **Volume/Brightness OSD**: wob

### SwayFX is required, not optional

The sway config uses `blur`, `shadows`, and `corner_radius`. These commands do
not exist in vanilla sway, which **aborts the entire config load** when it hits
them — you get a bare screen with a config-error nag. `setup.sh` installs
SwayFX in place of sway automatically.

Two things make that more than a plain `dnf install`, and both are handled by
the script:

* `swayfx` and `sway` both provide `sway`, so they conflict and the existing
  sway package must be erased (`--allowerasing`).
* Fedora marks sway as a protected package (`/etc/dnf/protected.d/`), so dnf
  refuses to remove it until `protected_packages` is cleared for that one
  transaction.

SwayFX ships its own `/usr/bin/sway`, so `grimshot`, `sway-systemd`,
`sddm-wayland-sway` and the existing `sway.desktop` session entry keep working
unchanged — log in by picking **Sway** at the display manager as usual.

To run these dotfiles on plain sway instead, comment out the SwayFX block at
the bottom of `sway/dot-config/sway/config`.

---

## Installation & Setup

### Bootstrap Script (Recommended)

Installs all dependencies, swaps in SwayFX, enables the Starship COPR, deploys
the symlinks, and configures the git hooks:

```bash
git clone https://github.com/James-Win/dotfiles.git ~/dotfiles
cd ~/dotfiles
./setup.sh
```

After it finishes, log out and back in so the SwayFX session is picked up.

---

### Manual Deployment Alternative

#### 1. Install the packages

```bash
sudo dnf install -y \
  stow \
  swaybg \
  swayidle \
  swaylock \
  waybar \
  SwayNotificationCenter \
  fuzzel \
  grim \
  slurp \
  swappy \
  wl-clipboard \
  cliphist \
  wob \
  wlogout \
  brightnessctl \
  pavucontrol \
  network-manager-applet \
  dex-autostart \
  ImageMagick \
  kitty \
  Thunar \
  mangohud \
  zsh \
  zsh-autosuggestions \
  zsh-syntax-highlighting \
  fzf
```

#### 2. Install SwayFX

```bash
sudo dnf copr enable -y swayfx/swayfx
sudo dnf install -y --allowerasing --setopt=protected_packages= swayfx
```

#### 3. Install the Starship prompt

```bash
sudo dnf copr enable -y atim/starship
sudo dnf install -y starship
```

#### 4. Deploy symlinks using GNU Stow

The `--dotfiles` flag renames files starting with `dot-` (e.g. `dot-bashrc`) to
their hidden equivalents (e.g. `.bashrc`):

```bash
stow --dotfiles -v -R -t ~ bash zsh git sway waybar wob scripts kitty mangohud thunar hermes gtk starship xfce4-terminal
```

*Note: every name in that list must be a real directory in this repo — stow
aborts on an unknown package. Keep it in sync with `setup.sh`'s `PACKAGES`
array and `ls -d */`.*

#### 5. Set up the pre-commit hook

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
* **`sway/`**: SwayFX compositor config — keybindings, window rules, and visual effects.
* **`waybar/`**: Waybar status bar config and styling.
* **`wob/`**: Overlay bar theme for the volume and brightness OSD (`wob.ini`).
* **`scripts/`**: Helper scripts linked into `~/.local/bin` (`volume-osd`, `brightness-osd`).
* **`kitty/`**: Kitty terminal emulator styling.
* **`xfce4-terminal/`**: XFCE terminal settings.
* **`mangohud/`**: Hardware monitoring overlay.
* **`thunar/`**: Custom user actions for the Thunar file manager.
* **`hermes/`**: Agent configurations and skills (`.hermes_backup`).
* **`gtk/`**: GTK theme settings for GTK 2, 3, and 4 (`.gtkrc-2.0`, `settings.ini`).
* **`starship/`**: Starship prompt layout settings (`starship.toml`).
* **`git-hooks/`**: Source scripts for Git hooks (like the credential scanning `pre-commit` hook). Not a stow package.

---

## Managing Changes

To make changes to a configuration file:
1. Simply edit the file inside your target home directory (e.g., `~/.config/sway/config`). Because it is a symlink, changes will write directly to the files in `~/dotfiles/`.
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

*Pushing requires GitHub credentials. `.gitconfig` uses the `gh` CLI as its
credential helper, so run `gh auth login` once on a new machine.*
