#!/bin/bash
set -e
cd "$(dirname "$0")"
ffmpeg -v error -y -i build/base.mp4 -framerate 30 -i frames/o_%05d.png -i build/audio_mix.wav -filter_complex "[0:v][1:v]overlay=0:0:format=auto:shortest=1,format=yuv420p[v]" -map "[v]" -map 2:a -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -r 30 -c:a aac -b:a 192k -movflags +faststart -shortest out/masha_salon_empleo_montreal_1080x1920.mp4
ffprobe -v error -show_entries stream=codec_name,codec_type,width,height,r_frame_rate,nb_frames,duration,sample_rate,bit_rate:format=duration,size -of default=nw=1 out/masha_salon_empleo_montreal_1080x1920.mp4
