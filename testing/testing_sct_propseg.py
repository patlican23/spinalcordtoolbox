#!/usr/bin/env python
#########################################################################################
#
# Test function sct_propseg
#
# ---------------------------------------------------------------------------------------
# Copyright (c) 2014 Polytechnique Montreal <www.neuro.polymtl.ca>
# Author: Augustin Roux
# modified: 2014/10/09
#
# About the license: see the file LICENSE.TXT
#########################################################################################

#import sct_utils as sct
import commands
import shutil
import getopt
import sys
import time
import sct_utils as sct
import os
import nibabel
import numpy as np
import math
from tabulate import tabulate

class param:
    def __init__(self):
        self.download = 0
        self.remove_tmp_file = 0
        self.verbose = 1
        self.url_git = 'https://github.com/neuropoly/sct_testing_data.git'
        self.path_data = '/home/django/benjamindeleener/data/PropSeg_data/'

def main():
    # Check input parameters
    try:
        opts, args = getopt.getopt(sys.argv[1:],'h:d:p:f:r:a:')
    except getopt.GetoptError:
        usage()
    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit(0)
        if opt == '-d':
            param.download = int(arg)
        if opt == '-p':
            param.path_data = arg
        if opt == '-r':
            param.remove_tmp_file = int(arg)

    start_time = time.time()

    # download data
    if param.download:
        sct.printv('\nDownloading testing data...', param.verbose)
        # remove data folder if exist
        if os.path.exists('sct_testing_data_propseg'):
            sct.printv('WARNING: sct_testing_data already exists. Removing it...', param.verbose, 'warning')
            sct.run('rm -rf sct_testing_data_propseg')
        # clone git repos
        sct.run('git clone '+param.url_git)
        # update path_data field 
        param.path_data = 'sct_testing_data_propseg'

    # get absolute path and add slash at the end
    param.path_data = sct.slash_at_the_end(os.path.abspath(param.path_data), 1)

    # segment all data in t2 folder
    results_t2 = []
    for dirname in os.listdir(param.path_data+"t2/"):
        if dirname not in ['._.DS_Store','.DS_Store']:
            for filename in os.listdir(param.path_data+"t2/"+dirname):
                if filename.startswith('t2_') and not filename.endswith('_seg.nii.gz') and not filename.endswith('_detection.nii.gz'):
                    [d_old,d_new],[r_old,r_new] = segmentation(param.path_data+"t2/"+dirname+"/"+filename,param.path_data+"t2/"+dirname+"/",'t2')
                    if d_old == 0: d_old = 'OK'
                    else: d_old = 'Not In'
                    if d_new == 0: d_new = 'OK'
                    else: d_new = 'Not In'
                    results_t2.append([dirname,d_old,d_new,round(r_old,2),round(r_new,2)])

    # Print results
    print ''
    print tabulate(results_t2, headers=["Subject-T2","Detect-old","Detect-new","DC-old", "DC-new"], floatfmt=".2f")

    # display elapsed time
    elapsed_time = time.time() - start_time
    print 'Finished! Elapsed time: '+str(int(round(elapsed_time)))+'s\n'

    # remove temp files
    if param.remove_tmp_file:
        sct.printv('\nRemove temporary files...', param.verbose)
        sct.run('rm -rf '+param.path_tmp, param.verbose)

    sys.exit(0)

def segmentation(fname_input, output_dir, image_type):
    # parameters
    path_in, file_in, ext_in = sct.extract_fname(fname_input)
    segmentation_filename_old = path_in + 'old/' + file_in + '_seg' + ext_in
    manual_segmentation_filename_old = path_in + 'manual_' + file_in + ext_in
    detection_filename_old = path_in + 'old/' + file_in + '_detection' + ext_in
    segmentation_filename_new = path_in + 'new/' + file_in + '_seg' + ext_in
    manual_segmentation_filename_new = path_in + 'manual_' + file_in + ext_in
    detection_filename_new = path_in + 'new/' + file_in + '_detection' + ext_in

    # initialize results
    results_detection = [0,0]
    results_segmentation = [0.0,0.0]

    # perform PropSeg old version
    sct.create_folder(output_dir+'old')
    cmd = 'sct_propseg_old -i ' + fname_input \
        + ' -o ' + output_dir+'old' \
        + ' -t ' + image_type \
        + ' -detect-nii'
    status_propseg_old, output_propseg_old = sct.run(cmd)

    # check if spinal cord is correctly detected with old version of PropSeg
    status_detection_old, output_detection_old = sct.run("isct_check_detection.py -i "+detection_filename_old+" -t "+manual_segmentation_filename_old)
    results_detection[0] = status_detection_old

    # compute Dice coefficient for old version of PropSeg
    cmd_validation = 'sct_dice_coefficient '+segmentation_filename_old \
                + ' '+manual_segmentation_filename_old \
                + ' -bzmax'
    status_validation_old, output_validation_old = sct.run(cmd_validation)
    results_segmentation[0] = float(output_validation_old.split()[-1])
    if math.isnan(results_segmentation[0]):
        results_segmentation[0] = 0.0

    # perform PropSeg new version
    sct.create_folder(output_dir+'new')
    cmd = 'sct_propseg -i ' + fname_input \
        + ' -o ' + output_dir+'new' \
        + ' -t ' + image_type \
        + ' -detect-nii'
    status_propseg_new, output_propseg_new = sct.run(cmd)

    # check if spinal cord is correctly detected with new version of PropSeg
    status_detection_new, output_detection_new = sct.run("isct_check_detection.py -i "+detection_filename_new+" -t "+manual_segmentation_filename_new)
    results_detection[1] = status_detection_new

    # compute Dice coefficient for new version of PropSeg
    cmd_validation = 'sct_dice_coefficient '+segmentation_filename_new \
                + ' '+manual_segmentation_filename_new \
                + ' -bzmax'
    status_validation_new, output_validation_new = sct.run(cmd_validation)
    results_segmentation[1] = float(output_validation_new.split()[-1])
    if math.isnan(results_segmentation[1]):
        results_segmentation[1] = 0.0

    return results_detection, results_segmentation


if __name__ == "__main__":
    # call main function
    param = param()
    main()