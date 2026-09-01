#!/bin/bash
set -e
cd "$(dirname "$0")"
F=out/masha_salon_empleo_montreal_1080x1920.mp4
rm -rf postqa; mkdir -p postqa
# exact frames with -vsync 0 (select by frame number, no -ss seeking)
ffmpeg -v error -y -i $F -vf "select='not(mod(n\,30))',scale=216:-1" -vsync 0 postqa/s_%04d.png
ls postqa | wc -l
ffmpeg -v error -y -pattern_type glob -i 'postqa/s_*.png' -vf "tile=10x8:padding=3:color=white" -frames:v 1 postqa_sheet.png
ffmpeg -v info -i $F -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I:|LRA:|Peak:)" | tail -3
