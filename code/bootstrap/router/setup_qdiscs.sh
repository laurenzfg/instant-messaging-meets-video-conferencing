#!/bin/bash

# Netbound interface should not xmit meaningful traffic and has a 100mbit uplink (we don't throttle that)
sudo tc qdisc replace dev enp4s0 root bfifo limit 60000

sudo ip link set dev ifb0 up
sudo ip link set dev ifb1 up

for i in enp1s0 enp0s25
do
    # Cap the port egress for the test net at 10mbit and put a 1xBDB FIFO queue on top
    sudo tc qdisc add dev $i root handle 1: tbf rate 10mbit burst 1540 limit 1540
    sudo tc qdisc add dev $i parent 1: bfifo limit 4500 # 625 Byte is the BDP (0.0005s RTT * 10MBit/s). Setting buf to 4500 to avoid being ridicolous
    # Turn on ingress qdisc so that we can control the ingress traffic
    sudo tc qdisc add dev $i ingress
done

# Redirect ingress traffic to a fake netif so that it becomes egress and we have the full suite of traffic control
sudo tc filter add dev enp1s0 parent ffff: protocol ip u32 match u32 0 0 action mirred egress redirect dev ifb0
sudo tc filter add dev enp0s25 parent ffff: protocol ip u32 match u32 0 0 action mirred egress redirect dev ifb1

# Set up artifical delays on the ingress route
for i in ifb0 ifb1
do
    # Add a 10 milli-second delay to traffic sent to the internet
    # Add a 2 milli-second delay to traffic sent P2P
    # This is achieved because all traffic is sent to band 1 / handle 1:2 and local traffic is singled out to hi-pri band 0 / handle 1:1
    sudo tc qdisc add dev $i root handle 1: prio priomap 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
    sudo tc filter add dev $i parent 1:0 prio 99 protocol ip u32 match ip dst 192.168.0.0/24 flowid 1:1
    sudo tc qdisc add dev $i parent 1:1 netem delay 5ms limit 10000000
    sudo tc qdisc add dev $i parent 1:2 netem delay 10ms limit 10000000
done

echo "qdisc setup completed"
