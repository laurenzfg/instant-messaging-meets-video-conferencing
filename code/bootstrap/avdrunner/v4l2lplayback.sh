#!/bin/bash

if [ "$HOSTNAME" = avda ]; then
    taskset --cpu-list 0-3,6-9 ffmpeg -nostdin -f rawvideo -s 1280x720 -r 60 -pix_fmt yuv420p -re -stream_loop -1 -i $1 -threads 1 -f v4l2 /dev/video0
else
    ffmpeg -nostdin -f rawvideo -s 1280x720 -r 60 -pix_fmt yuv420p -re -stream_loop -1 -i $1 -threads 1 -f v4l2 /dev/video0
fi

