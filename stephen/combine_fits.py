#!/usr/bin/env python3

#------------------------------------------------------------------------
__doc__="""\
combine_fits.py - combine multiple fits images into one
Simple FITS image load, combine (average, mediane etc) store.

Put this together to deal with TiMo CMOS camera data that appears
to have shifted 8 or 12 bit data to fill 16 bit unsigned short data
space. 

img_bitshift() - allows bit shifting image data
combine_imgs() - simple image combination (mean, median etc)
do_ixion_timo_10to1 () - specific image combination for Ixion 20201013 data

2021 Mar 09 - sel@ell - some clean up
2021 Mar 02 - sel@ell - added min,max,minmax clipping
2020 Dec 27 - sel@ell - shift to reduc_fits_util, and add c_main() driver
"""
__intro__="""\
combine_fits.py - combine multiple fits images into one
Simple FITS image load, combine (average, median, etc) store.
- average takes three optional arguments for weighting, mean, median and sum
- quantile takes one argument, floating point value between 0 and 1.  
  Default is 0.5

Includes an option bit shift the data before combination.
Shift all the data in an array left or right by nbits.
 if nbits < 0, shift right, ie the equivalent of dividing by 2^nbits
 if nbits > 0, shift left, ie the equivalent of multiplying by 2^nbits

If given an image N-cube, can squash in the axis=0 dimension to return
an (N-1)-dim cube (e.g. 2D from 3D).
"""
__author__="S. Levine"
__date__="2021 Mar 09"

#------------------------------------------------------------------------
# import glob
# import time

# Command line arg parsing
import argparse

import datetime as dt

import numpy as np

# sel reduction utility routines
import reduc_utils as ru
import reduc_fits_utils as rf

#------------------------------------------------------------------------

def img_bitshift (dat, nbits=0):
    """\
    Shift all the data in an array left or right by nbits.
    if nbits < 0, shift right, ie the equivalent of dividing by 2^nbits
    if nbits > 0, shift left, ie the equivalent of multiplying by 2^nbits
    """

    if ((nbits == 0) or (type(nbits) != int)):
        return dat

    elif (nbits < 0):
        shdat = np.right_shift (dat, abs(nbits))

    elif (nbits > 0):
        shdat = np.left_shift (dat, abs(nbits))

    return shdat

def cube_normalize (cube2norm, normalize='none'):
    """\
    Compute image cube normalization value.
    """
    normval = 1.0

    if (normalize != 'none'):
        if (normalize == 'mean'):
            normval = np.mean (cube2norm)
        elif (method_arg == 'median'):
            normval = np.median (cube2norm)
        elif (method_arg == 'sum'):
            normval = np.sum (cube2norm)

    return normval

def cube_clip (cube2clip, clip='none', clip_arg=[0]):
    """\
    Clip image cube using min, max or minmax clipping.
    """
    if (clip == 'none'):
        return cube2clip, str(0)

    # sort in the stack direction so that clipping is just clipping
    #  the top and/or bottom plane(s)
    cube2clip.sort(axis=0)

    # make sure that clip_args are not all zero
    calen = len(clip_arg)

    if ((calen == 1) and (clip_arg == [0])):
        return cube2clip, str(0)

    elif ((calen == 2) and (clip_arg == [0,0])):
        return cube2clip, str(0)

    else:
        if (clip == 'min'):
            cdat = cube2clip[clip_arg[0]:]
            carg_str = str(clip_arg[0])
        elif (clip == 'max'):
            cdat = cube2clip[0:-clip_arg[0]]
            carg_str = str(clip_arg[0])
        elif (clip == 'minmax'):
            if (calen == 1):
                cdat = cube2clip[clip_arg[0]:-clip_arg[0]]
                carg_str = str(clip_arg[0])
            elif (calen == 2):
                cdat = cube2clip[clip_arg[0]:-clip_arg[1]]
                carg_str = str(clip_arg[0]) + ',' + \
                    str(clip_arg[1])

    return cdat, carg_str

