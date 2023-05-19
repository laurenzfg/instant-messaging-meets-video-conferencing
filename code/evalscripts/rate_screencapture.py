#!/usr/bin/env python3

import cv2
import sys
import csv
import os
import numpy as np
import pandas as pd
from brisque import BRISQUE

def process_file(metadata: pd.DataFrame):
    guid = metadata["guid"][0]
    foldername = "/opt/grote/studydata/%s_qoe/" % guid

    files = [os.path.join(foldername, f) for f in os.listdir(foldername)]
    
    stats = {
        "brisque": [],
    }

    for filename in files:
        if os.path.isfile(filename):
            cmp_img = cv2.imread(filename)
            obj = BRISQUE(url=False)
            brisque = obj.score(cmp_img)

            stats["brisque"].append(brisque)

    dataHeaders = ['guid', 'brisque']
    new_element = (guid, np.nan)

    if len(stats["brisque"]) > 0:
        new_element = (guid, np.median(np.array(stats["brisque"])))

    with open('/opt/grote/studydata/' + metadata["guid"][0] + '_qoe.csv', 'w', encoding='UTF8') as f:
        writer = csv.writer(f)

        # write the header
        writer.writerow(dataHeaders)

        # write the data
        writer.writerow(new_element)



specfile_name = sys.argv[1]

matadata_name = specfile_name.replace("_qoe/out_001.png", ".csv")
metadata = pd.read_csv(matadata_name)

process_file(metadata)

