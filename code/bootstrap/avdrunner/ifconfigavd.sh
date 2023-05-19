#!/bin/bash

# This configures the "radio" of the AVD to use ip address specific
# and disables DHCP system-wide.
# Disable "wifi" on the guest (Android) side!

IP='192.168.0.200' # IP for AVD on avda goes here
MAC='00:00:00:12:34:56' # MAC for AVD on avda goes here

if [ "$(hostname)" == 'avdb' ]; then
    IP='192.168.0.201' # IP for AVD on avdb goes here
    MAC='00:00:00:98:76:54' # MAC for AVD on avda goes here
fi

adb shell << EOF
su
stop dhcpclient_rtr
stop dhcpclient_wifi
stop dhcpclient_def
sysctl -w net.ipv6.conf.default.disable_ipv6=1
sysctl -w net.ipv6.conf.all.disable_ipv6=1
ip link set dev eth0 down
ip link set dev eth0 address $MAC
ip link set dev eth0 up
ip addr flush eth0
ip route flush table 1015
ip addr add $IP/24 dev eth0
ip route add 192.168.0.0/24 dev eth0 table 1015
ip route add default via 192.168.0.1 dev eth0 table 1015
EOF
