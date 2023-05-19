from datetime import timedelta
import datetime
import os
import string
import numpy as np
import pandas as pd
import seaborn as sns
import pickle
from matplotlib import gridspec, lines
import matplotlib.pyplot as plt

from definitions import Specfile, TimelineElement

left = "enp0s25"
right = "enp1s0"

#                                                 enp4s0                        (The Internet)
#                                                   |                           (NAT)
# left/bridge/router         enp0s25 (bottleneck) <---> (bottleneck) enp1s0     (Test Net)

tcpb = "192.168.0.101"
tcpa = "192.168.0.100"
avdavda = "192.168.0.200"
avdavdb = "192.168.0.201"

def getToLeftTrafficClasses(time, packets, useEnqueue=False, offsetByOneMinute=False):
    left_NIC_enqueue, left_NIC_dequeue, _, _ = sort_capture_into_queues(packets)

    if useEnqueue:
        left_NIC_dequeue = left_NIC_enqueue

    # Filter to tcp traffic
    tcpToLeft = left_NIC_dequeue[(left_NIC_dequeue['l3.src'] == tcpb) & (left_NIC_dequeue['l3.dst'] == tcpa)]

    # Filter to call traffic
    callToLeft = left_NIC_dequeue[(left_NIC_dequeue['l3.src'] == avdavdb) & (left_NIC_dequeue['l3.dst'] == avdavda)]

    # for tcp only
    if len(callToLeft) < 11:
        return callToLeft, tcpToLeft, tcpToLeft.index[len(tcpToLeft.index)-1] - tcpToLeft.index[0]

    observationEnd = callToLeft.index[len(callToLeft.index)-11] # don't look at the last 10 packets
    observationStart = callToLeft.index[11]

    if time == "cong" and len(tcpToLeft) > 11:
        tcpStart = tcpToLeft.index[11]

        observationStart = max(observationStart, tcpStart) + pd.Timedelta("30 seconds")
        observationEnd = observationStart + pd.Timedelta("120 seconds")

    if (offsetByOneMinute):
        observationStart = observationStart + pd.Timedelta(minutes=1)

    # Filter data down to observation period
    tcpToLeft = tcpToLeft[(tcpToLeft.index > observationStart) & (tcpToLeft.index < observationEnd)]
    callToLeft = callToLeft[(callToLeft.index > observationStart) & (callToLeft.index < observationEnd)]

    observationDuration = observationEnd - observationStart
    observationDuration = observationDuration.to_pytimedelta()
    # Convert to s
    observationDuration = observationDuration / datetime.timedelta(seconds=1)

    return callToLeft, tcpToLeft, observationDuration


def parse_specfile(specfile_name: string) -> Specfile:
    # Read the specification of the experiment
    specfile_file = open(specfile_name, 'r')
    specfile_lines = specfile_file.readlines()
    specfile_file.close()

    guid = specfile_lines[0]
    guid = guid.rstrip(' \n') # Strip Whitespace + Newline Character
    assert specfile_lines[1] == "\n", "Line 1 has to be empty by specification"

    # Strips the newline character
    reachedTimeline = False
    frontmatter = dict()
    timeline = list()

    for line in specfile_lines[2:]:
        # Truncat the endline
        line = line.rstrip(' \n')
        if (reachedTimeline):
            timeline_fields = line.split(";")
            assert len(timeline_fields) == 3, "all timeline lines must have three fields"
            timestamp = pd.to_datetime(int(timeline_fields[0]), unit="ns")
            timeline.append(TimelineElement(timestamp, timeline_fields[1], timeline_fields[2]))
        else:
            # We parse the frontmatter

            # Empty Line? Skip forward to the timeline parsing
            if (line == ""):
                reachedTimeline = True
            else:
                frontmatter_fields = line.split(";")
                assert len(frontmatter_fields) == 2, "all front matter lines must have two fields"
                # If the frontmatter field is a path, prefix them with the the path (except if path is local)
                dirname = os.path.dirname(specfile_name)
                if (dirname != ""):
                    frontmatter_fields[1] = dirname + "/" + frontmatter_fields[1]
                frontmatter[frontmatter_fields[0]] = frontmatter_fields[1]

    return Specfile(guid, frontmatter, timeline)

