#!/bin/bash

# start NAT
sudo iptables-restore < /etc/iptables/rules.v4

# Install module supporting our eBPF measuring stack
cd /home/laurenz/mobile-vc-study-code/bootstrap/router/time
make install
cd

# Disable optimisations for all interfaces
for i in enp1s0 enp4s0 enp0s25
do 
    sudo ethtool -K $i gso off gro off tso off tx off rx off lro off
    sudo ethtool -A $i autoneg off rx off tx off
done

# Functional blocks for ingress + egress qdisc policing
sudo modprobe ifb numifbs=2

/home/laurenz/mobile-vc-study-code/bootstrap/router/setup_qdiscs.sh
