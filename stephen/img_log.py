#!/usr/bin/env python3
__doc__="""\
img_log.py - extract image headers and create a tabular log

Can be run from the command line, and img_log_main() can also be
imported and used as a function.

To use as a function:
  import img_log as imglg
  hdrlog = imglg.img_imglg_main(iargv)
where iargv is a list in the format of the command line input.
You can get an example by running this from the command line with
the -v (verbose) option on and looking for the first output line that
starts with "argc = ..." The list given after the argument count is the
format of the input iargv.

TBD: At some point I would be inclined to set up alternate args to 
img_log_main() in place of iargv that simplifies calling as a function.

Updates:
2021 Feb 28 - initial version
"""

__intro__= """\
Image header extraction and construction of single tabular log.
"""
__author__="Stephen Levine"
__date__="2021 Feb 28"

#------------------------------------------------------------------------

# Command line arg parsing
import argparse

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

    cli = argparse.ArgumentParser(prog='img_log.py', 
                                  description=__intro__,
                                  epilog='version: '+__date__)
    
    cli.add_argument ('fitsfiles', nargs='?', default=fits_input0,
                      help='Required Input Filename - Fits files. ' + 
                      'Default: ' + fits_input0)

    def_keyw = 'All'
    cli.add_argument ('-k', '--keywords', type=str, default=def_keyw,
                      help='Keywords to extract  ' +
                      'Default: ' + def_keyw)


    def_output = ''
    cli.add_argument ('-o', '--output', type=str, default=def_output,
                      help='Output file name. No value, stdio, or screen ' +
                      'will write the output to the screen. Anything else ' +
                      'will be interpretted as the name for an output file. ' +
                      'Default: ' + def_output)

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

    keyw = args.keywords.replace('\n','').replace(' ','').split(',')
    if ((keyw == []) or (keyw == '') or (keyw == ['All']) or
        (keyw == ['sort'])):
        keyw = 'sort'
    if (verbose == True):
        print ('keywords = {}'.format(keyw))

    outfile = args.output
    if (verbose == True):
        print ('output file = {}'.format(outfile))

    return  fits_input, keyw, outfile, verbose

#------------------------------------------------------------------------
def img_log_main (iargv):
    """
    Extract fits header keywords and write out a log
    """

    # Parse the command line
    fits_input, keyw, outfile, verbose = parse_cmd_line (iargv)

    # Get list of files to work on
    f_files = ru.expand_list_files2(ipfiles=fits_input, echo=verbose)
    num_files = len(f_files)

    # Loop through files, open, extract headers and write out a line
    iseq = 0

    # preset header and rows to empty strings, just in case
    tblhdr = ''
    tblrows = ''

    # Check for keyword set, or use all
    if (keyw == ['sort']):
        keyorder = 'sort'
    elif (keyw == ''):
        keyorder = 'sort'
    else:
        keyorder = keyw

    if (verbose == True):
        print ('Keywords: {}'.format(keyorder))
        print ('{} files: {}'.format(num_files, f_files))

    for pf in f_files:
        # open fits file
        hdr = rf.load_fits_hdr (pf, echo=('Short' if (verbose == True) 
                                          else False))

        if (hdr == None):
            # Failed to load for some reason, skip
            continue

        # for first successful fits file, construct table header
        if (iseq == 0):
            tblhdr = ru.print_tablehdr (hdr, ordering=keyorder,
                                        fltfmt='{:>18s}')

        # increment file counter
        iseq += 1

        # add a row for this file
        tblrows += ru.print_tablerow (hdr, ordering=keyorder, fname=pf,
                                       fltfmt='{:>18.10f}')

    # direct output
    if ((outfile == '') or (outfile == 'screen') or
        (outfile == 'stdio')):
        # send to screen
        print ('{}'.format(tblhdr))
        print ('{}'.format(tblrows))
        
    elif (outfile == 'skip'):
        # skip display
        pass

    else:
        # write to a file
        with open(outfile, 'a') as fo:
            fo.write ('{}'.format(tblhdr))
            fo.write ('{}'.format(tblrows))
            
    return tblhdr, tblrows

#------------------------------------------------------------------------
# Execute as a script

if __name__ == '__main__':
    import sys
    
    argv = sys.argv
    tblhdr, tblrows = img_log_main (argv)

    exit()

