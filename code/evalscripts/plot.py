#!/usr/bin/env python3

# This scripts generates a plot from a PCAP file
# Author: Constantin Sander
# Improved by: Laurenz Grote

import matplotlib as mpl
from matplotlib import gridspec, lines
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from utils import get_interpacket_time, get_rate_frame, getToLeftTrafficClasses, make_cdf, make_quad_cdf, make_rate_dataframe, sort_capture_into_queues, tcpb, tcpa, avdavda, avdavdb
mpl.use('Agg')
sns.set()

from pandas.plotting import register_matplotlib_converters

from definitions import Specfile

register_matplotlib_converters()


# This plots the various streams and globally stores the legend
color_pos = 0
colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:olive', 'tab:cyan']

color_map = {}
legend_list = []
stream_mapping = {}

def getmaxbw(timeline):
    maxbw = 0.0
    for event in timeline:
        if event.event == "bandwidth_changed":
            maxbw = max(maxbw, float(event.payload))
    return maxbw

def getp2prtt(timeline):
    for event in timeline:
        if event.event == "delay_changed":
            new_delays = event.payload.split('-')
            return "%sms" % (float(new_delays[0].replace('ms','')) * 2.0)
    return "-1ms"

def plot_streams(subplot, packets, plotRollingWindow, specfile: Specfile):
    for event in specfile.timeline:
        if event.event == "bandwidth_changed":
            subplot.scatter(event.timestamp, float(event.payload), zorder=1)
            
    subplot.set_ylim([0, getmaxbw(specfile.timeline)+0.5])

    global color_pos

    choosecolor = lambda i : colors[i % len(colors)]

    # Plot the data rates in Mbit/s

    for (stream, src, dst, srcport, dstport), group in packets.groupby(
            ['l4.stream', 'l3.src', 'l3.dst', 'l4.srcport', 'l4.dstport']):

        # Drop flows with < 20kBit xmitted
        if group['frame.len'].sum() < 20 * 10 ** 3:
            continue

        stream = stream.replace("tcp", "t").replace("udp", "u")

        key = (stream[0], src, srcport, dst, dstport)

        if key in stream_mapping:
            assert (stream_mapping[key] == stream)
        else:
            stream_mapping[key] = stream

        first = False
        if not key in color_map:
            color_map[key] = choosecolor(color_pos)
            first = True
            color_pos = color_pos + 1

        c = color_map[key]

        rate_frame = get_rate_frame(group, plotRollingWindow)

        # Scale to MBit/s
        rate_frame = rate_frame * 10 ** -6

        subplot.plot(rate_frame.index, rate_frame, color=c ,zorder=-1, linewidth=0.2)
        
        if first:
            line = lines.Line2D([], [], color=c, label="(%s) %s:%d->%s:%d" % key)
            legend_list.append(line)

def plot_latencys(specfile, netboundPlot, p2pPlot):
    for event in specfile.timeline:
        if event.event == "delay_changed":
            new_delays = event.payload.split('-')
            p2pPlot.scatter(event.timestamp, float(new_delays[0].replace('ms','')) * 2.0, zorder=1) # p2p delay incurrend on both routers -> x2
            netboundPlot.scatter(event.timestamp,  float(new_delays[1].replace('ms','')), zorder=1)

