#!/usr/bin/env bash
# Usage: encode.sh <media dir>
# Converts each video-<scene>/*.webm to <scene>.mp4 and <scene>.gif (390px wide, 8 fps). The webm stays.
set -euo pipefail
dir=$1
F=$(command -v ffmpeg) || { echo "prd-demo: ffmpeg not found (brew install ffmpeg)" >&2; exit 1; }
cd "$dir"
shopt -s nullglob
for v in video-*/; do
  scene=${v#video-}; scene=${scene%/}
  webm=$(ls "$v"*.webm | head -1)
  "$F" -y -loglevel error -i "$webm" -c:v libx264 -pix_fmt yuv420p -movflags +faststart "$scene.mp4"
  "$F" -y -loglevel error -i "$webm" -vf "fps=8,scale=390:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer" "$scene.gif"
done
ls -la ./*.png ./*.mp4 ./*.gif 2>/dev/null
