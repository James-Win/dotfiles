#!/usr/bin/env bash
# Launch polybar on all connected outputs.
# Falls back to "main" if no bar config is found.
set -euo pipefail

BAR_NAME="${POLYBAR_BAR:-main}"

# Kill any old bar instances
pkill -x polybar 2>/dev/null || true

# Wait for i3 to finish output detection
sleep 0.5

# Launch one bar per output
for m in $(polybar --list-monitors | cut -d':' -f1); do
  MONITOR="$m" polybar -q "$BAR_NAME" &
done

# If xrandr produced nothing, launch without MONITOR set
if ! pgrep -x polybar >/dev/null 2>&1; then
  polybar -q "$BAR_NAME" &
fi