# filter_traffic reduces the data_frame to the packets sent through a specific netif;
# Furthermore, it reduces the data only to the enqueue or dequeue events
def filter_traffic(data_frame, netif, enqueue=True):
    event_type = 0
    if enqueue:
        event_type = 1

    return data_frame[(data_frame['raw.event_type'] == event_type) & (data_frame['raw.ifname'] == netif)]

# This reduces the data_frame to the packets (not) sent P2P within the Test Net
def filter_local(data_frame, local=True):
    src_filter = data_frame['l3.src'].str.startswith('192.168')
    dest_filter = data_frame['l3.dst'].str.startswith('192.168')
    
    if local:
        return data_frame[src_filter & dest_filter]
    else:
        return data_frame.where[~(src_filter & dest_filter)]


# add_rate_field adds a rate in kBit/s averaged with a sliding window of plotRollingWindow[ms] to the data_frame
# beware! filter to enqueue / dequeue beforehand; otherwise you count every packet twice!
def get_rate_frame(data_frame, win, length_field='frame.len'):
    rate_frame = pd.Series(data_frame[length_field], index=data_frame.index)
    rate_frame = rate_frame.resample("%dms" % win).sum()
    # Take the average rate over win=plotRollingWindow[ms] in byte, convert to bit and divide it by the win (in seconds) to get the rate
    rate_frame = (rate_frame * 8 / (win / 1000)).fillna(0)
    return rate_frame

# create_data_frame pushes the recorded data into a Pandas data_frame
def create_data_frame(file) -> pd.DataFrame:
    inf = open(file, "rb")
    packets = pickle.load(inf)
    inf.close()

    data_frame = pd.DataFrame(packets)
    # index the data by timestamp
    data_frame = data_frame.rename(columns={'frame.time_epoch': 'time'})
    data_frame['time'] = data_frame['time'].map(lambda x: pd.Timestamp(x, unit="s"))
    data_frame = data_frame.set_index('time').sort_index()

    # data_frame.to_csv('out.csv') # (if you want to see what data we have available here)

    return data_frame

def sort_capture_into_queues(data_frame):
    # Sort packets into En-/De-queue and netif
    left_NIC_enqueue = filter_traffic(data_frame, left, enqueue=True)
    left_NIC_dequeue = filter_traffic(data_frame, left, enqueue=False)

    right_NIC_enqueue = filter_traffic(data_frame, right, enqueue=True)
    right_NIC_dequeue = filter_traffic(data_frame, right, enqueue=False)

    return (left_NIC_enqueue, left_NIC_dequeue, right_NIC_enqueue, right_NIC_dequeue)

def get_interpacket_time(packets, fromip, destip):
    packets = packets[(packets['l3.src'] == fromip) & (packets['l3.dst'] == destip)]

    if len(packets) == 0:
        return np.array([0.0])

    packets_ts = packets.index
    packet_ts_shifted = np.roll(packets_ts, 1)

    packets_ts = packets_ts[1:]
    packet_ts_shifted = packet_ts_shifted[1:]

    pia = packets_ts - packet_ts_shifted
    pia = pia.to_pytimedelta()
    pia_in_ms = pia / timedelta(milliseconds=1) # we now have packet interarrival times in ms

    return pia_in_ms

def make_cdf(subplot, data):
    sns.ecdfplot(data=data, ax=subplot)

