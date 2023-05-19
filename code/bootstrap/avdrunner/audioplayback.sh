#!/bin/bash

pactl load-module module-null-sink sink_name=vspeaker sink_properties=device.description=virtual_speaker
pactl load-module module-remap-source master=vspeaker.monitor source_name=vmic source_properties=device.description=virtual_mic
pactl set-default-source vmic

if [ "$HOSTNAME" = avda ]; then
    taskset --cpu-list 0-3,6-9 ffplay -nodisp -loop 0 -autoexit ~/preamble.wav -loglevel 16
else
    ffplay -nodisp -loop 0 -autoexit ~/preamble.wav -loglevel 16
fi