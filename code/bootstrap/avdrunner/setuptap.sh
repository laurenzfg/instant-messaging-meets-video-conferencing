#!/bin/sh

# This script creates a new tap device tap0 and attaches it
# to a bridge br0
# Give your username e.g. via $(whoami) as argument 1

# auto-run on startup with systemd by tap.service

ip tuntap add dev tap0 mode tap user $1

ip link set tap0 master br0
ip link set br0 up
ip link set tap0 up

ethtool -K eno1 gso off gro off tso off tx off rx off lro off
ethtool -A eno1 autoneg off rx off tx off

tc qdisc replace dev tap0 root bfifo
tc qdisc replace dev eno1 root bfifo
