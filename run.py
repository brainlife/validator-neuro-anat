#!/usr/bin/env python

import os
import json
import re
import subprocess
import nibabel

# Things that this script checks
# 
# * make sure mrinfo runs successfully on specified t1 file
# * make sure t1 is 3d
# * raise warning if t1 transformation matrix isn't unit matrix (identity matrix)

# display where this is running
# import socket
# print(socket.gethostname())

with open('config.json') as config_json:
    config = json.load(config_json)

results = {"errors": [], "warnings": []}

directions = None

def check_affine(affine):
    if affine[0][0] != 1: results['warnings'].append("transform matrix 0.1 is not 1")
    if affine[0][1] != 0: results['warnings'].append("transform matrix 0.2 is not 0")
    if affine[0][2] != 0: results['warnings'].append("transform matrix 0.2 is not 0")
    if affine[1][0] != 0: results['warnings'].append("transform matrix 1.0 is not 0")
    if affine[1][1] != 1: results['warnings'].append("transform matrix 1.1 is not 1")
    if affine[1][2] != 0: results['warnings'].append("transform matrix 1.2 is non 0")
    if affine[2][0] != 0: results['warnings'].append("transform matrix 2.0 is not 0")
    if affine[2][1] != 0: results['warnings'].append("transform matrix 2.1 is not 0")
    if affine[2][2] != 1: results['warnings'].append("transform  matrix 2.2 is not 1")

# TODO - I am not sure what I need to do differently between t1 and t2
def validate_anat(path):

    try:
        print('checking anatomy')
        img = nibabel.load(path)
        results['headers'] = str(img.header)
        results['base_affine'] = str(img.header.get_base_affine())

        # check dimensions
        dims = img.header['dim'][0]
        if dims != 3:
            results['errors'].append("input should be 3D but has " + str(dims))

        check_affine(img.header.get_base_affine())

    except Exception as e:
        results['errors'].append("nibabel failed on t1. error code: " + str(e))

if config.has_key('t1'):
    validate_anat(config['t1'])

    # TODO - normalize (for now, let's just symlink)
    # TODO - if it's not .gz'ed, I should?
    os.symlink(config['t1'], "t1.nii.gz")

if config.has_key('t2'):
    validate_anat(config['t2'])

    # TODO - normalize (for now, let's just symlink)
    # TODO - if it's not .gz'ed, I should?
    os.symlink(config['t2'], "t2.nii.gz")

with open("product.json", "w") as fp:
    json.dump(results, fp)