def make_debug_plot(specfile: Specfile, data_frame: pd.DataFrame, outputfolder, plotRollingWindow, filetype):
    # Set up the plot
    fig = plt.figure()
    fig.set_size_inches(18.5, 15)
    fig.suptitle(specfile.GUID, fontsize=14)

    # Some padding for the whole plot
    plt.subplots_adjust(0.04,0.06,0.96,0.94, 0.175, 0.175)

    # Sub-divide the plot into an upper area for b
    # andwidth and a lower area for queue stats
    gs = gridspec.GridSpec(2,1, height_ratios=[0.6, 0.5])
    bandwidth_plots = gridspec.GridSpecFromSubplotSpec(2, 2, subplot_spec = gs[0], hspace=1) # hspace ist dubios
    queue_plots = gridspec.GridSpecFromSubplotSpec(5, 2, subplot_spec = gs[1], hspace=1) # hspace ist dubios

    to_left_before_btln = plt.subplot(bandwidth_plots[0])
    to_left_after_btln = plt.subplot(bandwidth_plots[2], sharey=to_left_before_btln, sharex=to_left_before_btln)

    to_right_before_btln = plt.subplot(bandwidth_plots[1], sharey=to_left_before_btln, sharex=to_left_before_btln)
    to_right_after_btln = plt.subplot(bandwidth_plots[3], sharey=to_left_before_btln, sharex=to_left_before_btln)

    to_left_tcp_drop = plt.subplot(queue_plots[0], sharex=to_left_before_btln)
    to_left_call_drop = plt.subplot(queue_plots[2], sharex=to_left_before_btln)
    to_left_queue_length = plt.subplot(queue_plots[4], sharex=to_left_before_btln)
    to_left_queuing_delays = plt.subplot(queue_plots[6], sharex=to_left_before_btln) # TODO count drops in qdisc and at enqueue
    netboundRTT = plt.subplot(queue_plots[8], sharex=to_left_before_btln) # TODO count drops in qdisc and at enqueue

    to_right_tcp_drop = plt.subplot(queue_plots[1], sharey = to_left_tcp_drop, sharex=to_left_before_btln)
    to_right_call_drop = plt.subplot(queue_plots[3], sharey = to_left_call_drop, sharex=to_left_before_btln)
    to_right_queue_length = plt.subplot(queue_plots[5], sharey = to_left_queue_length, sharex=to_left_before_btln)
    to_right_queuing_delays = plt.subplot(queue_plots[7], sharey = to_left_queuing_delays, sharex=to_left_before_btln) # TODO count drops in qdisc and at enqueue
    p2pRTT = plt.subplot(queue_plots[9], sharex=to_left_before_btln) # TODO count drops in qdisc and at enqueue

    to_left_tcp_drop.set_ylim([0,10])
    to_right_tcp_drop.set_ylim([0,10])
    to_left_call_drop.set_ylim([0,10])
    to_right_call_drop.set_ylim([0,10])

    to_left_queuing_delays.set_ylim([0,100])
    to_right_queuing_delays.set_ylim([0,100])

    # Set titles
    to_left_before_btln.set_title("Traffic going left (before btln) (avg %sms)" % plotRollingWindow)
    to_left_after_btln.set_title("Traffic going left (after btln) (avg %sms)" % plotRollingWindow)

    to_right_before_btln.set_title("Traffic going right (before btln) (avg %sms)" % plotRollingWindow)
    to_right_after_btln.set_title("Traffic going right (after btln) (avg %sms)" % plotRollingWindow)

    to_left_tcp_drop.set_title("TCP Packets dropped with dest on left side (rolling sum %sms)" % plotRollingWindow)
    to_left_call_drop.set_title("CALL Packets dropped with dest on left side (rolling sum %sms)" % plotRollingWindow)
    to_left_queue_length.set_title("Traffic to left side netif queue length (rolling max %sms)" % plotRollingWindow)
    to_left_queuing_delays.set_title("Traffic to left side netif queue delay (rolling max %sms)" % plotRollingWindow)
    netboundRTT.set_title("Netbound RTT (+ 'real' RTT incurred by our DFN uplink)")

    to_right_tcp_drop.set_title("TCP Packets dropped with dest on right side (rolling sum %sms)" % plotRollingWindow)
    to_right_call_drop.set_title("CALL Packets dropped with dest on right side (rolling sum %sms)" % plotRollingWindow)
    to_right_queue_length.set_title("Traffic to right side netif queue length (rolling max %sms)" % plotRollingWindow)
    to_right_queuing_delays.set_title("Traffic to right side netif queue delay (rolling max %sms)" % plotRollingWindow)
    p2pRTT.set_title("Local, P2P RTT")

    # Set x and y titles
    to_left_before_btln.set_ylabel("Rate [Mb/s]")
    to_left_after_btln.set_ylabel("Rate [Mb/s]")
    to_left_before_btln.set_xlabel("Time")
    to_left_after_btln.set_xlabel("Time")

    to_right_before_btln.set_ylabel("Rate [Mb/s]")
    to_right_after_btln.set_ylabel("Rate [Mb/s]")
    to_right_before_btln.set_xlabel("Time")
    to_right_after_btln.set_xlabel("Time")

    to_left_tcp_drop.set_ylabel("Pckts.")
    to_left_call_drop.set_ylabel("Pckts.")
    to_left_queue_length.set_ylabel("Pckts.")
    to_left_queuing_delays.set_ylabel("ms")

    to_right_tcp_drop.set_ylabel("Pckts.")
    to_right_call_drop.set_ylabel("Pckts.")
    to_right_queue_length.set_ylabel("Pckts.")
    to_right_queuing_delays.set_ylabel("ms")

    left_NIC_enqueue, left_NIC_dequeue, right_NIC_enqueue, right_NIC_dequeue = sort_capture_into_queues(data_frame)

    plot_streams(to_left_before_btln, left_NIC_enqueue, plotRollingWindow, specfile)
    plot_streams(to_left_after_btln, left_NIC_dequeue, plotRollingWindow, specfile)

    plot_streams(to_right_before_btln, right_NIC_enqueue, plotRollingWindow, specfile)
    plot_streams(to_right_after_btln, right_NIC_dequeue, plotRollingWindow, specfile)

    fig.legend(handles=legend_list, ncol=4, loc='center', bbox_to_anchor=(0.5, 0.71), frameon=False)

    # Plot the queue delay packets experienced
    # 1st filter to the packets which have a non-zero queue delay
    # left_NIC_dequeue_non_zero_delay = left_NIC_dequeue[left_NIC_dequeue['queue_delay'].notnull()]
    # to_left_queuing_delays.plot(left_NIC_dequeue_non_zero_delay.index, left_NIC_dequeue_non_zero_delay['queue_delay'].rolling("%dms" % plotRollingWindow, closed='neither').max() * 1000)
    # right_NIC_dequeue_non_zero_delay = right_NIC_dequeue[right_NIC_dequeue['queue_delay'].notnull()]
    # to_right_queuing_delays.plot(right_NIC_dequeue_non_zero_delay.index, right_NIC_dequeue_non_zero_delay['queue_delay'].rolling("%dms" % plotRollingWindow, closed='neither').max() * 1000)

    # Plot Queue length as a rolling max value with a 50ms sliding window
    # to_left_queue_length.plot(left_NIC_dequeue.index, left_NIC_dequeue['raw.qlen'].rolling("%dms" % plotRollingWindow, closed='neither').max())
    # to_right_queue_length.plot(right_NIC_dequeue.index, right_NIC_dequeue['raw.qlen'].rolling("%dms" % plotRollingWindow, closed='neither').max())

    # Plot the limit
    if left_NIC_dequeue['raw.limit'][0] < 500:
        to_left_queue_length.plot(left_NIC_dequeue.index, left_NIC_dequeue['raw.limit'], '-o')
        to_right_queue_length.plot(right_NIC_dequeue.index, right_NIC_dequeue['raw.limit'], '-o')

    # Plot Drops of Call Packets
    # We mark every packet that was enqueue as not dropped, when we say it again in dequeue
    # So we can query the enqueue list for packets that were never dequeued --> dropped
    callToLeft = left_NIC_enqueue[(left_NIC_enqueue['l3.src'] == avdavdb) & (left_NIC_enqueue['l3.dst'] == avdavda)]
    callToRight = right_NIC_enqueue[(right_NIC_enqueue['l3.dst'] == avdavdb) & (right_NIC_enqueue['l3.src'] == avdavda)]
    tcpToLeft = left_NIC_enqueue[(left_NIC_enqueue['l3.src'] == tcpb) & (left_NIC_enqueue['l3.dst'] == tcpa)]
    tcpToRight = right_NIC_enqueue[(right_NIC_enqueue['l3.dst'] == tcpb) & (right_NIC_enqueue['l3.src'] == tcpa)]

    if len(callToLeft) > 0:
        to_left_call_drop.plot(callToLeft.index, callToLeft['dropped'].rolling("%dms" % plotRollingWindow, closed='neither').sum().fillna(0))
    if len(callToRight) > 0:
        to_right_call_drop.plot(callToRight.index, callToRight['dropped'].rolling("%dms" % plotRollingWindow, closed='neither').sum().fillna(0))
    
    if len(tcpToLeft) > 0:
        to_left_tcp_drop.plot(tcpToLeft.index, tcpToLeft['dropped'].rolling("%dms" % plotRollingWindow, closed='neither').sum().fillna(0))
    if len(tcpToRight) > 0:
        to_right_tcp_drop.plot(tcpToRight.index, tcpToRight['dropped'].rolling("%dms" % plotRollingWindow, closed='neither').sum().fillna(0))

    # Plot the latency settings
    plot_latencys(specfile, netboundRTT, p2pRTT)

    plt.savefig(outputfolder + specfile.GUID + "." + filetype)
    plt.close()



