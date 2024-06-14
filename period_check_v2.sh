#!/bin/bash

file_path="output.yaml"
# Set size limit in bytes (more precise for large values)
size_limit=20

while true; do
  tile_size=$(du -h "$file_path")

  echo "$(date +'%d-%m-%Y %H:%M:%S'): File size: $tile_size"

  # Check if file size is greater than the limit
  if [[ $(du -h --block-size=1G "$file_path" | awk '{print $1}') -gt $size_limit ]]; then
    echo "File size exceeds limit. Resetting..."
    echo "reset" > "$file_path"
  fi

  sleep 10
done
