#!/usr/bin/env python3

# If you just want the PCAP for manual inspection and not use the data from another script,
# just invoke this script directly instead of using parse_raw
# NOTE: Every packet is in there twice: Once when it was dequeued and once when it was enqueued onto a queue.
#       If you observe two queues and we have P2P traffic, you might even see every packet four times.
# Author: Laurenz Grote

import sys
import pickle
from parse_raw import convert

args = sys.argv[1:]

if args[0] == "":
    print("Invoke: python3 wireshark_gen.py in.txt out.pcap out.pickle . Converts the queue monitoring result into a Wireshark PCAP as well as the format for our analysis stack.")
else:
    inf = open(args[0], "rb")
    outf = open(args[1], "w+b")
    pickle_outf = open(args[2], "w+b")
    result = convert(inf, outf)
    pickle.dump(result, pickle_outf, pickle.HIGHEST_PROTOCOL)
    pickle_outf.close()
    inf.close()
    outf.close()
