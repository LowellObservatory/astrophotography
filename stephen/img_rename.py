#!/usr/bin/env python3
__doc__="""\
img_rename.py - rename images with assort names with a single rootname

Can be run from the command line, and img_rename_main() can also be
imported and used as a function.

To use as a function:
  import img_rename as imgrn
  hdrlog = imgrn.img_rename_main(iargv)
where iargv is a list in the format of the command line input.
You can get an example by running this from the command line with
the -v (verbose) option on and looking for the first output line that
starts with "argc = ..." The list given after the argument count is the
format of the input iargv.

TBD: At some point I would be inclined to set up alternate args to 
img_log_main() in place of iargv that simplifies calling as a function.

Updates:
2021 Mar 01 - initial version
"""

__intro__= """\
Rename images with assorted names with a single rootname, in user
determined ordering.
"""
__author__="Stephen Levine"
__date__="2021 Mar 01"

#------------------------------------------------------------------------

# Command line arg parsing
import argparse

# date/time package
import datetime as dt

# Numpy
# import numpy as np

# For use in sorting by a dictionary key within a list of dictionaries
from operator import itemgetter

# operating system interactions
import os

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

    cli = argparse.ArgumentParser(prog='img_rename.py', 
                                  description=__intro__,
                                  epilog='version: '+__date__)
    
    cli.add_argument ('fitsfiles', nargs='?', default=fits_input0,
                      help='Required Input Filename - Fits files. ' + 
                      'Default: ' + fits_input0)

    def_log = 'FileRename'
    cli.add_argument ('-l', '--logfile', type=str, default=def_log,
                      help='Renaming log file name, and root for ' +
                      'shell file to revert the change. ' +
                      'Default: ' + def_log)

    def_output = ''
    cli.add_argument ('-o', '--output', type=str, default=def_output,
                      help='Output file name root. ' +
                      'Default: ' + def_output)

    def_sort = 'DATE-OBS'
    cli.add_argument ('-s', '--sort', type=str, default=def_sort,
                      help='Keyword(s) to use as sort key(s). Comma ' +
                      'separated list, if more than 1. Dictionary ' +
                      'by key order for the first 2 keys.  The rest ' +
                      'are used just to extract added informational ' +
                      'keywords. An example might be IMAGETYP,DATE-OBS to ' +
                      'sort first by IMAGETYP, and within each IMAGETYP, ' +
                      'then sort by DATE-OBS.' +
                      'Default: ' + def_sort)

    def_tail = '.fit'
    cli.add_argument ('-t', '--tail', type=str, default=def_tail,
                      help='Output file name tail. ' +
                      'Default: ' + def_tail)

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

    logfile = args.logfile
    if (verbose == True):
        print ('logfile file = {}'.format(logfile))

    outfile = args.output
    if (verbose == True):
        print ('output file = {}'.format(outfile))

    sortkeys = args.sort.split(',')
    if (verbose == True):
        print ('sortkeys = {}'.format(sortkeys))

    filetail = args.tail
    if (verbose == True):
        print ('output file tail = {}'.format(filetail))

    return  fits_input, logfile, outfile, sortkeys, filetail, verbose

