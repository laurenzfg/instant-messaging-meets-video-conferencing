# This scripts generates a wireshark PCAP file from the BPF monitor output (monitorbpf.py).
# You also get the resulting PCAP into a Python list for further processing.
# Why do we convert our raw parse into PCAP just to parse it again?
# To decode all the binary source IP, dest IP, UDP port and so on and so forth
# without doing it ourselves.
# Author: Constantin Sander
# Improved by: Laurenz Grote

import struct
from pcap_parsing import PcapTshark

from qmon_serializer import get_qmon_items
from pcap_gen import PcapFileGen
from collections import deque
from heapq import heappop, heappush, heappushpop

# This parses the PCAP file and performs the counter based integrity check on the way
def pcapParseWithIntegrityCheck(deq, pcapf):
    tshark = PcapTshark(pcapf)
    
    packets = []

    # validate counter field
    s = struct.Struct("<L")
    for p in tshark.get_packets():
        d = deq.popleft()
        if p is None:
            continue
        b = bytearray([int(octet, 16) for octet in p['eth.dst'].split(":")])
        c,  = s.unpack(b[0:4])
        assert d['counter'] == c, ("PCAP integrity check failed", d['counter'], c)

        if d['handle'] == 0:
            continue

        # Add some data to the PCAP parsing result lost during the Raw -> PCAP -> Python path
        p['raw.ts'] = d['ts']
        p['raw.handle'] = d['handle']
        p['raw.limit'] = d['limit']
        p['raw.qlen'] = d['qlen']
        p['raw.qlen_qstats'] = d['qlen_qstats']
        p['raw.backlog'] = d['backlog']
        p['raw.drops'] = d['drops']
        p['raw.requeues'] = d['requeues']
        p['raw.overlimits'] = d['overlimits']
        p['raw.event_type'] = d['event_type']
        p['raw.misc'] = d['misc']
        p['raw.ifname'] = d['ifname']
        p['raw.counter'] = d['counter']
        p['raw.skb'] = d['skb']

        p['dropped'] = 1                    # assume the packet was dropped from the queue until we have positive evidence
        packets.append(p)

    return packets

# recordDelay cleanses the data: Every packet is in here as enqeued and dequeued.
# Keep track of the packets that were enqueued but not yet dequeued
def recordDelays(packets):

    skb_dict = {}

    for packet in packets:
        key = packet['raw.skb']

        if packet['raw.event_type'] == 1:
            #enqueuing
            if key in skb_dict:
                del skb_dict[key]
            if packet['raw.misc'] != 1:
                # if packet was dropped on enqueue, so we won't see it again.
                # So no need to record the delay.
                skb_dict[key] = {'bw-in': packet}
        else:
            #dequeuing
            if key in skb_dict:
                packet['dropped'] = 0
                # Mark the eqneue packet as not dropped, too
                skb_dict[key]['bw-in']['dropped'] = 0
                ints  = skb_dict[key]['bw-in']['raw.ts']
                outts  = packet['raw.ts']

                delay = outts - ints

                if delay > 4.0 or delay < 0:
                    assert False, ("too high queuing delay", packet, delay)

                packet['queue_delay'] = delay
                
                assert skb_dict[key]['bw-in']['l3.dst'] == packet['l3.dst'], (skb_dict[key]['bw-in']['l3.dst'], "==", packet['l3.dst'])
                assert skb_dict[key]['bw-in']['l3.src'] == packet['l3.src'], (skb_dict[key]['bw-in']['l3.src'], "==", packet['l3.src'])
                assert skb_dict[key]['bw-in']['raw.handle'] == packet['raw.handle'], (skb_dict[key]['bw-in']['raw.handle'], "==", packet['raw.handle'], skb_dict[key])

                del skb_dict[key]

# converts the raw capture into PCAP file
def convert(inf, outf):
    snaplen = 100

    pcap = PcapFileGen(snaplen, outf)

    deq = deque()

    # we need to push raw capture through a heap sorter to achieve in-order line up
    # (host has parallelized packet processing)
    def heapsorter(inp, length, key, key2):
        h = []
        counter = 0
        for item in inp:
            if len(h) < length:
                heappush(h, (key(item), key2(item), counter, item))
            else:
                yield heappushpop(h, (key(item), key2(item), counter, item))[3]
            counter += 1
        while len(h) > 0:
            yield heappop(h)[3]

    # To convert the raw capture into a PCAP compatible format, we
    # - sort the raw capture with a sliding window of 10k packets (the data is mostly sorted already,
    #   just needs a slight re-sort bcause of parallelism)
    # - actually convert the data by means of pcap.addPacket
    counter = 0
    ts = 0
    s = struct.Struct("<LLL")
    try:
        for item in heapsorter(get_qmon_items(inf), 10000, lambda x: x['ts'], lambda x: 1-x['event_type']):
            item['counter'] = counter
            assert item['ts'] >= ts, (item['ts'], ts) # verify that time is montonically increasing after the sort
            ts = item['ts']
            deq.append(item) # save the correct counter + ts for integrity check
            x = s.pack(counter, 0, 0) # encode counter value formatted as raw capture MAC
            # for later integrity checks of our pipeline,
            # we write the counter into the source  + dest MAC address field
            # ofc we then lose the information of the 'real' sender MAC
            pcap.addPacket(x + item['skbdata'][12:], item['ts'], item['skblen']) # do the conversion
            counter += 1
            if counter >= 2 ** 32: # counter flow over
                counter = 0
    except:
        pass

    # Do some integrity check and parse what we just converted into Python
    outf.seek(0)
    packets = pcapParseWithIntegrityCheck(deq, outf)

    # recordDelays
    recordDelays(packets)

    return packets
