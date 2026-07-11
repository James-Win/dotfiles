#!/usr/bin/env bash

LOCK_IMAGE="${XDG_RUNTIME_DIR:-/tmp}/i3-lock-screen.png"

# Ensure temporary image is removed on exit
trap 'rm -f "$LOCK_IMAGE"' EXIT

# Restrict file permissions
umask 0077

maim "$LOCK_IMAGE"
magick "$LOCK_IMAGE" -blur 0x8 -fill '#170d02AA' -colorize 25 "$LOCK_IMAGE"

i3lock \
  --nofork \
  --image="$LOCK_IMAGE" \
  --tiling \
  --color=170d02
