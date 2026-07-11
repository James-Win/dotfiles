# ============================================================
# Shell Aliases
# Sourced automatically by .bashrc via the .bashrc.d loader
# ============================================================

# --- Navigation ---
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'

# --- Listing (use eza if available, otherwise ls) ---
if command -v eza &>/dev/null; then
    alias ls='eza --icons --group-directories-first'
    alias ll='eza -lh --icons --group-directories-first'
    alias la='eza -lah --icons --group-directories-first'
    alias lt='eza --tree --level=2 --icons'
else
    alias ls='ls --color=auto'
    alias ll='ls -lh --color=auto'
    alias la='ls -lAh --color=auto'
fi

# --- Safety nets ---
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'

# --- Grep ---
alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'

# --- Git shortcuts ---
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gd='git diff'
alias gl='git log --oneline -20'
alias gco='git checkout'
alias gb='git branch'

# --- Dotfiles ---
alias dots='cd ~/dotfiles'

# --- System ---
alias df='df -h'
alias du='du -h'
alias free='free -h'
alias psg='ps aux | grep -v grep | grep -i'

# --- Misc ---
alias c='clear'
alias h='history | tail -30'
alias reload='source ~/.bashrc'
