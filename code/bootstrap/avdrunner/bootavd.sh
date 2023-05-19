#!/bin/bash

# This boots AVD avdx and attaches its radio net interfaces to tap0 
# It is your responsibility to ensure that such a tap device exists and has
# sufficent connectivity
# the x in avdx is being substituted with the first char of your hostname
# suppose your machine is called avda, then avda is fired up

# Clean all locks. This is actually dangerous. Take care to not start two emulators!
rm ~/.android/avd/*/hardware-qemu.ini.lock ~/.android/avd/*/multiinstance.lock

SUFFIX=$(hostname | cut -c1)

if [ "$HOSTNAME" = avda ]; then
    taskset --cpu-list 0-3,6-9 ~/Android/Sdk/emulator/emulator -avd avd$SUFFIX -no-snapshot -net-tap tap0 -camera-back none -camera-front webcam0 -allow-host-audio -dns-server 1.1.1.1
else
    ~/Android/Sdk/emulator/emulator -avd avd$SUFFIX -no-snapshot -net-tap tap0 -camera-back none -camera-front webcam0 -allow-host-audio -dns-server 1.1.1.1
fi
