#!/usr/bin/env bash

LOCK_IMAGE="/tmp/i3-lock-screen.png"

maim "$LOCK_IMAGE"
magick "$LOCK_IMAGE" -blur 0x8 -fill '#170d02AA' -colorize 25 "$LOCK_IMAGE"

i3lock \
  --nofork \
  --image="$LOCK_IMAGE" \
  --tiling \
  --color=170d02
