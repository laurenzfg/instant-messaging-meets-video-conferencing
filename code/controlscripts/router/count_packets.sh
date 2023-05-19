#!/bin/bash

sudo timeout $1 tcpdump -i $2 -nn -q "$3" 2>/dev/null | awk '{print $3"-"$5}' | perl -n -e'/(\d+.\d+.\d+.\d+).\d+-(\d+.\d+.\d+.\d+).\d+/ && print $1."-".$2."\n"' | sort | grep . | uniq -c
