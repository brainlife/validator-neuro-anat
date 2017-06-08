#!/usr/bin/env python

import os
import json
import re
import subprocess

# Things that this script checks
# 
# * make sure mrinfo runs successfully on specified t1 file
# * make sure t1 is 3d
# * raise warning if t1 transformation matrix isn't unit matrix (identity matrix)

#display where this is running
import socket
print(socket.gethostname())

with open('config.json') as config_json:
    config = json.load(config_json)

results = {"errors": [], "warnings": []}

#TODO - how should I keep up wit this path?
#mrinfo="/N/soft/rhel6/mrtrix/0.3.15/mrtrix3/release/bin/mrinfo"

directions = None

if config['t1'] is None: 
    results['errors'].append("t1 not set")
else:
	try:
		print("running t1 mrinfo")
		info = subprocess.check_output(["mrinfo", config['t1']], shell=False)
		results['t1_mrinfo'] = info
		info_lines = info.split("\n")

		#check dimensions
		dim=info_lines[4]
		dims=dim.split("x")
		if len(dims) != 3:
			results['errors'].append("T1 should be 3D but has "+str(len(dims)))

		#check transform
		tl = info_lines[-5:-1]
		tl[0] = tl[0][12:] #remove "Transform:"
		m = []
		for line in tl:
			line = line.strip()
			strs = re.split('\s+', line)
			ml = []
			for s in strs:
				ml.append(float(s))
			m.append(ml)

		if m[0][0] == 1 and m[0][1] == 0 and m[0][1] == 0 and m[0][0] == 1 and m[0][1] == 0 and m[0][1] == 0 and m[0][0] == 1 and m[0][1] == 0 and m[0][1] == 0:
			None #good
		else:
			results['warnings'].append("T1 has non-optimal transformation matrix. It should be 1 0 0 / 0 1 0 / 0 0 1")

	except subprocess.CalledProcessError as err:
		results['errors'].append("mrinfo failed on t1. error code: "+str(err.returncode))

with open("products.json", "w") as fp:
    json.dump([results], fp)

