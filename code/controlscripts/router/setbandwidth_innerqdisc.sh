#!/bin/bash

# Sets the downlink speed for both test net ports to $1mbit and the inner qdisc to $2
# Writes the timestamp to specfile belonging to GUID $3

for i in enp1s0 enp0s25
do
    sudo tc qdisc replace dev $i root handle 1: tbf rate $(echo $1)mbit burst 1540 limit 1
    sudo tc qdisc replace dev $i parent 1: $2
done

specfile_name="$3.txt"
echo "$(date +%s%N);bandwidth_changed;$1" >> $specfile_name 
