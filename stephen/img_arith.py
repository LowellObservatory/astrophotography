#!/usr/bin/env python3
__doc__="""\
img_arith.py - extract a portion of a or several 2-D image or 3-D
image cube and perform basic arithmetic operations on it(them).

Can be run from the command line, and img_stats_main() can also be
imported and used as a function.

To use as a function:
  import img_arith as imgar
  hdr, dat = imgar.img_arith_main(iargv)
where iargv is a list in the format of the command line input.
You can get an example by running this from the command line with
the -v (verbose) option on and looking for the first output line that
starts with "argc = ..." The list given after the argument count is the
format of the input iargv.

TBD: At some point I would be inclined to set up alternate args to 
img_arith_main() in place of iargv that simplifies calling as a function.

Updates:
2021 Feb 24 - fixed issue in constructing output name from root for group
2021 Jan 30 - added type promotion in simple_arithmetic()
2021 Jan 29 - update to make it easier to call img_arith_main() as a function
2021 Jan 25 - initial version
"""

__intro__= """\
Image manipulation tool to extract a portion of a or several 2-D image
or 3-D image cube and perform basic arithmetic operations on it(them).

This has a somewhat unusual feature. If img1 is a 2D image of the same
dimensions as the x,y dimensions of an img0 3D image cube, then the arithmetic
operation will be applied plane by plane in the z-direction to img0.  This
means if you have  2D bias (for example), you could directly subtract it
from each frame in a 3D cube without slicing the cube.  The output will
still be a 3D cube.

op == operator: +, -, x (or *), /, =

image op value,
image op image,
image_list op image,
image_list op image_list, image lists must be the same length
image_list op value,

-b [Xmin Xmax Ymin Ymax]
-B [Xmin Xmax Ymin Ymax Zmin Zmax]
-o [output image or image root]

"""
__author__="Stephen Levine"
__date__="2021 Feb 24"

#------------------------------------------------------------------------

# Command line arg parsing
import argparse

import datetime as dt

# OS routines
import os

# Numpy
import numpy as np

# Scipy
from scipy import stats as scst

# SEL reduction utilities
import reduc_utils as ru
import reduc_fits_utils as rf

#------------------------------------------------------------------------

