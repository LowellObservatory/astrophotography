#!/usr/bin/env python3
__doc__="""\
reduc_utils_fits.py - Fits utility functions for reduction pipeline

Simple Fits I/O utilities:


Usage: import reduc_utils as ru

Updates:
2021 Feb 28 - updates to load_fits_hdr()
2020 Dec 27 - initial version
"""

__intro__= """\
A small library of fits routines for use in the image reduction pipeline.
"""
__author__="Stephen Levine"
__date__="2021 Feb 28"

#------------------------------------------------------------------------
from   astropy.io import fits
import numpy as np

# import reduc_utils as ru

#------------------------------------------------------------------------
def load_fits_file (name=None, mode='readonly', echo=False):
    """\
    Load in a FITS image file.
    Assumes 1 HDU, and returns one header and one data unit.
    """
    try:
        with fits.open(name, mode) as hdu1:
            hdr = hdu1[0].header
            dat = hdu1[0].data
            if (echo != False):
                hdu1.info()
            # print ('hdrT = {}'.format(hdr))

    except:
        hdr = None
        dat = None
        # print ('hdrE = {}'.format(hdr))
        print ('Failed to open {}'.format(name))

    if ((echo == True) or (echo == 'Full') or (echo == 'HDump')):
        print (hdr)
            # print (sorted(dict(hdr.items())))
            # ru.print_struct(dict(hdr.items()))
            
    if ((echo == 'Full') or (echo == 'HSort')):
        for i in sorted(hdr.tostring(sep='\n').splitlines()):
            if ((i[0:3] != 'END') and (i[0] != ' ')):
                print (i)

    return hdr, dat

def load_fits_hdr (name=None, mode='readonly', echo=False):
    """\
    Load in a FITS file hdr.
    Assumes 1 HDU, and returns one header.
    Option to echo one keyword during load
    """
    try:
        with fits.open(name, mode) as hdu1:
            hdr = hdu1[0].header
                
            if (echo == 'Short'):
                hdu1.info()

            elif ((echo == True) or (echo == 'Full')):
                hdu1.info()
                print (hdr)

            elif (echo == 'HDump'):
                print (hdr)

            # elif (echo == 'pretty'):
            #     ru.print_struct(dict(hdr.items()))

            elif (echo == 'HSort'):
                for i in sorted(hdr.tostring(sep='\n').splitlines()):
                    if ((i[0:3] != 'END') and (i[0] != ' ')):
                        print (i)

            elif ((echo != False) and (echo != None)):
                try:
                    j = hdr[echo]
                    print ('{} {} = {}'.format(name, echo, hdr[echo]))

                except:
                    print ('{} Keyword {} not found'.format(name, echo))

    except:
        hdr = None
        print ('Failed to open {}'.format(name))
            
    return hdr
               
def write_fits_file (name=None, hdr=None, data=None):
    """\
    Write out a 2D fits file.
    """
    retval = 0
    try:
        fits.writeto(name, data=data, header=hdr)

    except OSError as e:
        retval = -1
        print ('Error: {}'.format(e))

    return retval

def extract_subimage (indat, naxlims=[], isrgb=False, echo=False):
    """\
    Extract a subset of an image cube (either 2 or 3-D)
    Full sub-cube for 3-D is not yet implemented.
    The special case where NAX3 = 3 can be re-ordered to display
    as an RGB image.

    indat == input data cube (2D or 3D)
    naxlims == x,y (, z)  trim limits
    isrgb == true/false if have 3 plane cube, reorder as RGB image
    """

    # Compute input image data dimensions and shape.
    inp_ndim  = len(np.shape(indat))
    inp_shape = np.shape(indat)
    if (echo == True):
        print ('Input Data   Ndim={}, shape={}'.format(inp_ndim, inp_shape))

    # Check for RGB flag
    rgb_flag = isrgb
    if ((inp_ndim != 3) or (inp_shape[0] != 3)):
        rgb_flag = False

    # Check for valid dimensions
    if ((inp_ndim > 3) or (inp_ndim < 1)):
        print ('Input Data invalid number of dimensions {}'.format(inp_ndim))
        return indat, rgb_flag, inp_ndim, inp_shape

    # must have min,max in each of at least two dims
    roi_nargs = len(naxlims)
    if (roi_nargs == 4):
        # 2D image
        naxXmin=np.min(naxlims[0:2])
        naxXmax=np.max(naxlims[0:2])
        naxYmin=np.min(naxlims[2:4])
        naxYmax=np.max(naxlims[2:4])
        naxZmin=0
        naxZmax=1

    elif (roi_nargs == 6):
        # 3D image cube
        naxXmin=np.min(naxlims[0:2])
        naxXmax=np.max(naxlims[0:2])
        naxYmin=np.min(naxlims[2:4])
        naxYmax=np.max(naxlims[2:4])
        naxZmin=np.min(naxlims[4:6])
        naxZmax=np.max(naxlims[4:6])

    else:
        # make sure the values are assigned
        naxXmin=0
        naxXmax=1
        naxYmin=0
        naxYmax=1
        naxZmin=0
        naxZmax=1

    if (naxZmin == naxZmax):
        naxZmax = naxZmax + 1

    # Handle re-ordering planes for RGB if appropriate, or
    # copy over 1st plane of 3-D cube, or just copy through w/o change
    if (naxlims == []):
        if (inp_ndim == 3):
            if ((inp_shape[0] == 3) and (rgb_flag == True)):
                # If input is NAXIS2=3, assume (for now) that it is RGB
                # and permute the axes to y,x,z from z,y,x for auto display
                # by imshow
                dat = np.swapaxes(np.swapaxes(indat[:,:,:],0,1),  1, 2)
        
            else:
                # select given range in Z (will reset later to be whole cube)
                # dat = indat[naxZmin:naxZmax]
                dat = indat

        else:
            dat = indat


    # Handle trimming to ROI and re-ordering planes for RGB if 
    # appropriate.  If 3-D but not RGB, just trim and copy the sub-cube
    else:
        # must have min,max in each of two dims
        if ((roi_nargs == 4) or (roi_nargs == 6)):

            if (inp_ndim == 2):
                dat = indat[naxYmin:naxYmax, naxXmin:naxXmax]

            elif (inp_ndim == 3):
                if ((inp_shape[0] == 3) and (rgb_flag == True)):
                    dat = np.swapaxes(np.swapaxes(
                            indat[:,naxYmin:naxYmax, naxXmin:naxXmax],0,1), 
                                      1, 2)

                else:
                    dat = indat[naxZmin:naxZmax, naxYmin:naxYmax, 
                                naxXmin:naxXmax]

        else:
            dat = indat

    img_ndim  = len(np.shape(dat))
    img_shape = np.shape(dat)
    if (echo == True):
        print ('Extracted Data Ndim={}, shape={}'.format(img_ndim, img_shape))

    return dat, rgb_flag, img_ndim, img_shape

def compute_xy_marginals (dat):
    """\
    Compute x, y marginal sums for a 2-D array.
    Can handle 3-D if array 3-D, sums along axes 0 and 1.
    returns x, y marginal vectors, vector lengths and index arrays.
    """

    xmarg = np.average(dat, axis=0)
    xlen  = len(xmarg)
    xidx  = np.arange(xlen)
    
    ymarg = np.average(dat, axis=1)
    ylen  = len(ymarg)
    yidx  = np.arange(ylen)
    
    return xmarg, ymarg, xlen, ylen, xidx, yidx