#------------------------------------------------------------------------
def img_rename_main (iargv):
    """
    Rename fits files with assorted names to those with a common
    filename root.  Sort based on user defined FITS keyword.
    """

    # Parse the command line
    fits_input, logfile, outfile, sortkeys, filetail, verbose = \
        parse_cmd_line (iargv)

    # Get list of files to work on
    f_files = ru.expand_list_files2(ipfiles=fits_input, echo=verbose)
    num_files = len(f_files)

    # Loop through files, open, extract headers and write out a line
    iseq = 0

    filedicts = []

    if (verbose == True):
        print ('Sort keys(s): {}'.format(sortkeys))
        print ('{} files: {}'.format(num_files, f_files))

    # Read fits file headers and extract name and sort key(s) into
    # list of dicts filedicts
    for pf in f_files:
        tdict = {}
        # open fits file
        hdr = rf.load_fits_hdr (pf, echo=('Short' if (verbose == True) 
                                          else False))

        if (hdr == None):
            # Failed to load for some reason, skip
            continue

        # increment file counter
        iseq += 1

        # Get a DATE-OBS from the header to use to set the 
        # dateutil.parser.parse default.

        bdefdt, defdt = ru.isadatetime (hdr['DATE-OBS'])
        if (bdefdt == False):
            bdefdt, defdt = ru.isadatetime (hdr['DATEOBS'])
            if (bdefdt == False):
                bdefdt, defdt = ru.isadatetime (hdr['DATE'])
                if (bdefdt == False):
                    defdt = None

        # hold default outfile rootname based on date of 1st file
        # just in case
        if (iseq == 1):
            if (defdt != None):
                outdefault = dt.datetime.strftime (defdt, "%Y%m%d")
            else:
                outdefault = "nodate"
        
        # construct dict for this file
        tdict['filename'] = pf
        for sk in sortkeys:
            try:
                # Test if is a datetime string
                bdt, tdt = ru.isadatetime (hdr[sk], defdt=defdt)
                if (bdt == True):
                    tdict[sk] = tdt

                elif (ru.isainumber(hdr[sk]) == True):
                    tdict[sk] = int(hdr[sk])

                elif (ru.isanumber(hdr[sk]) == True):
                    tdict[sk] = float(hdr[sk])

                else:
                    tdict[sk] = hdr[sk]

            except:
                tdict[sk] = 'None'

        filedicts.append(tdict)

    # ru.print_struct (filedicts)

    # Sort by primary key
    # If there is a secondary key, then sort each sub-group by those
    # E.g. Sort by IMAGETYP, then within IMAGETYP by DATE-OBS

    s0files = sorted (filedicts, key=itemgetter(sortkeys[0]))
    s0fl = len(s0files)
    skl  = len(sortkeys)
    # print ('len(sortkeys,s0files) == {} {}'.format(skl, s0fl))

    # Optional sort by secondary key
    if (len (sortkeys) > 1):
        subfiles = []
        s0key  = sortkeys[0]
        subkey = sortkeys[1]
        subst  = 0
        subval = s0files[subst][s0key]
        for j in range(1, len(s0files)):
            suben = j
            newval = s0files[j][s0key]
            if (newval != subval):
                subfiles.extend(sorted (s0files[subst:suben], 
                                        key=itemgetter(subkey)))
                subst = suben
                subval = newval
        subfiles.extend(sorted (s0files[subst:suben+1], 
                                key=itemgetter(subkey)))
        # print (subfiles)

    else:
        subfiles = s0files
    
    if (verbose == True):
        sortkeys.insert(0, 'filename')
        print ('Keys = {}'.format(sortkeys))

        ttbl = ru.print_tablehdr (subfiles[0], ordering=sortkeys, 
                                  strfmt='{:<22s}', intfmt='{:>8s}', echo=False)
        for j in subfiles:
            ttbl += ru.print_tablerow (j, ordering=sortkeys, 
                                       strfmt='{:<22s}', intfmt='{:>8d}', echo=False)
        print (ttbl)
    
    # Rename files in sorted order

    # Check for outfile rootname. If null, set to DATE-OBS date of first
    # image
    if (outfile == ''):
        outfile = outdefault + '.'

    # Set up number of sequence digits
    if (s0fl > 9999):
        seqfmt = '{}{:05d}{}'
    else:
        seqfmt = '{}{:04d}{}'

    # Log the rename sequence to a file, and create a reversion script
    fo_log    = open (logfile + '.log', 'w')
    fo_log.write ('# Log of renaming of raw files to a continuous sequence.\n')
    fo_log.write ('# Date: {}\n'.format(dt.datetime.now().isoformat()))

    fo_revert = open (logfile + '_revert.csh', 'w')
    fo_revert.write ('#!/bin/tcsh\n')
    fo_revert.write ('# Script to undo file renaming\n')

    iseq = 0
    for j in subfiles:
        iseq += 1
        oldfname = j['filename']
        newfname = seqfmt.format(outfile, iseq, filetail)

        # kludge: use path.exists to check dest filename, since
        # os.rename() will silently overwrite if you have permission
        if (os.path.exists(newfname) == True):
            fo_log.write ('{} to {} Failed, dst exists.\n'.format(
                    oldfname, newfname))
            fo_revert.write ('# mv \"{}\" \"{}\"\n'.format(newfname, 
                                                           oldfname))
        else:
            try:
                os.rename (oldfname, newfname)
                fo_log.write ('{} to {} Successful\n'.format(oldfname,
                                                             newfname))
                fo_revert.write ('mv \"{}\" \"{}\"\n'.format(newfname,
                                                             oldfname))
            
            except:
                fo_log.write ('{} to {} Failed, some problem.\n'.format(
                        oldfname,newfname))
                fo_revert.write ('# mv \"{}\" \"{}\"\n'.format(newfname, 
                                                               oldfname))

    fo_log.close()
    fo_revert.close()

    return

#------------------------------------------------------------------------
# Execute as a script

if __name__ == '__main__':
    import sys
    
    argv = sys.argv
    img_rename_main (argv)

    exit()

