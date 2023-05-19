#!/usr/bin/env python3
import os
import subprocess
import sys

filename = sys.argv[1]
guid = filename[:-4]
foldername = guid + "_" + "qoe"

# make sure folder exists
if not os.path.exists(foldername):
    os.makedirs(foldername)

outmask = foldername + "/" + "out_%03d.png"
outglob = foldername + "/" + "out_*.png"
subprocess.run('ffmpeg -i {} -vf "select=(eq(n\,{})+eq(n\,{})+eq(n\,{})+eq(n\,{})+eq(n\,{})+eq(n\,{})+eq(n\,{})+eq(n\,{})+eq(n\,{})+eq(n\,{}))" -vsync vfr {}'.format(filename, *range(190, 200), outmask), shell=True)

if os.path.isfile(foldername + "/" + "out_001.png"):
    subprocess.run('mogrify  -shave 35%x10% -gravity center {}'.format(outglob), shell=True)
