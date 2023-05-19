#!/usr/bin/env python3

import csv
from multiprocessing import Pool
import numpy as np

import pandas as pd

from utils import getToLeftTrafficClasses

# This beasts conducts an analysis over numerous runs.
# Invoke: 1st argument: jobname
#         2nd argument: all the sweet, tasty files. May be multi-rtt, multi-bw, multi-bdp

dataHeaders = ['guid', 'call_bytes', 'tcp_bytes', 'obsdur', 'qdelay', 'qlen', 'callDropRate', 'tcpDropRate', 'didCallBreak']

def process_file(cap_data, metadata: pd.DataFrame):
    if metadata["scenario"][0] == "JUST_TCP":
        return

    skipFirstMinute = metadata["scenario"][0] == "JUST_CALL"
    callToLeft, tcpToLeft, observationDuration = getToLeftTrafficClasses("cong", cap_data, offsetByOneMinute=skipFirstMinute)
    callToLeftEnq, tcpToLeftEnq, _ = getToLeftTrafficClasses("cong", cap_data, useEnqueue=True, offsetByOneMinute=skipFirstMinute)

    callPacketsCount = len(callToLeft)
    tcpPacketsCount = len(tcpToLeft)

    if observationDuration < 5 or callPacketsCount < 5:
        new_element = (metadata["guid"][0], np.NaN, np.NaN, np.NaN, np.NaN, np.NaN, np.NaN, np.NaN)
        return new_element

    # Calculate the overall bandwidth
    callBytes = float(callToLeft['frame.len'].sum())
    tcpBytes = float(tcpToLeft['frame.len'].sum())
    qdelay = float(callToLeft['queue_delay'].sum()) / float(callPacketsCount)
    qlen = float(callToLeft['raw.qlen'].sum()) / float(callPacketsCount)

    callDropRate = np.NaN
    if len(callToLeftEnq) != 0:
        callDropRate = float(callToLeftEnq['dropped'].sum()) / float(len(callToLeftEnq))
    
    tcpDropRate = np.NaN
    if len(tcpToLeftEnq) != 0:
        tcpDropRate = float(tcpToLeftEnq['dropped'].sum()) / float(len(tcpToLeftEnq))

    didCallBreak = callToLeft.index[-10] < callToLeft.index[0] + pd.Timedelta("115 seconds")

    new_element = (metadata["guid"][0], callBytes, tcpBytes, observationDuration, qdelay, qlen, callDropRate, tcpDropRate, didCallBreak)

    with open('/opt/grote/studydata/' + metadata["guid"][0] + '_avgbwdist.csv', 'w', encoding='UTF8') as f:
        writer = csv.writer(f)

        # write the header
        writer.writerow(dataHeaders)

        # write the data
        writer.writerow(new_element)
