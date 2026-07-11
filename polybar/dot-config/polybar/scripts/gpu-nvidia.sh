#!/usr/bin/env bash

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "GPU: nvidia-smi missing"
  exit 0
fi

stats="$(nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu \
  --format=csv,noheader,nounits 2>/dev/null | head -n 1)"

if [ -z "$stats" ]; then
  echo "GPU: off"
  exit 0
fi

IFS=',' read -r util mem_used mem_total temp <<< "$stats"

util="$(echo "$util" | xargs)"
mem_used="$(echo "$mem_used" | xargs)"
mem_total="$(echo "$mem_total" | xargs)"
temp="$(echo "$temp" | xargs)"

echo "GPU ${util}% ${temp}°C ${mem_used}/${mem_total}MiB"