def combine_imgs (names=None, method='median', method_arg=None, 
                  normalize='none',
                  clip='none', clip_arg=None, bshift=0,
                  reduce_dim=False, unitmean=False):
    """\
    Combine a stack of identical format images,
    kind of like a simplified iraf>imcombine.
    names == list of file names, can include regex syntax.
    method == combination method.  Options include:
      'average', 'mean', 'median', 'quantile', 'sum'
    clip == clip the input cube for outliers. Number of outliers set 
      in clip_arg. Options = min, max, minmax
    bshift == # of bits to shift input images.
    reduce_dim == take and N-dimensional cube and squash in the axis=0
      dimension, returning an (N-1)-dimensional cube.
    unitmean == rescale final image to have unit mean
    """

    if (names == None):
        ifiles = ru.expand_list_files2 ()
    else:
        ifiles = ru.expand_list_files2 (ipfiles=names)

    nfiles = 0

    # print ('ifiles = {}'.format(ifiles))

    # Read in all the files and stack the data units in the next 
    # (probably 3rd) dimension in a data cube.  All combination options
    # then operate by pixel along that dimension, reducing to a final
    # output of the same dimensionality as the input.

    for i in ifiles:
        if (nfiles == 0):
            basehdr, basedat = rf.load_fits_file (name=i)
            # pop up on error
            if (basehdr == None):
                return basehdr, basedat

            if (bshift != 0):
                basedat = img_bitshift (basedat, bshift)

            # Normalize by first frame mean,median or sum before stacking
            # base0norm is the normalizing factor for the first frame
            # norms for the others will be divide by their norm and multplied
            # by base0norm
            base0norm = cube_normalize (basedat, normalize=normalize)

        else:
            lasthdr, lastdat = rf.load_fits_file (name=i)
            # pop up on error
            if (lasthdr == None):
                return lasthdr, lastdat

            if (bshift != 0):
                lastdat = img_bitshift (lastdat, bshift)

            # Normalize relative to the first frame
            baseNnorm = cube_normalize (lastdat, normalize=normalize)
            if (baseNnorm != 0.0):
                lastdat =  (base0norm / baseNnorm) * lastdat
            else:
                print ('WARNING: Image plane norm is 0.0, not renormalized')

            # Stack latest data array onto the accumulating basedata array
            if (nfiles == 1):
                basedat = np.append([basedat], [lastdat], axis=0)
            else:
                basedat = np.append(basedat, [lastdat], axis=0)

        # Add history keys to header
        try:
            bddate=basehdr['DATE-OBS']
        except:
            try:
                bddate=basehdr['DATE']
            except:
                bddate='UNKNOWN'

        basehdr.set('IMCD{:04d}'.format (nfiles), 
                    value=bddate,
                    comment='Original Img Date-Time')

        basehdr.set('IMC_{:04d}'.format (nfiles), 
                    value=i, comment='File name')

        print ('Loaded file {}'.format(i))

        nfiles += 1

    # add stuff at end of fits header about the combination
    # in preparation for the construction of the output image
    if (bshift != 0):
        basehdr['IM_BSHFT'] = (bshift, 'Input data bitshift')

    basehdr['IMC_NFIL'] = (nfiles, 'Number of files combined')
    basehdr['IMC_MTHD'] = (method, 'Combination method')
    if (method_arg != None):
        basehdr['IMC_MARG'] = (method_arg, 'Method arg(s)')

    # Check shape of basedat
    bd_shape = np.shape(basedat)
    bd_ndim = len(bd_shape)
    # print (bd_ndim, bd_shape)

    # Return None if no images found
    if (nfiles == 0):
        return None, None

    # Return unmodified image if only one submitted, and
    # if # of dimensions is < 3 or reduce_dim == False
    elif ((nfiles == 1) and ((reduce_dim == False) or (bd_ndim < 3))):
        return basehdr, basedat

    elif ((nfiles == 1) and ((reduce_dim == True) or (bd_ndim >= 3))):
        basehdr.set('IMCF{:04d}'.format (nfiles-1),
                    value=bd_shape[0], comment='Frames combined')

    # If clipping is selected, sort the cube and clip
    if (clip != 'none'):
        cdat, carg_str = cube_clip(basedat, clip=clip, clip_arg=clip_arg)

        print (np.shape(basedat))
        basedat = cdat
        print (np.shape(basedat))
        basehdr['IMC_CLIP'] = (clip, 'Clipping Method')
        basehdr['IMC_CARG'] = (carg_str, 'Clipping Argument(s)')
            
    # Combine the images - compress the 3d cube to 2d.
    #  2d images were stacked along axis=0
    if (method == 'average'):
        # optional weighted average
        #  weighting options: 
        #    method_arg=None -> None - means equal weight
        #              ='mean'   -> weight[i] = np.mean(basedat[i])
        #              ='median' -> weight[i] = np.median(basedat[i])
        #              ='sum'   -> weight[i] = np.sum(basedat[i])

        if (method_arg == None):
            wgts = None
        elif (method_arg == 'mean'):
            wgts = np.mean (basedat, axis=(1,2))
        elif (method_arg == 'median'):
            wgts = np.median (basedat, axis=(1,2))
        elif (method_arg == 'sum'):
            wgts = np.sum (basedat, axis=(1,2))
                
        retdat = np.average (basedat, weights=wgts, axis=0)

    elif (method == 'max'):
        # maximum value
        retdat = np.max (basedat, axis=0)

    elif (method == 'mean'):
        # arithmetic mean
        retdat = np.mean (basedat, axis=0)

    elif (method == 'median'):
        # median
        retdat = np.median (basedat, axis=0)
        
    elif (method == 'min'):
        # minimum value
        retdat = np.min (basedat, axis=0)

    elif (method == 'quantile'):
        # q-th quantile
        #  method_arg is the q'th quartile 0 <= q <= 1
        if (method_arg == None):
            q = 0.5
        elif (type(method_arg) == float):
            q = method_arg
        else:
            q = 0.5

        retdat = np.quantile (basedat, q, axis=0)
        
    elif (method == 'std'):
        # std deviation (rms)
        retdat = np.std (basedat, axis=0)

    elif (method == 'sum'):
        # sum
        #  Warning, the default value format will be as the input
        #  within limits - e.g. if input is short, then get integer
        #  or some sort.
        #  Need to decide on how to promote to floating point.
        retdat = np.sum (basedat, axis=0)

    elif (method == 'var'):
        # variance
        retdat = np.var (basedat, axis=0)

    # rescale to unit mean
    if (unitmean == True):
        rmean = np.mean(retdat)
        if (rmean != 0.0):
            retdat = retdat / rmean
            basehdr['IMC_UNIT'] = (rmean, 'Rescaled to unit mean')
        else:
            pass

    return basehdr, retdat

