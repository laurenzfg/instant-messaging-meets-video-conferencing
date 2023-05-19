#!/usr/bin/env python3

# This script processes a file specification.
# Set the rolling window as the 2nd argument!
# File is created in place in the folder of the specfile
# Author: Laurenz Grote

import sys
from utils import create_data_frame, parse_specfile
from avgbwdist import process_file
from plot import make_debug_plot

import pandas as pd

specfile_name = sys.argv[1]
specfile = parse_specfile(specfile_name)

data_frame = create_data_frame(specfile.frontmatter['bpfcapture'])

matadata_name = specfile_name.replace(".txt", ".csv")
metadata = pd.read_csv(matadata_name)

make_debug_plot(specfile, data_frame, "", int(sys.argv[2]), sys.argv[3])
process_file(data_frame, metadata)