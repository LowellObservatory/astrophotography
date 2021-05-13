#!/usr/bin/env python3
__doc__="""\
img_stats.py - extract a portion of a 2-D image or 3-D image cube and 
  compute statistics.

Can be run from the command line, and img_stats_main() can also be
imported and used as a function.

To use as a function:
  import img_stats as imgst
  stats, st_vals = imgst.img_stats_main(iargv)
where iargv is a list in the format of the command line input.
You can get an example by running this from the command line with
the -v (verbose) option on and looking for the first output line that
starts with "argc = ..." The list given after the argument count is the
format of the input iargv.

TBD: At some point I would be inclined to set up alternate args to 
img_stats_main() in place of iargv that simplifies calling as a function.

Updates:
2021 Mar 09 - moved val_fmt() to reduc_utils.
2021 Jan 29 - updates to make img_stats_main() callable as fcn, returns stats
2021 Jan 17 - initial version
"""

__intro__= """\
Image manipulation tool to extract a portion of a 2-D image or 3-D
image cube and compute statistics.
"""
__author__="Stephen Levine"
__date__="2021 Mar 09"

#------------------------------------------------------------------------

# Command line arg parsing
import argparse

# Numpy
import numpy as np

# Scipy - used for mode computation
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

    fits_input0 = './*.fits'

    # Prep the line for input
    argc = len(iargv)

    # Parse command line input
    # - using argparse

    cli = argparse.ArgumentParser(prog='img_stats.py', 
                                  description=__intro__,
                                  epilog='version: '+__date__)
    
    cli.add_argument ('fitsfiles', nargs='?', default=fits_input0,
                      help='Required Input Filename - Fits files. ' + 
                      'Default: ' + fits_input0)

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
                      help='Output file name. No value, stdio, or screen ' +
                      'will write the output to the screen. Anything else ' +
                      'will be interpretted as the name for an output file. ' +
                      'Default: ' + def_output)

    def_stats = 'num,sum,mean,median,rms'
    cli.add_argument ('-s', '--stats', type=str, default=def_stats,
                      help='Select statistical quantities to compute. ' +
                      'Options include: average, max, min, mean, ' +
                      'median, mode, num, rms, std, sum, var. ' +
                      'Default: ' + def_stats)

    twodframe = False
    cli.add_argument ('-t', '--twodframe', action="store_true",
                      help='For a 3-D cube, compute stats for each 2-D ' +
                      'image frame individually, rather than for the ' +
                      'entire 3-D volume.')

    update = False
    cli.add_argument ('-u', '--update', action="store_true",
                      help='Add stats keywords and update input ' +
                      'fits file header.')

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

    # And extract the various inputs into internal variables
    fits_input = args.fitsfiles
    if (verbose == True):
        print ('fits_input = {}'.format(fits_input))

    naxlims = args.bounds
    if (naxlims == []):
        naxlims = args.Bounds
        if (naxlims != []):
            if (naxlims[4] == naxlims[5]):
                naxlims[5] += 1

    if (verbose == True):
        print ('x(min,max), y(min,max) [, z(min,max)] bounds = {}'.\
                   format(naxlims))

    outfile = args.output
    if (verbose == True):
        print ('output file = {}'.format(outfile))

    stats = args.stats.split(',')
    if (verbose == True):
        print ('stats to compute = {}'.format(stats))

    if (args.twodframe):
        twodframe = True
        if (verbose == True):
            print ('Compute stats by frame')
    else:
        if (verbose == True):
            print ('Compute stats for the requested volume')

    if (args.update):
        update = True
        if (verbose == True):
            print ('Update fits file headers with stats information')

    return  fits_input, naxlims, outfile, stats, twodframe, update, verbose

def compute_stat (stat_to_comp, ipdat):
    """
    Compute requested statistic (stat_to_comp) over array (ipdat)
    """

    if (stat_to_comp == 'average'):
        stat_value = np.average (ipdat, weights=None)

    elif (stat_to_comp == 'max'):
        stat_value = np.max (ipdat)

    elif (stat_to_comp == 'mean'):
        stat_value = np.mean (ipdat)

    elif (stat_to_comp == 'median'):
        stat_value = np.median (ipdat)

    elif (stat_to_comp == 'min'):
        stat_value = np.min (ipdat)

    elif (stat_to_comp == 'mode'):
        stat_value = scst.mode (ipdat, axis=None)[0][0]

    elif ((stat_to_comp == 'rms') or (stat_to_comp == 'std')):
        stat_value = np.std (ipdat)

    elif (stat_to_comp == 'sum'):
        stat_value = np.sum (ipdat)

    elif (stat_to_comp == 'var'):
        stat_value = np.var (ipdat)

    return stat_value

