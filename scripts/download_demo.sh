#!/usr/bin/env bash
set -euo pipefail

target="${1:-demo/input_airport_luggage.mp4}"
source_url="https://videos.pexels.com/video-files/36017327/15272831_1920_1080_60fps.mp4"
mkdir -p "$(dirname "$target")"
temporary="${target}.download.mp4"
curl -L --fail --retry 3 -o "$temporary" "$source_url"
if command -v ffmpeg >/dev/null 2>&1; then
  ffmpeg -y -i "$temporary" -vf 'scale=960:-2,fps=30' -an -c:v libx264 -preset veryfast -crf 22 "$target"
  rm "$temporary"
else
  mv "$temporary" "$target"
fi
printf '%s\n' "Saved $target" "Source page: https://www.pexels.com/video/luggage-on-airport-baggage-carousel-36017327/" "License: https://www.pexels.com/license/"