def parse_cmd_line (iargv):
    """
    Parse the input command line and return run time variables.
    """

    # --- Default inputs ---

    # Prep the line for input
    argc = len(iargv)

    # Parse command line input
    # - using argparse

    cli = argparse.ArgumentParser(prog='img_arith.py', 
                                  description=__intro__,
                                  epilog='version: '+__date__)
    
    cli.add_argument ('arithin', nargs=3,
                      help='Required Input: Image(s)1 Op Image(s)orValue2 ')

    def_xylims3 = []
    str_def_xylims3 = '[min:max, min:max, min:max]'
    cli.add_argument ('-B', '--Bounds', type=int, nargs=6, default=def_xylims3,
                      help='Image bounds (in pixels).  ' +
                      'NB: Bounds are given here as ZERO based, ' + 
                      'BUT FITS files use ONE based counting. ' +
                      'Default: ' + str(str_def_xylims3))


    def_xylims = []
    str_def_xylims = '[min:max, min:max]'
    cli.add_argument ('-b', '--bounds', type=int, nargs=4, default=def_xylims,
                      help='Image bounds (in pixels). ' + 
                      'NB: Bounds are given here as ZERO based, ' + 
                      'BUT FITS files use ONE based counting. ' +
                      'Default: ' + str(str_def_xylims))

    def_output = ''
    cli.add_argument ('-o', '--output', type=str, default=def_output,
                      help='Output file name. No value will take image1 ' +
                      'root and add _arith. Anything else will be ' +
                      'interpretted as the (root) name for an output file. ' +
                      'Default: ' + def_output)

    simul = False
    cli.add_argument ('-s', '--simul', action="store_true",
                      help='Simulate action, but do not write output.')

    verbose = False
    cli.add_argument ('-v', '--verbose', action="store_true",
                      help='Verbose output.')

    # Parse the input
    args = cli.parse_args(args=iargv[1:])

    # Check for verbose request, and if True echo inputs
    if (args.verbose):
        verbose=True

    # Echo calling name
    if (verbose == True):
        print ('argc = {} {}'.format(argc,iargv))

    # And extract the various inputs into internal variables
    arith_input = args.arithin
    lai = len(arith_input)
    if ((verbose == True) or (lai != 3)):
        print ('arith_input = {}'.format(arith_input))
        if (lai != 3):
            print ('Need min of 3 inputs: Img1 Op Img/Val2')
            exit ()

    # Extract operations args and check
    # 0 == operand0 = image or images
    imgs0 = arith_input[0]
    li1  = len(imgs0)

    # 1 == operator
    oper  = arith_input[1]

    # 2 == operand1 = image, images or scalar, scalars (?)
    try:
        iv1   = int(arith_input[2])
    except:
        try:
            iv1   = float(arith_input[2])
        except:
            iv1   = arith_input[2]

    if ((type(iv1) is int) or (type(iv1) is float)):
        liv1 = 1

    elif (type(iv1) is str):
        liv1 = len(iv1)

    else:
        print ('Invalid image/value2 input')
        exit ()

    if ((oper == '+') or (oper == '-') or
        (oper == '*') or (oper == '/') or
        (oper == '=') or (oper == 'x')):
        if (oper == 'x'):
            oper = '*'

    else:
        print ('Invalid operation. Must be one of +,-, x (or *),/,=')
        exit ()

    if (verbose == True):
        print ('(Img0 = {}) (Op = {}) (Img1/Val1 = {})'.\
                   format (imgs0, oper, iv1))

    # Check for 2D limits first
    naxlims = args.bounds

    # Then check for 3D limits if no 2D limits
    if (naxlims == []):
        naxlims = args.Bounds
        if (naxlims != []):
            if (naxlims[4] == naxlims[5]):
                naxlims[5] += 1

    # check limits and increment upper limit if equal to lower limit
    if (naxlims != []):
        if (naxlims[0] == naxlims[1]):
                naxlims[1] += 1
        if (naxlims[2] == naxlims[3]):
                naxlims[3] += 1

    if (verbose == True):
        print ('x(min,max), y(min,max)[, z(min,max)] bounds = {}'.\
                   format(naxlims))

    outfile = args.output
    if (verbose == True):
        print ('output file = {}'.format(outfile))

    if (args.simul):
        simul = True
        if (verbose == True):
            print ('Simulate action, but do not write output')

    return  imgs0, oper, iv1, naxlims, outfile, simul, verbose

def open_and_extract(pfile, naxlims, verbose=False):
    """\
    Open a fits file and extract a subset.
    """
    hdr, dat = rf.load_fits_file (pfile,
                                  echo=('Short' if (verbose == True) 
                                        else False))
    if (hdr == None):
        # Failed to load for some reason, pass back null
        return hdr, None, 1, (1)

    # Extract a subset of an image cube (either 2 or 3-D)
    # Set rgb to false for this application
    cdat, rgb_flag, img_ndim, img_shape = \
        rf.extract_subimage (dat, naxlims, isrgb=False)

    return hdr, cdat, img_ndim, img_shape

