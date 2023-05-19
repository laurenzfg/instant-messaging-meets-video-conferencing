#!/usr/bin/env python3

from multiprocessing import Pool
import numpy as np
import pandas as pd

from utils import create_data_frame, get_rate_frame, getToLeftTrafficClasses, parse_specfile

# This beasts conducts an analysis over numerous runs.
# returns a dataframe in CSV format. One bandwidth per second Columns
# - Time Delta (0s, 1s, ...)
# - RTT
# - MVCA used
# - rates

index = pd.read_csv("index.csv").set_index("guid")

def process_file(inputtuple):
    specfile_name = inputtuple[0]
    scenario = inputtuple[1]

    print("tallying file %s" % specfile_name)

    specfile = parse_specfile(specfile_name)

    call_rates_table = create_data_frame(specfile.frontmatter['bpfcapture'])

    matadata_name = specfile_name.replace(".txt", ".csv")
    metadata = pd.read_csv(matadata_name)

    packets = None
    if scenario == "BWP":
        packets, _, _ = getToLeftTrafficClasses("all", call_rates_table, useEnqueue=True)
    elif scenario == "JUST_TCP":
        _, packets, _ = getToLeftTrafficClasses("all", call_rates_table, useEnqueue=True)

    window = 1000

    # Calculate the rates
    call_rates = get_rate_frame(packets, window)

    # We want to plot from the 4th event (last 4MBit, end of ramp up time on)
    start = None
    if scenario == "BWP":
        start = specfile.timeline[4].timestamp
    elif scenario == "JUST_TCP":
        start = specfile.timeline[1].timestamp + pd.Timedelta(45, unit="s")

    # Offset the index by the start
    call_rates.index = call_rates.index - start
    call_rates.index = call_rates.index.round('S')

    # cut off before start
    call_rates = call_rates[call_rates.index >= pd.Timedelta(0, unit="s")]

    # Expand the Rates Series into a full-blown DF
    call_rates_table = call_rates.to_frame()

    # Annotate by MVCA name
    call_rates_table.insert(1, "mvca", metadata["mvca"][0])
    call_rates_table.insert(2, "rtt", metadata["rtt"][0])
    call_rates_table.insert(3, "bw", metadata["bw"][0])
    call_rates_table.insert(4, "innerqdisc", metadata["innerqdisc"][0])
    call_rates_table.insert(5, "cong", metadata["cong"][0])

    return call_rates_table

def make_profile(scenario: str, filename: str, bw = 2.0):
    global index

    my_index = index[index["scenario"] == scenario]
    if scenario == "JUST_TCP":
        my_index = my_index[my_index["bw"] == bw]

    my_index = my_index.index + ".txt"

    # Now my_index is a list of BWProfile GUIDs

    scenario = np.repeat(scenario, len(my_index))

    process_pool = Pool(processes=20)
    # Start processes in the pool
    dfs = process_pool.map(process_file, zip(my_index, scenario))

    df = pd.concat(dfs)

    df.to_csv("/opt/grote/studydata/%s.csv.gz" % filename,
              index=True,
              compression="gzip")


# make_profile("JUST_TCP", "tcprofiles2mbit", 2.0)
# make_profile("JUST_TCP", "tcprofiles03mbit", 0.3)
make_profile("BWP", "bwprofiles")