def parse_cmd_line (iargv):
    """
    Read and parse the input command line.
    """

    # --- Default inputs ---

    # Prep the line for input
    argc = len(iargv)

    # Parse command line input
    # - using argparse

    cli = argparse.ArgumentParser(prog='combine_fits.py', 
                                  description=__intro__,
                                  epilog='version: '+__date__)
    
    fits_input0 = './*.fits'
    cli.add_argument ('fitsfiles', nargs='?', default=fits_input0,
                      help='Required Input Filename - Fits files. ' + 
                      'Default: ' + fits_input0)

    def_marg= None
    cli.add_argument ('-a', '--marg', default=def_marg,
                      help='Argument for method. ' + 
                      'Default: ' + str(def_marg))

    def_clip='none'
    clip_options = ['none', 'minmax', 'max', 'min']
    cli.add_argument ('-c', '--clip', type=str, default=def_clip,
                      choices=clip_options,
                      help='Clipping options during combination. ' + 
                      'Default: ' + def_clip)

    def_carg='0'
    cli.add_argument ('-d', '--carg', default=def_carg,
                      help='Argument for clipping. ' +
                      'Number of points to clip. ' + 
                      'Default: ' + str(def_carg))

    def_method = 'median'
    method_options = ['average', 'max', 'min', 
                      'mean', 'median', 'quantile', 
                      'rms', 'std', 'sum', 'var']
    cli.add_argument ('-m', '--method', type=str, default=def_method,
                      choices=method_options,
                      help='Combination Method Choices. ' + 
                      'Default: ' + def_method)

    def_norm='none'
    norm_options = ['none', 'mean', 'median', 'sum']
    cli.add_argument ('-n', '--norm', type=str, default=def_norm,
                      choices=norm_options,
                      help='Normalizing options during combination. ' + 
                      'Default: ' + def_norm)

    def_output = 'test.fits'
    cli.add_argument ('-o', '--output', type=str, default=def_output,
                      help='Output file name. ' + 
                      'Default: ' + def_output)

    reduce = False
    cli.add_argument ('-r', '--reduce', action="store_true",
                      help='Reduce cube by 1 dimension by combining in ' +
                      'axis=0 dimension.')

    def_bsh = 0
    cli.add_argument ('-s', '--bshift', type=int, default=def_bsh,
                      help='Number of bits to shift (+/-) ' + 
                      'Default: ' + str(def_bsh))

    unitmean = False
    cli.add_argument ('-u', '--unit', action="store_true",
                      help='Rescale output image to have unit mean.')

    verbose = False
    cli.add_argument ('-v', '--verbose', action="store_true",
                      help='Verbose output.')

    # Parse the input
    args = cli.parse_args(args=iargv[1:])
    
    # Check for verbose request, and if True echo inputs
    if (args.verbose):
        verbose=True

    if (verbose == True):
        print ('argc = {} {}'.format(argc,iargv))

    fits_input = args.fitsfiles
    if (verbose == True):
        print ('fits_input = {}'.format(fits_input))

    method = args.method
    if (method == 'rms'):
        method = 'std'
    if (verbose == True):
        print ('method = {}'.format(method))

    marg = args.marg
    if (verbose == True):
        print ('method args = {}'.format(marg))

    norm = args.norm
    if (verbose == True):
        print ('normalize = {}'.format(norm))

    clip = args.clip
    if (verbose == True):
        print ('clipping = {}'.format(clip))

    carg = [int(a) for a in args.carg.replace('  ','').split(',')]
    if (verbose == True):
        print ('clipping args = {}'.format(carg))

    bshift = args.bshift
    if (verbose == True):
        print ('bit shift = {}'.format(bshift))

    reduce = args.reduce
    if (verbose == True):
        if (reduce == True):
            print ('reduce dim by 1 == True')
        else:
            print ('reduce dim by 1 == False')

    out_name = args.output
    if (verbose == True):
        print ('output_name = {}'.format(out_name))

    if (args.unit):
        unitmean=True

    return fits_input, method, marg, norm, clip, carg, bshift, \
        out_name, reduce, unitmean, verbose

