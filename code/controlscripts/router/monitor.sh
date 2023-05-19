#!/bin/bash

# This script invokes monitorbpf.py and writes a Experiment File according to specs
# The first argument shall be a GUID describing the experiment, e.g. SignalVsTCP1312211200
# Second argument is the queue type to be monitored, e.g. CODEL or bfifo
# Sudo is needed to call!

GUID=$1
specfile_name="$GUID.txt"
capfile_name="$GUID.bpf"

# Write GUID and name of bpfcapture to specfile
touch $specfile_name
echo $GUID >> $specfile_name
echo "" >> $specfile_name

# Write name of picklefile to specfile
picklefile_name="$GUID.pickle"
echo "bpfcapture;$picklefile_name" >> $specfile_name
echo "" >> $specfile_name

chmod 666 $specfile_name

# Segue into monitorbpf.py
mydir=$(dirname "$0") # script is in the same dir as we are
exec $mydir/monitorbpf.py -t $2 > $capfile_name