def simple_arithmetic (inp0, oper, inp1, echo=False):
    """\
    Perform simple arithmetic +,-,*,/ on input operands inp0 and inp1.
    Tries to somewhat smart about how and when to promote the datatype
    for the requested operation
    """

    # Check input data types
    i0 = inp0.flatten()[0]
    if ((type(inp1) is int) or (type(inp1) is float)):
        i1 = inp1
    else:
        i1 = inp1.flatten()[0]

    ms0 = np.min_scalar_type(i0)
    ms1 = np.min_scalar_type(i1)
    if (echo == True):
        print ('i0, i1 type = {} {}'.format(ms0, ms1))

    mst_type = np.promote_types(ms0,ms1)
    if (echo == True):
        print ('mst_type = {}'.format(mst_type))

    # int types or floats
    if ((mst_type == np.int8) or
        (mst_type == np.int16) or
        (mst_type == np.int32) or
        (mst_type == np.int64) or
        (mst_type == np.uint8) or
        (mst_type == np.uint16) or
        (mst_type == np.uint32) or
        (mst_type == np.uint64)):
        morf = 'int'
    else:
        morf = 'float'

    # get input min and max range
    mn0 = np.min(inp0)
    mx0 = np.max(inp0)
    mn1 = np.min(inp1)
    mx1 = np.max(inp1)

    op_type = mst_type

    if (oper == '+'):
        # Check ranges
        if (morf == 'int'):
            omx = mx0.astype(np.int64) + mx1.astype(np.int64)
            omn = mn0.astype(np.int64) + mn1.astype(np.int64)
        else:
            omx = mx0.astype(np.float64) + mx1.astype(np.float64)
            omn = mn0.astype(np.float64) + mn1.astype(np.float64)
        op_type = np.promote_types(np.min_scalar_type(omn),
                                   np.min_scalar_type(omx))
        if (op_type == np.float16):
            # Fits writer won't recognize float16
            op_type = np.dtype(np.float32)

        if (echo == True):
            print ('omn, omx = {} {} op_type + = {}'.format(omn,omx,op_type))

        inp2 = np.add(inp0, inp1, dtype=op_type)

    elif (oper == '-'):
        # Check ranges
        if (morf == 'int'):
            omx = mx0.astype(np.int64) - mn1.astype(np.int64)
            omn = mn0.astype(np.int64) - mx1.astype(np.int64)
        else:
            omx = mx0.astype(np.float64) - mn1.astype(np.float64)
            omn = mn0.astype(np.float64) - mx1.astype(np.float64)
        op_type = np.promote_types(np.min_scalar_type(omn),
                                   np.min_scalar_type(omx))
        if (op_type == np.float16):
            # Fits writer won't recognize float16
            op_type = np.dtype(np.float32)

        if (echo == True):
            print ('omn, omx = {} {} op_type - = {}'.format(omn,omx,op_type))

        inp2 = np.subtract(inp0, inp1, dtype=op_type)

        # inp2 = np.subtract(inp0.astype(np.int16), inp1.astype(np.int16))
        # print ('op_type = {}, min,max = {} {}'.\
        #            format(op_type, np.min(inp2), np.max(inp2)))

    elif (oper == '*'):
        # Check ranges
        if (morf == 'int'):
            omx = mx0.astype(np.int64) * mx1.astype(np.int64)
            omn = mn0.astype(np.int64) * mn1.astype(np.int64)
        else:
            omx = mx0.astype(np.float64) * mx1.astype(np.float64)
            omn = mn0.astype(np.float64) * mn1.astype(np.float64)
        op_type = np.promote_types(np.min_scalar_type(omn),
                                   np.min_scalar_type(omx))
        if (op_type == np.float16):
            # Fits writer won't recognize float16
            op_type = np.dtype(np.float32)

        if (echo == True):
            print ('omn, omx = {} {} op_type * = {}'.format(omn,omx,op_type))

        inp2 = np.multiply(inp0, inp1, dtype=op_type)

    elif (oper == '/'):
        # Check ranges
        if (morf == 'int'):
            omx = mx0.astype(np.int64) / mn1.astype(np.int64)
            omn = mn0.astype(np.int64) / mx1.astype(np.int64)
        else:
            omx = mx0.astype(np.float64) / mn1.astype(np.float64)
            omn = mn0.astype(np.float64) / mx1.astype(np.float64)
        op_type = np.promote_types(np.min_scalar_type(omn),
                                   np.min_scalar_type(omx))
        if (op_type == np.float16):
            # Fits writer won't recognize float16
            op_type = np.dtype(np.float32)

        if (echo == True):
            print ('omn, omx = {} {} op_type / = {}'.format(omn,omx,op_type))

        inp2 = np.divide(inp0, inp1, dtype=op_type)

    elif (oper == '='):
        inp2 = np.full(np.shape(inp0), inp1, dtype=op_type)

    return inp2
    
