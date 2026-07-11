# ============================================================
# Shell Functions
# Sourced automatically by .bashrc via the .bashrc.d loader
# ============================================================

# mkcd - Create a directory and cd into it
mkcd() {
    if [ -z "$1" ]; then
        echo "Usage: mkcd <directory>"
        return 1
    fi
    mkdir -p "$1" && cd "$1"
}

# extract - Automatically extract common archive formats
extract() {
    if [ -z "$1" ]; then
        echo "Usage: extract <file>"
        return 1
    fi

    if [ ! -f "$1" ]; then
        echo "extract: '$1' is not a valid file"
        return 1
    fi

    case "$1" in
        *.tar.bz2)  tar xjf "$1"    ;;
        *.tar.gz)   tar xzf "$1"    ;;
        *.tar.xz)   tar xJf "$1"    ;;
        *.tar.zst)  tar --zstd -xf "$1" ;;
        *.bz2)      bunzip2 "$1"    ;;
        *.rar)      unrar x "$1"    ;;
        *.gz)       gunzip "$1"     ;;
        *.tar)      tar xf "$1"     ;;
        *.tbz2)     tar xjf "$1"    ;;
        *.tgz)      tar xzf "$1"    ;;
        *.zip)      unzip "$1"      ;;
        *.Z)        uncompress "$1" ;;
        *.7z)       7z x "$1"       ;;
        *.xz)       unxz "$1"       ;;
        *.zst)      unzstd "$1"     ;;
        *)          echo "extract: '$1' - unknown archive format" ;;
    esac
}

# fkill - Use fzf to interactively select and kill a process
fkill() {
    local pid
    pid=$(ps -ef | sed 1d | fzf -m --header='Select process(es) to kill' | awk '{print $2}')
    if [ -n "$pid" ]; then
        echo "$pid" | xargs kill -${1:-9}
        echo "Killed PID(s): $pid"
    fi
}

# weather - Quick weather report
weather() {
    curl -s "wttr.in/${1:-}" | head -17
}

# port - Show what's listening on a given port
port() {
    if [ -z "$1" ]; then
        echo "Usage: port <port_number>"
        return 1
    fi
    ss -tlnp | grep ":$1 "
}
