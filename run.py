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
#import socket
#print(socket.gethostname())

with open('config.json') as config_json:
    config = json.load(config_json)

results = {"errors": [], "warnings": []}

directions = None

#TODO - I am not sure what I need to do differently between t1 and t2
def validate_t1t2(path):
	try:
		print("running mrinfo")
		info = subprocess.check_output(["mrinfo", path], shell=False)
		results['detail'] = info
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
			results['warnings'].append("T1/T2 has non-optimal transformation matrix. It should be 1 0 0 / 0 1 0 / 0 0 1")


	except subprocess.CalledProcessError as err:
		results['errors'].append("mrinfo failed on t1/t2. error code: "+str(err.returncode))

if config.has_key('t1'):
    validate_t1t2(config['t1'])

    #TODO - normalize (for now, let's just symlink)
    #TODO - if it's not .gz'ed, I should?
    os.symlink(config['t1'], "t1.nii.gz")

if config.has_key('t2'):
    validate_t1t2(config['t2'])

    #TODO - normalize (for now, let's just symlink)
    #TODO - if it's not .gz'ed, I should?
    os.symlink(config['t2'], "t2.nii.gz")

with open("products.json", "w") as fp:
    json.dump([results], fp)

