#!/usr/bin/env python
########################################################################################################################
#
#
# Compute TSNR using inputed anat.nii.gz and fmri.nii.gz files.
#
# ----------------------------------------------------------------------------------------------------------------------
# Copyright (c) 2014 Polytechnique Montreal <www.neuro.polymtl.ca>
# Authors: Julien Cohen-Adad, Sara Dupont
# Created: 2015-03-12
#
# About the license: see the file LICENSE.TXT
########################################################################################################################

import sys
#import time
from msct_parser import *
import sct_utils as sct
# from sct_average_data_across_dimension import average_data_across_dimension


class Param:
    def __init__(self):
        self.debug = 0
        self.verbose = 1


########################################################################################################################
######------------------------------------------------- Classes --------------------------------------------------######
########################################################################################################################

# ----------------------------------------------------------------------------------------------------------------------
# TSNR -----------------------------------------------------------------------------------------------------------------
class Tsnr:
    def __init__(self, param=None, fmri=None, anat=None):
        self.param = param
        self.fmri = fmri
        self.anat = anat

    def compute(self):

        fname_data = self.fmri

        # # create temporary folder
        # sct.printv('\nCreate temporary folder...', self.param.verbose)
        # path_tmp = 'tmp.'+time.strftime("%y%m%d%H%M%S/")
        # status, output = sct.run('mkdir '+path_tmp, self.param.verbose)

        # # motion correct the fmri data
        # # sct.printv('\nMotion correct the fMRI data...', self.param.verbose, 'normal')
        # path_fmri, fname_fmri, ext_fmri = sct.extract_fname(self.fmri)
        # fname_fmri_moco = fname_fmri
        # # print sct.slash_at_the_end(path_fmri) + fname_fmri
        # # sct.run('mcflirt -in ' + sct.slash_at_the_end(path_fmri, 1) + fname_fmri + ' -out ' + fname_fmri_moco)

        # compute tsnr
        sct.printv('\nCompute the tSNR...', self.param.verbose, 'normal')
        fname_data_mean = sct.add_suffix(fname_data, '_mean')
        sct.run('sct_maths -i '+fname_data+' -o '+fname_data_mean+' -mean t')
        # if not average_data_across_dimension(fname_data, fname_data_mean, 3):
        #     sct.printv('ERROR in average_data_across_dimension', 1, 'error')
        # sct.run('fslmaths ' + fname_data + ' -Tmean ' + fname_data_mean)
        fname_data_std = sct.add_suffix(fname_data, '_std')
        sct.run('sct_maths -i '+fname_data+' -o '+fname_data_std+' -mean t')
        # if not average_data_across_dimension(fname_data, fname_data_std, 3, 1):
        #     sct.printv('ERROR in average_data_across_dimension', 1, 'error')
        # sct.run('fslmaths ' + fname_data + ' -Tstd ' + fname_data_std)
        fname_tsnr = sct.add_suffix(fname_data, '_tsnr')
        from msct_image import Image
        nii_mean = Image(fname_data_mean)
        data_mean = nii_mean.data
        data_std = Image(fname_data_std).data
        data_tsnr = data_mean/data_std
        nii_tsnr = nii_mean
        nii_tsnr.data = data_tsnr
        nii_tsnr.setFileName(fname_tsnr)
        nii_tsnr.save()
        # sct.run('fslmaths ' + fname_data_mean + ' -div ' + fname_data_std + ' ' + fname_tsnr)

        # Remove temp files
        sct.printv('\nRemove temporary files...', self.param.verbose, 'normal')
        import os
        os.remove(fname_data_mean)
        os.remove(fname_data_std)

        # to view results
        sct.printv('\nDone! To view results, type:', self.param.verbose, 'normal')
        sct.printv('fslview '+fname_tsnr+' &\n', self.param.verbose, 'info')


def get_parser():
    parser = Parser(__file__)
    parser.usage.set_description('Compute temporal SNR (tSNR) in fMRI time series.')
    parser.add_option(name='-i',
                      type_value='file',
                      description='fMRI data',
                      mandatory=True,
                      example='fmri.nii.gz')
    parser.add_option(name='-v',
                      type_value='multiple_choice',
                      description='verbose',
                      mandatory=False,
                      example=['0', '1'])
    return parser

def main(args=None):

    param = Param()
    if args is None:
        args = sys.argv[1:]

    if param.debug:
        print '\n*** WARNING: DEBUG MODE ON ***\n'
    else:

        parser = get_parser()
        arguments = parser.parse(args)
        input_fmri = arguments['-i']

        if '-v' in arguments:
            param.verbose = int(arguments['-v'])

        tsnr = Tsnr(param=param, fmri=input_fmri)
        tsnr.compute()


if __name__ == '__main__':
    main()
