#!/bin/bash

# This captures all the traffic Android <--> Android
# and Android <--> Cloud.
# The capture happens before the NAT is performed,
# so you'll see packets from a private IP to cloud IPs

# For further analysis, download the .dump to your local machine
# and open it with wireshark

sudo tcpdump -i br0 -s 0 -w out.dump
