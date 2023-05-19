#!/bin/sh

# This script disables optimizations and CoDeL on the test net interface

# auto-run on startup with systemd by tap.service

ethtool -K eno1 gso off gro off tso off tx off rx off lro off
ethtool -A eno1 autoneg off rx off tx off

tc qdisc replace dev eno1 root bfifo limit 4500

sudo sysctl net.ipv4.tcp_congestion_control=bbr
