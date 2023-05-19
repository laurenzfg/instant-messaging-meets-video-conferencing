#!/bin/bash

# Call e.g. ./setlatency.sh 2ms 10ms GUID
# Writes the timestamp to specfile belonging to GUID $3

# Set up artifical delays on the ingress route
for i in ifb0 ifb1
do
    # Add a $1 milli-second delay to traffic sent P2P
    # Add a $2 milli-second delay to traffic sent to the internet
    # This is achieved because all traffic is sent to band 1 / handle 1:2 and local traffic is singled out to hi-pri band 0 / handle 1:1
    sudo tc qdisc replace dev $i parent 1:1 netem delay $1 limit 10000000
    sudo tc qdisc replace dev $i parent 1:2 netem delay $2 limit 10000000
done

specfile_name="$3.txt"
echo "$(date +%s%N);delay_changed;$1-$2" >> $specfile_name 