#------------------------------------------------------------------------
def img_stats_main (iargv):
    """
    Extract a subvolume from a 2-D or 3-D image array and compute stats.
    """

    # Parse the command line
    fits_input, naxlims, outfile, stats, twodframe, update, verbose = \
        parse_cmd_line (iargv)

    # Get list of files to work on
    f_files = ru.expand_list_files2(ipfiles=fits_input, echo=verbose)
    num_files = len(f_files)

    # Loop through files, open, extract roi and compute stats
    iseq = 0

    # Stats value(s) dictionary space
    st_val = {}
    
    # setup output stats arrays
    st_val['filename'] = []
    for st_comp in stats:
        st_val[st_comp] = []


    for pf in f_files:
        # open fits file
        hdr, dat = rf.load_fits_file (pf, 
                                      echo=('Short' if (verbose == True) 
                                            else False))

        if (hdr == None):
            # Failed to load for some reason, skip
            continue

        # Extract a subset of an image cube (either 2 or 3-D)
        # Set rgb to false for this application
        cdat, rgb_flag, img_ndim, img_shape = \
            rf.extract_subimage (dat, naxlims, isrgb=False)

        # If ROI axis limits not set, set to existing image limits
        if (naxlims == []):
            if (img_ndim == 2):
                naxlims = [0, img_shape[1],
                           0, img_shape[0]]
            elif (img_ndim == 3):
                naxlims = [0, img_shape[2], 
                           0, img_shape[1], 
                           0, img_shape[0]]
            else:
                print ('Error: unable to set naxlims')
                exit()

        # Construct string showing original file
        # and bounds, in FITS base ONE values
        if (img_ndim == 2):
            histline = '{}[{}:{},{}:{}]'.format(pf, 
                                                naxlims[0]+1, naxlims[1],
                                                naxlims[2]+1, naxlims[3])
        elif (img_ndim == 3):
            histline = '{}[{}:{},{}:{},{}:{}]'.format(pf, 
                                                      naxlims[0]+1, naxlims[1],
                                                      naxlims[2]+1, naxlims[3],
                                                      naxlims[4]+1, naxlims[5])
        else:
            histline = '{}'.format(pf)

        # Construct printing header line (column ids)
        hdr_line = '#{} '.format('FileName')
        if ((img_ndim == 3) and (twodframe == True)):
            hdr_line += '{} '.format('zidx'.capitalize())

        for st_comp in stats:
            hdr_line += '{} '.format(st_comp.capitalize())

        # compute statistics - either for the whole volume, or
        #   if 3-D and requested, for each frame in the z-direction
        # ['num', 'max', 'min', 'average', 'mean', 'median', 'mode',
        #  'rms', 'std', 'sum', 'var']
        # 'quantile' - quantile not implemented

#        # Stats value(s) dictionary space
#        st_val = {}
        
        # Set up output printing line
        op_line = ''

        # Separate out the frame by frame computation of stats from the
        # computation for the full selected region

        # 2D Frame by frame in 3D cube
        if ((img_ndim == 3) and (twodframe == True)):

#            # setup output stats arrays
#            for st_comp in stats:
#                st_val[st_comp] = []

            # add an index array
            st_val['zidx'] = []

            # Loop over the planes in the cube
            for zidx in range(img_shape[0]):

                st_val['filename'].append(pf)

                st_val['zidx'].append(zidx)
                op_line += '{} {:4d} '.format(histline, zidx+1)

                # Loop over the stats requested
                for st_comp in stats:

                    if (st_comp == 'num'):
                        cstat = img_shape[1] * img_shape[2]
                    else:
                        cstat = compute_stat(st_comp, cdat[zidx])

                    st_val[st_comp].append(cstat)
                    op_line += '{} '.format(ru.val_fmt(cstat))

                op_line += '\n'

        # Full 2D or 3D region stats
        else:
            op_line += '{} '.format(histline)

            st_val['filename'].append(pf)

            # Loop over the stats requested
            for st_comp in stats:
                if (st_comp == 'num'):
                    if (img_ndim == 2):
                        cstat = img_shape[0] * img_shape[1]
                    elif (img_ndim == 3):
                        cstat = img_shape[0] * img_shape[1] * img_shape[2]
                else:
                    cstat = compute_stat(st_comp, cdat)

#                st_val[st_comp] = cstat
                st_val[st_comp].append(cstat)
                op_line += '{} '.format(ru.val_fmt(cstat))

            op_line += '\n'

        # print (st_val)

        # direct output
        if ((outfile == '') or (outfile == 'screen') or
            (outfile == 'stdio')):
            # send to screen
            print (hdr_line)
            print (op_line)

        elif (outfile == 'skip'):
            # skip display
            pass

        else:
            # write to a file
            with open(outfile, 'a') as fo:
                fo.write ('{}\n'.format(hdr_line))
                fo.write ('{}'.format(op_line))

        if (update == True):
            hdr['STAT_REG'] = histline

        # Write stats to image header(s)
        #        if (update == True):
        #            rf.write_fits_file (outnam, hdr=hdr, data=cdat)

    return stats, st_val

#------------------------------------------------------------------------
# Execute as a script

if __name__ == '__main__':
    import sys
    
    argv = sys.argv
    stats, st_val = img_stats_main (argv)

    # print (stats, st_val)

    exit()

