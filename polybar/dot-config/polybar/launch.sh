#!/usr/bin/env bash

killall -q polybar

while pgrep -u "$UID" -x polybar >/dev/null; do
  sleep 0.2
done

polybar main -c "$HOME/.config/polybar/config.ini" &
