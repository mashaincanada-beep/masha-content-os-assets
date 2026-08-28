#!/bin/sh
# Montaje final: "Oficina orbital AURORA-7"
FF=/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2
SRC="/root/.claude/uploads/9db96e73-cd21-5367-bded-6f72ac5fad13/1e1c4f7a-IMG_2214.mov"
# NOTA: unsharp/gblur no aceptan RGB planar y ffmpeg colaria una conversion a YUV;
# un blend=screen sobre planos de croma tine la imagen de magenta. De ahi los format=gbrp explicitos.
$FF -hide_banner -loglevel error \
 -i "$SRC" \
 -framerate 30 -i glow/g_%04d.png \
 -framerate 30 -i hud/h_%04d.png \
 -loop 1 -i scanlines.png \
 -i ambience.wav \
 -filter_complex "\
[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,\
setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv,\
unsharp=5:5:0.5:5:5:0.4,format=gbrp,\
eq=contrast=1.24:brightness=-0.055:saturation=0.52:gamma=0.95,\
colorbalance=rs=-0.11:gs=-0.03:bs=0.21:rm=-0.08:gm=-0.02:bm=0.13:rh=-0.05:gh=0.00:bh=0.09,\
curves=all='0/0.025 0.25/0.19 0.5/0.43 0.75/0.70 1/0.96',format=gbrp,setsar=1[base];\
[1:v]fps=30,scale=1080:1920,format=gbrp,setsar=1[gl];\
[base][gl]blend=all_mode=screen:all_opacity=0.80,format=gbrp[b1];\
[2:v]fps=30,scale=1080:1920,format=rgba,setsar=1[hd];\
[b1]format=rgba[b1r];[b1r][hd]overlay=0:0:format=gbrp:shortest=1,format=gbrp[b2];\
[b2]split[c1][c2];[c2]gblur=sigma=20,format=gbrp[blr];\
[c1]format=gbrp[c1f];[c1f][blr]blend=all_mode=screen:all_opacity=0.22,format=gbrp[b3];\
[b3]rgbashift=rh=2:bh=-2[b4];\
[b4]rgbashift=rh=16:bh=-14:rv=4:bv=-4:enable='between(t,0.96,1.06)+between(t,3.32,3.42)+between(t,6.04,6.12)'[b5];\
[b5]eq=brightness=0.07:saturation=0.35:enable='between(t,0.96,1.02)+between(t,3.32,3.37)+between(t,6.04,6.09)'[b6];\
[3:v]scale=1080:1920,format=rgba,setsar=1[sl];\
[b6]format=rgba[b6r];[b6r][sl]overlay=0:0:format=gbrp:shortest=1[b7];\
[b7]format=yuv420p,vignette=PI/4.2,noise=alls=5:allf=t+u,\
setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv[v]" \
 -map "[v]" -map 4:a \
 -c:v libx264 -crf 19 -preset slow -pix_fmt yuv420p \
 -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv \
 -movflags +faststart -c:a aac -b:a 192k -shortest -y out/oficina_espacial.mp4
