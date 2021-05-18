#!/usr/bin/env python3

import os
import json
import re
import subprocess
import nibabel
import numpy as np
from PIL import Image, ImageDraw
import io
import base64
import math
import binascii

# Things that this script checks
# 
# * make sure mrinfo runs successfully on specified t1 file
# * make sure t1 is 3d
# * raise warning if t1 transformation matrix isn't unit matrix (identity matrix)

# display where this is running
# import socket
# print(socket.gethostname())

with open('config.json', encoding='utf8') as config_json:
    config = json.load(config_json)

results = {
    "errors": [], 
    "warnings": [], 
}

#copy _input
if "_inputs" in config:
    iconfig = config["_inputs"][0]
    if "meta" in iconfig:
        results["meta"] = iconfig["meta"]
    if "tags" in iconfig:
        results["tags"] = iconfig["tags"]
    if "datatype_tags" in iconfig:
        results["datatype_tags"] = iconfig["datatype_tags"]

directions = None
if not os.path.exists("secondary"):
    os.mkdir("secondary")

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
    #check to make sure nifti starts with gzip marker
    with open(path, 'rb') as test_f:
        if binascii.hexlify(test_f.read(2)) != b'1f8b':
            results['errors'].append("file doesn't look like a gzip-ed nifti");
            return

    try:
        #print('checking anatomy')
        img = nibabel.load(path)
        #results['headers'] = str(img.header)
        #results['base_affine'] = str(img.header.get_base_affine())
    
        results['meta'] = {"nifti_headers": {}}
        for key in img.header:
            value = img.header[key]
            results['meta']['nifti_headers'][key] = value
        results['meta']['nifti_headers']['base_affine'] = img.header.get_base_affine()

        # check dimensions
        dims = img.header['dim'][0]
        if dims != 3:
            results['errors'].append("input should be 3D but has " + str(dims))

        #results['meta'] = {
        #    "dim":img.header['dim'].tolist(),
        #    "pixdim":img.header['pixdim'].tolist()
        #}

        #affine shouldn't always be identity
        #check_affine(img.header.get_base_affine())

        #################################################################
        # save some mid slices
        #
        img_data = img.get_fdata()
        slice_x_pos = int(img.header['dim'][1]/2)
        slice_y_pos = int(img.header['dim'][2]/2)
        slice_z_pos = int(img.header['dim'][3]/2)
        slice_x = img_data[slice_x_pos, :, :]
        slice_y = img_data[:, slice_y_pos, :]
        slice_z = img_data[:, :, slice_z_pos]

        slice_x = fix_level(slice_x).T
        slice_y = fix_level(slice_y).T
        slice_z = fix_level(slice_z).T

        image_x = Image.fromarray(np.flipud(slice_x)).convert('L')
        image_x.save('secondary/x.png')
        image_y = Image.fromarray(np.flipud(slice_y)).convert('L')
        image_y.save('secondary/y.png')
        image_z = Image.fromarray(np.flipud(slice_z)).convert('L')
        image_z.save('secondary/z.png')

        results['brainlife'] = []

        #copy secondary content to product.json (should I?)
        i = Image.open('secondary/x.png')
        buf = io.BytesIO()
        i.save(buf, format="PNG")
        #results['brainlife'].append({
        #    "type": "image/png",
        #    "name": "x "+str(slice_x_pos),
        #    "base64": base64.b64encode(buf.getvalue()).decode('ascii')
        #})

        i = Image.open('secondary/y.png')
        buf = io.BytesIO()
        i.save(buf, format="PNG")

        #results['brainlife'].append({
        #    "type": "image/png",
        #    "name": "y "+str(slice_y_pos),
        #    "base64": base64.b64encode(buf.getvalue()).decode('ascii')
        #})

        i = Image.open('secondary/z.png')
        buf = io.BytesIO()
        i.save(buf, format="PNG")

        #results['brainlife'].append({
        #    "type": "image/png",
        #    "name": "z "+str(slice_z_pos),
        #    "base64": base64.b64encode(buf.getvalue()).decode('ascii')
        #})        #
        #
        #################################################################

    except Exception as e:
        print(e)
        results['errors'].append("nibabel failed on t1. error code: " + str(e))

if not os.path.exists("output"):
    os.mkdir("output")

if 't1' in config:
    validate_anat(config['t1'])

    # TODO - normalize (for now, let's just symlink)
    # TODO - if it's not .gz'ed, I should?
    if os.path.lexists("output/t1.nii.gz"):
        os.remove("output/t1.nii.gz")
    os.symlink("../"+config['t1'], "output/t1.nii.gz")

if 't2' in config:
    validate_anat(config['t2'])

    # TODO - normalize (for now, let's just symlink)
    # TODO - if it's not .gz'ed, I should?
    if os.path.lexists("output/t2.nii.gz"):
        os.remove("output/t2.nii.gz")
    os.symlink("../"+config['t2'], "output/t2.nii.gz")

if 'flair' in config:
    validate_anat(config['flair'])

    # TODO - normalize (for now, let's just symlink)
    # TODO - if it's not .gz'ed, I should?
    if os.path.lexists("output/flair.nii.gz"):
        os.remove("output/flair.nii.gz")
    os.symlink("../"+config['flair'], "output/flair.nii.gz")

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
            np.int16, np.int32, np.int64, np.uint8,
            np.uint16, np.uint32, np.uint64)):
            ret = int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            ret = float(obj)
        elif isinstance(obj, (np.ndarray,)): 
            ret = obj.tolist()
        else:
            ret = json.JSONEncoder.default(self, obj)

        if isinstance(ret, (float)):
            if math.isnan(ret):
                ret = None

        if isinstance(ret, (bytes, bytearray)):
            ret = ret.decode("utf-8")

        return ret

with open("product.json", "w") as fp:
    json.dump(results, fp, cls=NumpyEncoder)

print("done");