#------------------------------------------------------------------------
def img_arith_main (iargv):
    """
    Image arithmetic on 2D or 3D arrays.
    """

    # Parse the command line
    imgs0, oper, iv1, naxlims, outfile, simul, verbose = \
        parse_cmd_line (iargv)

    # Check and parse outfile to figure out how to name output(s)
    # nimg0  == 1 -> outfile == name as is
    # nimg0 > 1 -> n_out == nimg0 -> outfile == array of names as is
    #            n_out == 1 -> is root -> need to figure post-fix, and seq nums

    # Get directory, path separator, and base filename(s)
    ofl_dir    = os.path.dirname (outfile)
    ofl_sep    = os.path.sep
    ofl_base   = os.path.basename (outfile)
    # Check if given multiple, comma separated names
    ofl_mult_b = ofl_base.replace(' ','').split(',')
    num_ofl    = len(ofl_mult_b)

    # Get list of image0 files to work on
    f0_files = ru.expand_list_files2(ipfiles=imgs0, echo=verbose)
    num0_files = len(f0_files)

    # Handle second operand
    if (type(iv1) is str):
        # Get list of image1 files to work on
        f1_files = ru.expand_list_files2(ipfiles=iv1, echo=verbose)
        num1_files = len(f1_files)

    elif ((type(iv1) is float) or (type(iv1) is int)):
        # For scalar, set img dim and shape to unit
        num1_files = 0
        img_ndim1  = 1
        img_shape1 = (1)

    # Confirm that we have a valid match of inputs
    if ((num0_files == num1_files) or
        (num0_files > 0 and num1_files == 0) or
        (num0_files > 0 and num1_files == 1)):
        pass
    else:
        print ('Invalid request - mismatch between allowed inputs')
        print ('  num0_files, num1_files = {} {}'.format(num0_files, num1_files))
        exit(-1)

    if ((num_ofl != 1) and (num_ofl != num0_files)):
        print ('Invalid request - mismatch between number of inputs and outputs')
        print ('  num0_files, num_ofl = {} {}'.format(num0_files, num_ofl))
        exit(-1)
        

    # Loop through files, open, extract roi and compute stats
    for f0idx in range(num0_files):
        # open img0 fits file
        pf0 = f0_files[f0idx]
        hdr0, cdat0, img_ndim0, img_shape0 = open_and_extract(pf0, naxlims,
                                                              verbose=verbose)
        if (hdr0 == None):
            # Failed to load for some reason, skip
            continue

        # If there is 1 operand1 image, only open it on the first pass
        # else if the # of operand1 images == # of operand0 images,
        # open corresponding image on each pass
        if ((num1_files == num0_files) or
            ((num1_files == 1) and (f0idx == 0))):

            # open img1 fits file
            pf1 = f1_files[f0idx]
            hdr1, cdat1, img_ndim1, img_shape1 = \
                open_and_extract(pf1, naxlims, verbose=verbose)

            if (hdr1 == None):
                # Failed to load for some reason, skip
                continue

        # Check dimensional compatibility
        if (num1_files > 0):
            # Check to see if can do (Ndim) op (N-1)dim arithmetic
            if ((img_ndim0 == 3) and (img_ndim1 == 2)):
                if (img_shape0[1:3] == img_shape1):
                    pass

                else:
                    print ('Images of incompatible dimensions. Skipping')
                    print ('  Img0,1 shapes = {}, {}'.format(img_shape0, 
                                                           img_shape1))
                    continue

            # Check compatible shapes
            elif (img_shape1 != img_shape0):
                print ('Images of incompatible dimensions. Skipping')
                print ('  Img0,1 shapes = {}, {}'.format(img_shape0, 
                                                         img_shape1))
                continue

        # N-dim image Op Scale
        if (num0_files > 0 and num1_files == 0):
            cdat2 = simple_arithmetic (cdat0, oper, iv1)
                
        # N-dim image Op (N-1)-dim image
        elif (((img_ndim0 == 3) and (img_ndim1 == 2)) and
            (img_shape0[1:3] == img_shape1)):
 #           cdat2 = simple_arithmetic (cdat0, '=', 0)
            for zidx in range(img_shape0[0]):
