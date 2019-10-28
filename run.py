#!/usr/bin/env python

import os
import json
import re
import subprocess
import nibabel
import numpy as np
from PIL import Image, ImageDraw
import io
import base64
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

def fix_level(image):
    image = image - np.min(image)
    image_max = np.max(image)
    return (image / image_max)*500

# TODO - I am not sure what I need to do differently between t1 and t2
def validate_anat(path):

    try:
        #print('checking anatomy')
        img = nibabel.load(path)
        results['headers'] = str(img.header)
        results['base_affine'] = str(img.header.get_base_affine())

        # check dimensions
        dims = img.header['dim'][0]
        if dims != 3:
            results['errors'].append("input should be 3D but has " + str(dims))

        results['meta'] = {
            "dim":img.header['dim'].tolist(),
            "pixdim":img.header['pixdim'].tolist()
        }

        check_affine(img.header.get_base_affine())

        #################################################################
        # save some mid slices
        #
        img_data = img.get_fdata()
        slice_x_pos = img.header['dim'][1]/2
        slice_y_pos = img.header['dim'][2]/2
        slice_z_pos = img.header['dim'][3]/2
        slice_x = img_data[slice_x_pos, :, :]
        slice_y = img_data[:, slice_y_pos, :]
        slice_z = img_data[:, :, slice_z_pos]

        slice_x = fix_level(slice_x).T
        slice_y = fix_level(slice_y).T
        slice_z = fix_level(slice_z).T

        image_x = Image.fromarray(np.flipud(slice_x)).convert('L')
        image_x.save('x.png')
        image_y = Image.fromarray(np.flipud(slice_y)).convert('L')
        image_y.save('y.png')
        image_z = Image.fromarray(np.flipud(slice_z)).convert('L')
        image_z.save('z.png')

        results['brainlife'] = []
        image_a = io.BytesIO()
        image_x.save(image_a, format="JPEG")
        results['brainlife'].append({
            "type": "image/jpeg",
            "name": "x "+str(slice_x_pos),
            "base64": base64.b64encode(image_a.getvalue())
        })
        #
        #
        #################################################################

    except Exception as e:
        print(e)
        results['errors'].append("nibabel failed on t1. error code: " + str(e))

if config.has_key('t1'):
    validate_anat(config['t1'])

    # TODO - normalize (for now, let's just symlink)
    # TODO - if it's not .gz'ed, I should?
    if os.path.exists("t1.nii.gz"):
        os.remove("t1.nii.gz")
    os.symlink(config['t1'], "t1.nii.gz")

if config.has_key('t2'):
    validate_anat(config['t2'])

    # TODO - normalize (for now, let's just symlink)
    # TODO - if it's not .gz'ed, I should?
    if os.path.exists("t2.nii.gz"):
        os.remove("t2.nii.gz")
    os.symlink(config['t2'], "t2.nii.gz")

with open("product.json", "w") as fp:
    json.dump(results, fp)

