#!/usr/bin/env bash

GUID=$1
movie_name="$GUID.mkv"

env DISPLAY=:0 XAUTHORITY=/home/laurenz/.Xauthority wmctrl -r Android Emulator -e 0,100,100,720,1560

if [ "$HOSTNAME" = avda ]; then
    timeout 14 taskset --cpu-list 4,5,10,11 ffmpeg -nostdin -video_size 720x1560 -framerate 30 -f x11grab -i :0.0+100,100 -c:v libx264rgb -crf 0 -preset ultrafast -color_range 2 $movie_name
else
    printf "cannot capture on avdb"
fi

if [ $? -eq 124 ] 
then
    exit 0
fi
