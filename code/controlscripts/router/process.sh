#!/bin/bash

# This script takes GUID of the experiment
# and starts pre-processing the raw capture data with tshark

specfile_name="$1.txt"
capfile_name="$1.bpf"
pcapfile_name="$1.pcap"
picklefile_name="$1.pickle"

exec ~/mobile-vc-study-code/controlscripts/router/preprocessing/convert_raw.py $capfile_name $pcapfile_name $picklefile_name