# # Region: PIA PLOT Packet-Interarrival-Timing
# def make_pia_plot(specfile: Specfile, data_frame: pd.DataFrame, outputfolder, filetype):
#     # Set up the plot
#     fig = plt.figure()
#     fig.set_size_inches(18.5, 10.5)
#     fig.suptitle(specfile.GUID, fontsize=14)

#     left_NIC_enqueue, left_NIC_dequeue, right_NIC_enqueue, right_NIC_dequeue = sort_capture_into_queues(data_frame)
#     leftEnqList = get_interpacket_time(left_NIC_enqueue, avdavdb, avdavda)
#     leftDeqList = get_interpacket_time(left_NIC_dequeue, avdavdb, avdavda)
#     rightEnqList = get_interpacket_time(right_NIC_enqueue, avdavda, avdavdb)
#     rightDeqList = get_interpacket_time(right_NIC_dequeue, avdavda, avdavdb)

#     make_quad_cdf(leftEnqList, leftDeqList, rightEnqList, rightDeqList, getmaxbw(specfile.timeline))

#     plt.savefig(outputfolder + specfile.GUID + "__piaplot__" + "." + filetype)
#     plt.close()

# # Region: Make Violin Plot
# def make_bw_plot(specfile: Specfile, data_frame: pd.DataFrame, outputfolder, filetype):
#     fig = plt.figure()
#     fig.set_size_inches(8.25, 11.75)
#     fig.suptitle(specfile.GUID, fontsize=14)

#     d = make_rate_dataframe([data_frame], [getp2prtt(specfile.timeline)], "all")

#     plot = sns.ecdfplot(data=d, x="rate", hue="flow")

#     plot.set_xlim(0.0, (getmaxbw(specfile.timeline) + 0.5)*10**6)

#     plt.savefig(outputfolder + specfile.GUID + "__bwplot__"+ ".png")
#     plt.close()

#     # and now, make a violin

#     fig = plt.figure()
#     fig.set_size_inches(8.25, 11.75)
#     fig.suptitle(specfile.GUID, fontsize=14)

#     d = make_rate_dataframe([data_frame], [getp2prtt(specfile.timeline)], "all")

#     sns.violinplot(data=d, y="rate", x="rtt", hue="flow")

#     plot.set_ylim(0.0, (getmaxbw(specfile.timeline) + 0.5)*10**6)

#     plt.savefig(outputfolder + specfile.GUID + "__violin__"+ ".png")
#     plt.close()