def make_quad_cdf(leftEnqList, leftDeqList, rightEnqList, rightDeqList, bw):
    optimalInterPacketTiming = float(1500*8) / float(bw * 10**3) # in ms

    # Some padding for the whole plot
    plt.subplots_adjust(0.04,0.06,0.96,0.94, 0.175, 0.175)

    plots = gridspec.GridSpec(2, 2) # hspace ist dubios

    to_left_before_btln = plt.subplot(plots[0])
    to_left_after_btln = plt.subplot(plots[2], sharey=to_left_before_btln, sharex=to_left_before_btln)

    to_right_before_btln = plt.subplot(plots[1], sharey=to_left_before_btln, sharex=to_left_before_btln)
    to_right_after_btln = plt.subplot(plots[3], sharey=to_left_before_btln, sharex=to_left_before_btln)

    # Set Axis Limits
    to_left_before_btln.set_xlim([0,100])
    to_left_after_btln.set_xlim([0,100])
    to_right_before_btln.set_xlim([0,100])
    to_right_after_btln.set_xlim([0,100])

    to_left_before_btln.set_ylim([0,1.0])
    to_left_after_btln.set_ylim([0,1.0])
    to_right_before_btln.set_ylim([0,1.0])
    to_right_after_btln.set_ylim([0,1.0])

    to_left_before_btln.set_xticks(np.arange(0, 100, step=5))
    to_left_after_btln.set_xticks(np.arange(0, 100, step=5))
    to_right_before_btln.set_xticks(np.arange(0, 100, step=5))
    to_right_after_btln.set_xticks(np.arange(0, 100, step=5))

    # Set titles
    to_left_before_btln.set_title("CDF Plot of Inter Packet Arrival Time; traffic destined to left")
    to_left_after_btln.set_title("CDF Plot of Inter Packet Dequeue Time; traffic destined to left ")

    to_right_before_btln.set_title("CDF Plot of Inter Packet Dequeue Time; traffic destined to right")
    to_right_after_btln.set_title("CDF Plot of Inter Packet Dequeue Time; traffic destined to right")

    to_left_before_btln.set_xlabel("Inter Packet Time [ms]")
    to_left_after_btln.set_xlabel("Inter Packet Time [ms]")

    to_right_before_btln.set_xlabel("Inter Packet Time [ms]")
    to_right_after_btln.set_xlabel("Inter Packet Time [ms]")

    make_cdf(to_left_before_btln, leftEnqList)
    make_cdf(to_left_after_btln, leftDeqList)

    make_cdf(to_right_before_btln, rightEnqList)
    make_cdf(to_right_after_btln, rightDeqList)

    # Make lines for optimal inter packet spacing
    to_left_before_btln.axvline(x=optimalInterPacketTiming, ls='--')
    to_left_after_btln.axvline(x=optimalInterPacketTiming, ls='--')
    to_right_before_btln.axvline(x=optimalInterPacketTiming, ls='--')
    to_right_after_btln.axvline(x=optimalInterPacketTiming, ls='--')

def make_rate_dataframe(packets_list, rtt_list, time, win=200):
    if len(packets_list) != len(rtt_list):
        print("rtt and packet list must have the same length!")
        raise Exception()

    rates = np.empty((0,1))
    rtts = np.empty((0,1))
    flow = np.empty((0,1))

    for packets, rtt in list(zip(packets_list, rtt_list)):
        callToLeft, tcpToLeft, observationDuration = getToLeftTrafficClasses(time, packets)

        call_rates = get_rate_frame(callToLeft, win)
        rates = np.append(rates, call_rates.to_numpy())
        flow = np.append(flow, np.repeat("call", len(call_rates)))

        tcp_rates = get_rate_frame(tcpToLeft, win)
        rates = np.append(rates, tcp_rates.to_numpy())
        flow = np.append(flow, np.repeat("tcp", len(tcp_rates)))

        rtts = np.append(rtts, np.repeat(rtt, len(tcp_rates) + len(call_rates)))

    d = {'flow': flow, 'rate': rates, 'rtt': rtts}
    
    return pd.DataFrame(data=d)