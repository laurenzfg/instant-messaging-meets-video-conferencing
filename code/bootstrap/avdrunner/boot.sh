#!/bin/bash

tmux new-session -d -s avd
tmux rename-window -t 0 'VideoRunner'
tmux send-keys -t 'VideoRunner' '~/mobile-vc-study-code/bootstrap/avdrunner/v4l2lplayback.sh ~/kristenandsara.yuv' C-m

tmux new-window -t avd:1 -n 'AudioRunner'
tmux send-keys -t 'AudioRunner' '~/mobile-vc-study-code/bootstrap/avdrunner/audioplayback.sh' C-m

sleep 10

tmux new-window -t avd:2 -n 'AVDRunner'
tmux send-keys -t 'AVDRunner' '~/mobile-vc-study-code/bootstrap/avdrunner/bootavd.sh' C-m

echo "Started Audio, Video and AVD in tmux session"

# Wait until ADB "sees" the device
adb wait-for-device
# Wait another 50 seconds because the AVD has a bug:
# It gets a DHCP lease from the DHCP server and correctly configures it
# But then, some baked in script dials in 10.0.2.15 as in the SLIRP NAT setups
# we wait until the boot is completely done and then bake in our static v4 config
sleep 50

# bake it in
~/mobile-vc-study-code/bootstrap/avdrunner/ifconfigavd.sh

tmux attach-session