#                cdat2[zidx] = simple_arithmetic (cdat0[zidx], oper, cdat1)
                if (zidx == 0):
                    cdat2 = simple_arithmetic (cdat0[zidx], oper, cdat1)
                elif (zidx == 1):
                    cdat2 = np.append([cdat2],[simple_arithmetic (cdat0[zidx], oper, cdat1)],
                                      axis=0)
                else:
                    cdat2 = np.append(cdat2,[simple_arithmetic (cdat0[zidx], oper, cdat1)],
                                      axis=0)

                if (verbose == True):
                    print ('SubImg {} mean = {}'.format(zidx, 
                                                        np.mean(cdat2[zidx])))

        # N-dim image Op N-dim image
        elif ((num0_files == num1_files) or 
              (num0_files > 0 and num1_files == 1)):
            cdat2 = simple_arithmetic (cdat0, oper, cdat1)

        # Check output - remove once happy with this
        if (verbose == True):
            print ('Img0 min,max = {} {}'.format(np.min(cdat0), np.max(cdat0)))
            if (num1_files != 0):
                print ('Img1 min,max = {} {}'.format(np.min(cdat1), np.max(cdat1)))
            print ('Img2 min,max = {} {}'.format(np.min(cdat2), np.max(cdat2)))
            print ('Img mean = {}'.format(np.mean(cdat2)))

        # If ROI axis limits not set, set to existing image limits
        if (naxlims == []):
            if (img_ndim0 == 2):
                naxlims = [0, img_shape0[1],
                           0, img_shape0[0]]
            elif (img_ndim0 == 3):
                naxlims = [0, img_shape0[2], 
                           0, img_shape0[1], 
                           0, img_shape0[0]]
            else:
                print ('Error: unable to set naxlims')
                exit()

        # Construct string showing original file
        # and bounds, in FITS base ONE values
        if (img_ndim0 == 2):
            region = '[{}:{},{}:{}]'.format(naxlims[0]+1, naxlims[1],
                                            naxlims[2]+1, naxlims[3])
        elif (img_ndim0 == 3):
            region = '[{}:{},{}:{},{}:{}]'.format(naxlims[0]+1, naxlims[1],
                                                  naxlims[2]+1, naxlims[3],
                                                  naxlims[4]+1, naxlims[5])
        else:
            region = '{}'.format('')

        hdrval = 'img_arith {} UT:'.\
            format(dt.datetime.utcnow().isoformat(timespec='seconds'))
        hdrval += ' {}{}'.format(pf0, region)
        hdrval += ' {} '.format(oper)

        if (num1_files == 0):
            hdrval += '{}'.format(iv1)
        elif (num1_files > 0):
            hdrval += '{}{}'.format(pf1, region)

        hdr0.add_history(value=hdrval)

        # Write out resultant fits file
        if (simul == True):
            if (verbose == True):
                print ('Simulate == True, output skipped')
        else:
            # Construct output file name
            ofile_name = ''
            if (outfile == ''):
                ofile_name = 'imar_' + pf0

            elif (num0_files == 1):
                ofile_name = os.path.join(ofl_dir, ofl_mult_b[0])

            elif ((num0_files > 1) and (num0_files == num_ofl)):
                ofile_name = os.path.join(ofl_dir, ofl_mult_b[f0idx])

            elif ((num0_files > 1) and (num_ofl == 1)):
                bpf0 = os.path.basename(pf0).split('.')
                # print ('bpf0 = {}'.format(bpf0))

                nbpf0 = len(bpf0)
                if (nbpf0 == 1):
                    nb_addon = bpf0[0]

                elif (nbpf0 > 1):
                    if ((bpf0[-1] == 'fits') or (bpf0[-1] == 'fit')):
                        nb_post = bpf0[-1]
                    else:
                        nb_post = ''

                    # check back from end for first integer, and 
                    # treat that as a sequence number. Ignore whatever
                    # comes before that.  Tack on everything after it as
                    # the post-fix
                    nb_seqn = ''
                    for nbidx in range(nbpf0-2, -1, -1):
                        # print ('bpf0[{}] = {}'.format(nbidx, bpf0[nbidx]))
                        try:
                            seqnum = int(bpf0[nbidx])
                            nb_seqn = bpf0[nbidx]
                            break

                        except:
                            try:
                                dashstr = bpf0[nbidx].split('-')
                                seqnum = int(dashstr[-1])
                                nb_seqn = dashstr[-1]
                                break

                            except:
                                nb_post = bpf0[nbidx] + '.' + nb_post

                    nb_addon = nb_seqn + '.' + nb_post

                ofile_name = os.path.join(ofl_dir, ofl_mult_b[0] +'.'+ 
                                          nb_addon)
            
                # print ('Ofile = {}'.format(ofile_name))

            if (os.path.exists(ofile_name) == True):
                print ('img_arith: File {} exists, skipping'.format(ofile_name))
            else:
                wstat = rf.write_fits_file (ofile_name, hdr=hdr0, data=cdat2)
                print('{} -> {}'.format(hdrval, ofile_name))

    # pass back final HDU header and data blocks if wanted for
    # manipulation by calling code.

    return hdr0, cdat2

#------------------------------------------------------------------------
# Execute as a script

if __name__ == '__main__':
    import sys
    
    argv = sys.argv
    hdr, dat = img_arith_main (argv)

#    print (hdr)
    exit()