#------------------------------------------------------------------------
def combine_fits_main (iargv):
    """
    Run simple fits image combination.
    """

    # Parse the command line
    fits_input, method, marg, norm, clip, carg, bshift, out_name, reduce, \
        unitmean, verbose = parse_cmd_line (iargv)

    # Combine
    h, d = combine_imgs (names=fits_input, method=method, method_arg=marg,
                         normalize=norm, clip=clip, clip_arg=carg,
                         bshift=bshift, reduce_dim=reduce, unitmean=unitmean)

    if (h == None):
        # Error in fits read somewhere
        return

    # Write out new file
    rf.write_fits_file (name=out_name, hdr=h, data=d)

    return

#------------------------------------------------------------------------
def do_ixion_timo_10to1 ():
    """\
    Single, specific use case - Ixion 20201013 occultation, TiMo data.
    median together timo data in sets of 10 to get enough signal
    to compute centroids for aperture setup.
    """

    _starttime = dt.datetime.now()

    set_counter = range(100)

    for c in set_counter:
        img_names = '20201013.0{:02d}?.fits'.format(c)
        out_name =  '20201013m.0{:02d}0.fits'.format(c)

        print ('{}'.format(img_names))

        h, d = combine_imgs (names=img_names, bshift=-4)

        rf.write_fits_file (name=out_name, hdr=h, data=d)

    _endtime = dt.datetime.now()

    print ('# Took {} to run'.format(_endtime - _starttime))

    return

#------------------------------------------------------------------------
# Execute as a script

if __name__ == '__main__':
    import sys
    
    argv = sys.argv
    combine_fits_main (argv)
    
    exit()

