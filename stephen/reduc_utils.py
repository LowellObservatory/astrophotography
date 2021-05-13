#!/usr/bin/env python3
__doc__="""\
reduc_utils.py - Utility functions for reduction pipeline

Int, Float type and Sexigesimal formatted value check:
 def isainumber(a) - is string an integer value?
 def isanumber(a) - is string a floating point value?
 def isasnumber(a) - is the string a sexigesimal formatted value?

 def hms2sec(hh ...) - sexigesimal format to decimal seconds
 def sec2hms(sec ...) - decimal seconds to sexigesimal format
 def isadatetime (instr) - try to parse a string into a datetime

Routines for handling space separated data file (Ra, Rb, PICA cat):
 def get_ssv_colhdrs () 
 def get_rb_colhdrs() - calls get_ssv_colhdrs()
 def get_pica_colhdrs() - calls get_ssv_colhdrs()
 def get_rbhdr () - read Rb file header 
 def get_rbdata () - read Rb file data

Routines for listing out files and directories:
 def list_files (dirname = './', ftail= '.txt')
 def list_dirs (dirname = './')
 def list_astfiles (dirname = './')
 def list_mpcfiles (dirname = './')
 def expand_list_files (ipfiles='./*.fits', echo=True)
 def expand_list_files2 (ipfiles='./*.fits', echo=True) - adds comma separator option

Print out dict and list of dicts
 def val_fmt () - simple print fmt by value type
 def print_struct (toprint) -  as JSON struct:
 def print_tablehdr (toprint) - print columnar table header based on toprint
 def print_tablerow (toprint) - as one line of a columnar table

URL query routines:
 def pica_vo_cone () - call get_url()
 def get_url () - initial version. Handles GET queries
 def get_url2 () - expanded version of get_url(). Handles GET and POST queries.

Usage: import reduc_utils as ru

Updates:
2021 Mar 09 - merged in val_fmt()
2021 Mar 01 - added isadatetime(), using dateutil.parser.parse
2021 Feb 28 - added print_table{hdr,row} functions
2020 Sep 26 - check 3 char string in #Telescop= as possible MPC site code
"""

__intro__= """\
A small library of routines for use in the image reduction pipeline.
"""
__author__="Stephen Levine"
__date__="2021 Mar 09"

#------------------------------------------------------------------------

# JSON handling
import json

# Basic math functions
from math import sqrt, cos, pi
#import math

# For use in sorting by a dictionary key within a list of dictionaries
from operator import itemgetter

# Date/Time
import datetime as dt
import dateutil.parser as dupa

# Package for parsing directories/files
import glob

# Package for OS access
import os

# System interface
import sys

# urllib - URL library for web access (py3 version). Need urllib2 for py2.
# socket is needed to be able to set the connection timeout duration
import urllib.request
import urllib.parse
from urllib.error import URLError

import socket

#------------------------------------------------------------------------
# simple type checks of input string
#------------------------------------------------------------------------
# TITLE: isainumber - check if a string is an integer number
def isainumber(a):
    """Q&D test to see if a string is an integer number.
    Courtesy of the internet, slightly modified.
    """
    try:
        int(a)
        bool_a = True
    except:
        bool_a = False

    return bool_a

#------------------------------------------------------------------------
# TITLE: isanumber - check if a string is a floating point number
def isanumber(a):
    """Q&D test to see if a string is a floating point number.
    Courtesy of the internet, slightly modified.
    """
    try:
        float(a)
        bool_a = True
    except:
        bool_a = False

    return bool_a

#------------------------------------------------------------------------
# TITLE: isasnumber - check if a string is in sexigesimal format
def isasnumber(a):
    """Q&D test to see if a string is a sexigesimal format number.
    Assumes either ':' or ' ' separation between the values.
    Returns True|False and the HH, MM, SS.S values
    """

    bool_a = False
    b0 = 0
    b1 = 0
    b2 = 0.0
    
    # check ':' separated
    for i in [':', ' ']:
        try:
            b = a.split(i)
            lb = len(b)
        except:
            break
        
        try:
            b0 = int(b[0])
            b1 = int(b[1])
            b2 = float(b[2])
            if ((b1 >= 0) and (b1 < 60)):
                if ((b2 >= 0.0) and (b2 < 60.0)):
                    bool_a = True
                    break
        except:
            pass

    return [bool_a, b0, b1, b2]

# TITLE: hms2sec - sexigesimal to decimal seconds conversion
def hms2sec (hh, mm, ss):
    """
    Convert HH MM SS.s to decimal seconds.
    """
    sgn = -1 if (hh < 0) else 1
    secval = sgn * ((abs(hh) * 60.0 + mm) * 60.0 + ss)
    return secval

# TITLE: sec2hms - decimal seconds to sexigesimal conversion
def sec2hms(sec, n_msec=3, tonly=False):
    """
    Convert decimal seconds to 'D days, HH:MM:SS.FFF' 
    n_msec == significant digits on the seconds
    tonly == return time part only (True), include days (False)

    Modified and based on, from the web:
    https://stackoverflow.com/questions/775049/how-do-i-convert-seconds-to-hours-minutes-and-seconds
    """

    # Handle case where given list of seconds to convert
    if (hasattr(sec,'__len__')):
        return [sec2hms(s, n_msec=n_msec, tonly=tonly) for s in sec]

    # Compute days, hours, minutes, seconds
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)

    
    if (n_msec > 0):
        spat = '{}{:d}.{:d}f{}'.format('{:0', n_msec+3, n_msec, '}')
        sp = s
        
    else:
        spat = '{}'.format('{:02d}')
        sp = int(round(s))

    pattern = '{}:{}:{}'.format('{:02d}', '{:02d}', spat)

    tpart  = pattern.format(int(h), int(m), sp)
    dtpart = '{:d}T{}'.format(int(d), tpart)
    
    if (tonly == True):
        return tpart
    else:
        return dtpart

# TITLE: extract_datetime - extract date and/or time from a string
#        return datetime
def isadatetime (instr, defdt=None):
    """ 
    TITLE: isadatetime - test and extract date and/or time from a 
    string return datetime
    """
    bool_a = False
    try:
        dtinst = dupa.parse(instr, default=defdt)
        bool_a = True
    except:
        dtinst = dt.datetime (1,1,1)
        bool_a = False

    return bool_a, dtinst
   
#------------------------------------------------------------------------
def get_ssv_colhdrs (inbuf, h1id='#1', h2id='#1U', h3id='#1N', h4id='#1F',
                     echo=False):
    """
    Get Space Separated Variable Column Headers

    Read in up to 4 rows of column headers from the inbuf buffer.
    h1id, h2id, h3id, h4id are the leading strings identifying the up to
    4 header lines. If any are set to None, they will be skipped.
    Returns 4 lists that correspond to the h?ids.
    Nominal assumptions are: #1 == ID
                             #1U == Units
                             #1N == Col Number
                             #1F == Col Format string
    """

    # set up empty return lists
    c1list = []
    c2list = []
    c3list = []
    c4list = []

    # split the buffer into lines
    inp_lines = inbuf.splitlines()

    # find and extract the rows with the column header information
    # iterate over the lines
    hflg = 0
    for i in inp_lines:
        j = ' '.join(i.split()).split()

        # Column number
        if (j[0] == h1id):
            c1list = j[1:]
            hflg |= 0x1

        elif (j[0] == h2id):
            c2list = j[1:]
            hflg |= 0x2

        elif (j[0] == h3id):
            c3list = j[1:]
            hflg |= 0x4

        elif (j[0] == h4id):
            c4list = j[1:]
            hflg |= 0x8
            
    if ((echo == True) or (echo == 'debug')):
        print ('HeaderFlagBits = {}'.format(hflg))
        
    if ((echo == True) or (echo == 'hdrs')):
        print ('Header l.1 = {}'.format(c1list))
        print ('Header l.2 = {}'.format(c2list))
        print ('Header l.3 = {}'.format(c3list))
        print ('Header l.4 = {}'.format(c3list))

    return c1list, c2list, c3list, c4list

def get_rb_colhdrs(inp, echo=False):
    """
    Simple call to handle Ra, Rb style row headers
    Only uses 3 of 4 possible header lines.
    """
    c1, c2, c3, c4 = get_ssv_colhdrs (inp, h1id='#1', h2id='#1U', h3id='#1N',
                                      h4id=None, echo=echo)
    return c1, c2, c3

def get_pica_colhdrs(inp, echo=False):
    """
    Simple call to handle PICA catalogue style row headers
    Only uses 3 of 4 possible header lines.
    """
    c1, c2, c3, c4 = get_ssv_colhdrs (inp, h1id='#1', h2id='#2', h3id='#3',
                                      h4id=None, echo=echo)
    return c1, c2, c3

#------------------------------------------------------------------------
# Rb file parsing - get_rbhdr, get_rbdata
def get_rbhdr (filename, min_fit_stars=50, echo=False):
    """ 
    Parse out specific items from Rb file header. 
    For look up, we'll need:
      #Object=
      #Filter=
      #Date=
      #UT=
      #Exptime=
      #Scale= 2.514
      #nx,ny= 4096 4096
      #Longitude= -70.808056

      #Latitude= -30.169917
      #RANEW=   01:57:17.601
      #DECNEW=  +00:03:15.38
      #RADNEW=     76.4935730

      #DECDNEW=   -10.9801708
      #EPOCHNEW= 2012.9168025

      #RMS differences [arcsec]: N.NNN N.NNN for N points

    Returns a dictionary with the relevant information. If the dictionary
    is complete, the status value will be OK. Ie ast_hdr['status'] == 'OK'.
    Possible values for status:
    OK == all values found, look reasonable to continue
    SKIP == some values don't look right
    BAD == not all values found and/or some are also bad
    """

    flag = 0x0
    ast_hdr = {'status': 'BAD', 
               'fileid': 'UNK', 
               'object': 'UNK',
               'filter': 'UNK',
               'dateobs': 'UNK', 'exptime': 'UNK', 'midtime': 'UNK',
	       'scale': 'UNK', 'npix': 'UNK',
               'lon':   'UNK', 'lat':  'UNK', 
               'obscode': 500, 'telid': 'GEO',
               'ra':    'UNK', 'dec':  'UNK',
               'rad':   'UNK', 'decd': 'UNK',
               'epoch': 'UNK',
               'nfitpts': 'UNK' }

    with open(filename, 'r') as fl:
        inp = fl.read()
        k = 0
        inpspl = inp.splitlines()
        # TBD - Need to set the range on this based on finding line #1
        for i in inpspl:
            # Last header line to parse should be the #RMS line from the fit
            d = i.split(' ')
            e = d[0].strip()
            if (e == '#RMS'):
                ast_hdr['nfitpts'] = int(d[6].strip())
                flag = flag | 0x8000
                break;

            # parse for other header information
            a = i.split('=')
            b = a[0].strip()
            if (len(a) > 1):
                c = a[1].strip()

            ast_hdr['fileid'] = filename
            flag = flag | 0x01

            if (b == '#Object'):
                ast_hdr['object'] = c
                flag = flag | 0x02

            elif (b == '#Filter'):
                ast_hdr['filter'] = c
                flag = flag | 0x04

            elif (b == '#Date'):
                date_ymd = dt.datetime.strptime(c, "%Y-%m-%d")
                flag = flag | 0x08

            elif (b == '#UT'):
                date_ut = dt.timedelta(hours=float(c))
                flag = flag | 0x10

            elif (b == '#Exptime'):
                ast_hdr['exptime'] = dt.timedelta(seconds=float(c))
                flag = flag | 0x20

            elif (b == '#nx,ny'):
                # take the larger detector dimension
                sz_x  = float(c.split(' ')[0])
                sz_y  = float(c.split(' ')[1])
                if (sz_x >= sz_y):
                    ast_hdr['npix'] = sz_x
                else:
                    ast_hdr['npix'] = sz_y
                    
                flag = flag | 0x40

            elif (b == '#Scale'):
                ast_hdr['scale'] = float(c)
                flag = flag | 0x80

            elif (b == '#Longitude'):
                ast_hdr['lon'] = float(c)
                flag = flag | 0x100

            elif (b == '#Latitude'):
                ast_hdr['lat'] = float(c)
                flag = flag | 0x200

            elif (b == '#Telescop'):
                ast_hdr['telid'] = c
                flag = flag | 0x300

            elif (b == '#RANEW'):
                ast_hdr['ra'] = c.replace(':', ' ')
                flag = flag | 0x400

            elif (b == '#DECNEW'):
                ast_hdr['dec'] = c.replace(':', ' ')
                flag = flag | 0x800

            elif (b == '#RADNEW'):
                ast_hdr['rad'] = float(c)
                flag = flag | 0x1000

            elif (b == '#DECDNEW'):
                ast_hdr['decd'] = float(c)
                flag = flag | 0x2000

            elif (b == '#EPOCHNEW'):
                ast_hdr['epoch'] = float(c)
                flag = flag | 0x4000

            # print ('{} - {} - {:x}'.format(k, a, flag))
            k = k + 1
        
        fl.close()

        if (flag == 0xffff):
            ast_hdr['status'] = 'OK'

            # Put the two parts of the date and time together to
            # get UT @ start (dateobs) and UT @ exp mid-time (midtime)
            ast_hdr['dateobs'] = date_ymd + date_ut
            ast_hdr['midtime'] = date_ymd + date_ut + 0.5 * ast_hdr['exptime']
            
            # Figure out how to get the site information:
            #    need the site code (ideally anyway)
           
            if ((ast_hdr['telid'] == 'DCT') or
                (ast_hdr['telid'] == 'LDT')):
                ast_hdr['obscode'] = 'G37'
                # G37 248.57749 0.822887 +0.566916 Lowell Discovery Telescope
                
            elif ((ast_hdr['telid'] == 'hall') or
                  (ast_hdr['telid'] == 'perkins') or
                  (ast_hdr['telid'] == '2GSSA')):
                ast_hdr['obscode'] = '688'
                # 688 248.4645  0.81938  +0.57193  Lowell Observatory, Anderson Mesa Station
                
            elif ((ast_hdr['telid'] == 'NO61') or
                  (ast_hdr['telid'] == 'NO40') or
                  (ast_hdr['telid'] == 'NO13')):
                ast_hdr['obscode'] = '689'
                
            elif (ast_hdr['telid'] == 'Clay_Mag_2'):
                ast_hdr['obscode'] = '268'
                # 268 289.30803 0.875516 -0.482342 New Horizons KBO Search-Magellan/Clay
                
            elif (ast_hdr['telid'] == 'Baade_Mag_1'):
                ast_hdr['obscode'] = '269'
                # 269 289.30914 0.875510 -0.482349 New Horizons KBO Search-Magellan/Baade

            elif (ast_hdr['telid'] == '6.5m'):
                ast_hdr['obscode'] = '304'
                # 304 289.2980  0.87559  -0.48217  Las Campanas Observatory

            elif ((ast_hdr['telid'] != 'GEO') and
                  (len(ast_hdr['telid']) == 3)):
                # Assume that if #Telescop= is a 3 char string, it is the
                # MPC site code - kind of a last ditch effort
                ast_hdr['obscode'] = ast_hdr['telid']
                
            # if ((ast_hdr['lat'] > -31.) and (ast_hdr['lat'] < -30.0)):
            #     ast_hdr['obscode'] = 'W84'
            #     # CTIO
            # elif (ast_hdr['fileid'][0] == 's'):
            #     ast_hdr['obscode'] = 'W84'
            # elif ((ast_hdr['lat'] > 32.) and (ast_hdr['lat'] < 33.0)):
            #     ast_hdr['obscode'] = '645'
            #     # Apache Point
            # elif (ast_hdr['fileid'][0] == 'n'):
            #     ast_hdr['obscode'] = '645'

            # compute radius of the CCD diagonal in arcmin, pad by 10%
            #  uses the larger dimension of the detector
            ast_hdr['radius'] = ast_hdr['scale'] * ast_hdr['npix'] / \
                (60.0 * sqrt(2)) * 1.1

            # Check for reasonable scale factor, if not w/in bounds, set
            # status to SKIP. Limits set to 0 and 5 arcsec/pix for now
            if ((ast_hdr['scale'] < 0.0) or (ast_hdr['scale'] > 5.0)):
                ast_hdr['status'] = 'SKIP'

            # Check for a reasonable min number of fit stars
            if (ast_hdr['nfitpts'] < min_fit_stars):
                ast_hdr['status'] = 'SKIP'

        if (echo == True):
            for ei in sorted(ast_hdr.keys()):
                print ('{0:16s} = {1}'.format(ei, ast_hdr[ei]))

    return ast_hdr

def get_rbdata (filename, echo=False):
    """ 
    Parse out specific items from Rb file data section.
    now all are returned == returned for each record
     Col    Object                    DictID
     ----   ------                    ------
        1   XWIN_IMAGE [pix]          xwin
        2   YWIN_IMAGE [pix]          ywin
        3   ID                        id
        4   X_IMAGE [pix]             xim
        5   Y_IMAGE [pix]             yim
        6   ERRX2W [pix^2]            errx2w
        7   ERRY2W [pix^2]            erry2w
        8   ERRXYW [pix^2]            errxyw
        9   Awin [pix]                awin
       10   Bwin [pix]                bwin
       11   ThetaWin [deg]            thetawin
       12   MAG_AUTO [mag]            magauto
       13   MAGERR_AU(TO) [mag]       magerrau
       14   FWHM [pix]                fwhm
       15   Elong [nd]                elong
       16   Ellip [nd]                ellip
       17   FLAGS                     flags
       18-26 Mag1 - Mag9 [mag]        mag[1-9]
       27-35 SigMag1 - SigMag9 [mag]  sigmag[1-9]
       36   RA [deg]                  ra
       37   Dec [deg]                 dec
       38   Xi [asec]                 xi
       39   Eta [asec]                eta
       40   RefID                     refid
       41   O-Cxi [asec]              o-cxi
       42   O-Ceta [asec]             o-ceta
       43   O-Cx [pix]                o-cx
       44   O-Cy [pix]                o-cy
       45   RefFlg [hex]              refflg
       46   PF_RA [au]                pf_ra
       47   PF_DEC [au]               pf_dec
       48-?  Ref Cat Mags [mag]       E.g.for GaiaDR2: g, bp, rp

    Returns a subset of the columns for each row, and sorts the list in RA.
    Each row is returned as a dictionary, and the whole is a list of
    dictionaries.

    """

    _starttime = dt.datetime.now()

    # open and read in the ast file
    with open(filename, 'r') as fl:
        inp = fl.read()
        fl.close()

    # Read in column header names, units and numbers
    col_names, col_units, col_nums = get_rb_colhdrs (inp, echo=echo)
        
    # remove [] from unit names
    for k in range(len(col_units)):
        col_units[k] = col_units[k].replace('[','').replace(']','')
        # print (k)
        
    # option to lowercase the names
    setlower = True
    if (setlower == True):
        for k in range(len(col_names)):
            col_names[k] = col_names[k].lower()
            # print (k)

    if ((echo == True) or (echo == 'hdrs')):
        print ('Header names = {}'.format(col_names))
        print ('Header units = {}'.format(col_units))
        print ('Header nums  = {}'.format(col_nums))
    
    # split into lines
    inp_lines = inp.splitlines()

    # Read the data block
    # prep
    idx = 0
    data_lines = []

    # iterate over the lines
    for i in inp_lines:
        tmp_flds = {}

        # skip any line that starts with '#'
        if (i[0] != '#'):
            # split, join, split to compress all whitespace to single
            # space and then split
            j = ' '.join(i.split()).split()
            # print ('{} - {}'.format(idx, j))

            for k in range(len(j)):
                if (('px'    in col_units[k]) or ('mag'   in col_units[k]) or
                    ('asec'  in col_units[k]) or ('deg'   in col_units[k]) or
                    ('au'    in col_units[k]) or ('as/hr' in col_units[k]) or
                    ('elong' in col_names[k]) or ('ellip' in col_names[k])):
                    tmp_flds[col_names[k]] = float(j[k])
                    
                elif ('hex' in col_units[k]):
                    tmp_flds[col_names[k]] = int(j[k], base=16)
                    
                elif (('id' in col_names[k]) or ('flag' in col_names[k]) or
                      ('mat' in col_names[k])):
                    tmp_flds[col_names[k]] = int(j[k])

                else:
                    tmp_flds[col_names[k]] = (j[k])
                    
            # tmp_flds['x']        = float(j[ 0])
            # tmp_flds['y']        = float(j[ 1])
            # tmp_flds['number']   = int  (j[ 2])
            # tmp_flds['mag_auto'] = float(j[11])
            # tmp_flds['mag_err']  = float(j[12])
            # tmp_flds['fwhm']     = float(j[13])
            # tmp_flds['rad']      = float(j[35])
            # tmp_flds['decd']     = float(j[36])
            # tmp_flds['xi']       = float(j[37])
            # tmp_flds['eta']      = float(j[38])
            # tmp_flds['refid']    = int  (j[39])
            ## print ('{} - {}'.format(idx, tmp_flds))

            data_lines.append(tmp_flds)

            idx = idx + 1
            
    # print ('{}'.format(data_lines))

    # sort the list by Dec
    # data_rasort = sorted(data_lines, key=itemgetter('decd'))
    data_rasort = sorted(data_lines, key=itemgetter('dec'))

    if ((echo == True) or (echo == 'data')):
        print_struct(data_rasort)
        #for j in data_rasort:
            #        print ('{:>8s} {:>8s} {:>5d} {:>8s} {:>6s} {:>11s} {:>11s} {:>9s} {:>9s} {:>12s}'.
            #print ('{:8.3f} {:8.3f} {:5d} {:8.4f} {:6.2f} {:6.2f} {:11.7f} {:11.7f} {:9.3f} {:9.3f} {:21d}'.
            #       format(j['x'], j['y'],
            #              j['number'], j['mag_auto'], j['mag_err'],
            #              j['fwhm'],
            #              j['rad'], j['decd'], 
            #              j['xi'], j['eta'], 
            #              j['refid']))
        
    _endtime = dt.datetime.now()

    if ((echo == 'debug') or (echo == True)):
        print ('#{} NLINES = {} took {}'.format(filename, 
                                                len(data_rasort), 
                                                (_endtime - _starttime)))

    return data_rasort

#------------------------------------------------------------------------
# Support routines - file manipulation

def list_files (dirname = './', ftail= '.txt', echo=False):
    """
    Listing of files in a directory with particular extension.
    Sorts alphabetically.
    Defaults to list .txt files in the current directory.
    """
    files = sorted(glob.glob(dirname + '/*' + ftail))
    if (echo == True):
        print ('{}'.format(files))
    return files

def list_astfiles (dirname = './'):
    """ listing of ast files in a directory. """
    files = list_files (dirname=dirname, ftail='.ast')
    return files

def list_mpcfiles (dirname = './'):
    """ listing of mpc files in a directory. """
    files = list_files (dirname=dirname, ftail='.mpc')
    return files

def expand_list_files (ipfiles='./*.fits', echo=True):
    """
    Listing of files based on the input (regular expression) string
    files.
    Sorts alphabetically/numerically.
    DEPRECATED in favor of expand_list_files2()
    """
    files = sorted(glob.glob(ipfiles))
    if (echo == True):
        print ('{}'.format(files))
    return files
                
def expand_list_files2 (ipfiles='./*.fits', echo=True):
    """
    Listing of files based on the input (regular expression) string
    files.
    Sorts alphabetically/numerically.
    Allow expansion of comma separated list, mixed with regex.
    """
    if (',' in ipfiles):
        files = []
        for ipx in ipfiles.replace(' ','').split(','):
            files.extend(sorted(glob.glob(ipx)))
    else:
        files = sorted(glob.glob(ipfiles))

    if (echo == True):
        print ('{}'.format(files))
    return files
                
def val_fmt (cstat):
    """
    Set up printing format by value type.
    """
    jt = type(cstat)
    if ((jt is int) or (jt is np.uint16)):
        retval = '{:>6d}'.format(cstat)
    elif ((jt is float) or (jt is np.float64)):
        retval = '{:>.3f}'.format(cstat)
    else:
        retval = '{}'.format(str(cstat))

    return retval

def print_struct (toprint):
    """
    Print out the json style dictionary portion requested.
    If there is a datetime item, reformat as an isoformat string for
    printing, since the json.dumps doesn't handle datetime structures
    nicely.
    """
    if (type(toprint) is dict):
        i = toprint
        # force a local copy so as not to modify the original list
        # j = i.copy()
        # for ki, kj in zip(i, j):
        j = {}
        for ki in i:
            if (type(i[ki]) is not dict):
                if (type(i[ki]) is dt.datetime):
                    j[ki] = '{}'.format(i[ki].isoformat())
                elif (type(i[ki]) is dt.timedelta):
                    j[ki] = '{}'.format(i[ki].total_seconds())
                else:
                    j[ki] = i[ki]
            # print ('i[ki={}], j[ki={}] == {} {}'.format (ki,ki,i[ki], j[ki]))
        lcl = j

    elif (type(toprint) is list):
        lcl = []
        for i in toprint:
            # force a local copy so as not to modify the original list
            j = i.copy()
            for ki, kj in zip(i, j):
                if (type(i[ki]) is not dict):
                    if (type(i[ki]) is dt.datetime):
                        j[kj] = '{}'.format(i[ki].isoformat())
                    elif (type(i[ki]) is dt.timedelta):
                        j[kj] = '{}'.format(i[ki].total_seconds())
                    # print ('i[ki], j[kj] == {} {}'.format (i[ki], j[kj]))
            lcl.append(j)

    print (json.dumps(lcl, indent=2,
                      separators=(',', ':'), sort_keys=True))

    return

def print_tablehdr (toprint, fname=None, echo=False,
                    defsep=' ', ordering='sort',
                    strfmt='{:<22s}', intfmt='{:>9s}',
                    fltfmt='{:>14s}', dtfmt='{:<26s}',
                    leadin=['#1 ', '#1N']):
    """
    Print out a header line for a table based on a 
    dict as one line of a columnar table.
    fname == optional file name (e.g. for fits filename)
    echo == True means echo the line to stdout
    defsep == separator. Default = space
    ordering == how to order the columns. 
       Options: 'sort' means alphabetically sorted by key name
                ['col1', 'col2' ...] == ordered list of keys
    {str,int,flt,dt}fmt == string, int, float, datetime formats
    leadin == the header line comment character

    Meant to be used with print_tablerow(), with same ordering arg.
    Call this before first call to print_tablerow() with toprint being the
    first instance that would be a table line. The keys will be used, the
    values ignored.
    """
    nodata = '....'

    tblrow = leadin[0]
    tblcol = leadin[1]

    i = toprint

    # Construct column ordering list
    ordlist = []
    if (type(ordering) is str):
        if (ordering == 'sort'):

            # check if it has the attribute AND if the attribute is callable
            # if ((hasattr(toprint, 'keys') and 
            #      callable(getattr(toprint, 'keys'))):

            if (hasattr(toprint, 'keys')):
                ordlist = ['Filename']
                ordlist.extend(sorted(toprint.keys()))
    elif (type(ordering) is list):
        ordlist = ordering

    # print (ordlist)

    cnum = 0
    for ei in ordlist:
        # if (cnum > 0):

        tblrow += defsep
        tblcol += defsep
        cnum += 1

        try:
            eival = i[ei]
        except:
            eival = nodata

        if (ei == 'Filename'):
            tblrow += strfmt.format(ei)
            tblcol += strfmt.format(str(cnum))
        elif (type(eival) is str):
            tblrow += strfmt.format(ei)
            tblcol += strfmt.format(str(cnum))
        elif (type(eival) is int):
            tblrow += intfmt.format(ei)
            tblcol += intfmt.format(str(cnum))
        elif (type(eival) is float):
            tblrow += fltfmt.format(ei)
            tblcol += fltfmt.format(str(cnum))
        elif (type(eival) is dt.datetime):
            tblrow += dtfmt.format(ei)
            tblcol += dtfmt.format(str(cnum))
        else:
            tblrow += strfmt.format(ei)
            tblcol += strfmt.format(str(cnum))
    tblrow += '\n'
    tblcol += '\n'

    if (echo == True):
        print (tblrow)
        print (tblcol)

    tblrow += tblcol

    return tblrow

def print_tablerow (toprint, fname=None, echo=False,
                    defsep=' ', ordering='sort',
                    strfmt='{:<22s}', intfmt='{:>9d}',
                    fltfmt='{:>14.7f}', dtfmt='{:<26s}',
                    leadin='   ', spacereplace='_'):
    """
    Print out a dict as one line of a columnar table.
    fname == optional file name (e.g. for fits filename)
    echo == True means echo the line to stdout
    defsep == separator. Default = space
    ordering == how to order the columns. 
       Options: 'sort' means alphabetically sorted by key name
                ['col1', 'col2' ...] == ordered list of keys
    {str,int,flt,dt}fmt == string, int, float, datetime formats
    spacereplace == char to replace space in string vals

    Meant to be used with print_tablehdr(), with same ordering arg.
    Call this after call to print_tablehdr().
    """
    nodata = '....'

    tblrow = leadin

    i = toprint

    # Construct column ordering list
    ordlist = []
    if (type(ordering) is str):
        if (ordering == 'sort'):
            if (hasattr(toprint, 'keys')):
                ordlist = ['Filename']
                ordlist.extend(sorted(toprint.keys()))
    elif (type(ordering) is list):
        ordlist = ordering
    # print (ordlist)

    cnum = 0
    for ei in ordlist:
        # if (cnum > 0):

        tblrow += defsep
        cnum += 1

        # check if keyword exists, if not replace w/ nodata string
        try:
            eival = i[ei]
        except:
            eival = nodata

        # replace totally blank values with the nodata string
        try:
            # if (''.join(eival.split()) == ''):
            # if (eival.replace(' ','') == ''):
            if (eival.strip() == ''):
                eival = nodata
        except:
            pass

        if ((ei == 'Filename') and (fname != None)):
            tblrow += strfmt.format(fname)
        elif ((ei == 'Filename') and (fname == None)):
            tblrow += strfmt.format('....')
        elif (type(eival) is str):
            if (spacereplace != None):
                tblrow += strfmt.format(eival.replace(' ', spacereplace))
            else:
                tblrow += strfmt.format(eival)
        elif (type(eival) is int):
            tblrow += intfmt.format(eival)
        elif (type(eival) is float):
            tblrow += fltfmt.format(eival)
        elif (type(eival) is dt.datetime):
            tblrow += dtfmt.format(str(eival.isoformat()))
        else:
            if (spacereplace != None):
                tblrow += strfmt.format(eival.replace(' ', spacereplace))
            else:
                tblrow += strfmt.format(eival)

    tblrow += '\n'

    if (echo == True):
        print (tblrow)

    return tblrow

#------------------------------------------------------------------------
# URL query routines - get_url, pica_vo_cone
def pica_vo_cone (ra, dec, sr=0.1, cat='GAIA-DR2', verb=1, echo=False):
    """
    Simple query test to the pica/vo_cone service.
    Requires at least RA, Dec of pointing center, both in degrees.
    SR is the cone radius, also in degrees.
    cat is the catalogue to select from. Options are GAIA-DR2, GAIA-DR1, 
    NOMAD, USNO-B1, USNO-A2, UCAC-2, UCAC-3, UCAC-4, URAT-1, ACT.
    """

    urlpath = 'http://astrometry.mit.edu/cgi-bin/vo_cone6.cgi'

    data = {}
    data['CAT']  = cat
    data['RA']   = ra
    data['DEC']  = dec
    data['SR']   = sr
    data['VERB'] = verb

    ret_data = get_url(urlpath, appdata=data, echo=echo)

    return ret_data

def get_url (urlpath, appdata=None, ntries=1, socdeftime=20.0, echo=False):
    """
    Construct a simple, or GET style request for data to a URL.
    appdata has any appended args for the GET query.

    urlpath is the basic URL of the page requested

    appdata == appended data for a GET style request. 
    If appdata == None, then assume just a simple URL request.

    ntries is the number of times to try the connection. Default is 1.

    After ntries, if the connection times out or fails, this will just
    return None.

    The retrieved data are returned in byte array format. That makes
    it possible for this to handle both text and binary. The calling
    routine will need to convert as appropriate.
    """

    # make sure the socket default time out is not None. Set to
    # 20.0sec as a nominal default.  Not clear if this is the timeout
    # for the entire connection, or just the timeout when trying to
    # connect.

    if (socket.getdefaulttimeout() == None):
        socket.setdefaulttimeout(socdeftime)

    url = urlpath
    if (appdata != None):
        data = appdata
        url_values = urllib.parse.urlencode(data)
        if (echo == 'Values'):
            print('{}'.format(url_values))  # The order may differ
                                            # from below.
    
        full_url = url + '?' + url_values

    else:
        full_url = url

    for tcount in range(1,ntries+1):
        try:
            with urllib.request.urlopen(full_url) as response:
                ret_data = response.read()

        # except OSError as e:
        # socket.timeout is a subclass of OSError.
        except socket.timeout as e:
            print('URL request failed. {}. Try {} of {}'.\
                          format(e, tcount, ntries))
            if (tcount >= ntries):
                return None
            
        except URLError as e:
            if hasattr(e, 'reason'):
                print('URL request failed. Reason: {}. Try {} of {}'.\
                          format(e.reason, tcount, ntries))
            elif hasattr(e, 'code'):
                print('URL request failed. Code: {}. Try {} of {}'.\
                          format(e.code, tcount, ntries))
            if (tcount >= ntries):
                return None

        else:
            # everything is fine, and break out of the loop
            if (echo == True):
                print ('Connected OK.')
            break

    if (echo != False):
        j = ret_data.splitlines()
        for i in j:
            print ('{}'.format(i))

    return ret_data

def get_url2 (urlpath, appdata=None, hdrinfo=None, g_or_p='GET',
              ntries=1, socdeftime=20.0, echo=False):
    """
    Construct a simple, or GET or POST style request for data to a URL.
    appdata has any appended args for the GET query.

    urlpath is the basic URL of the page requested

    appdata == appended data for a GET or POST style request. 
    If appdata == None, then assume just a simple URL request.
    appdata should be a dictionary. The keys and values get translated to 
    key=value& for each pair.

    hdrinfo == possible HTTP header information, if needed for querying.
    hdrinfo should be a dictionary. The keys and values get translated to 
    key=value& for each pair.

    ntries is the number of times to try the connection. Default is 1.

    After ntries, if the connection times out or fails, this will just
    return None.

    g_or_p allows the caller to specify whether to construct a GET or POST
    query.

    The retrieved data are returned in byte array format. That makes
    it possible for this to handle both text and binary. The calling
    routine will need to convert as appropriate.
    """

    # make sure the socket default time out is not None. Set to
    # 20.0sec as a nominal default.  Not clear if this is the timeout
    # for the entire connection, or just the timeout when trying to
    # connect.

    if (socket.getdefaulttimeout() == None):
        socket.setdefaulttimeout(socdeftime)

    # The basic URL
    url = urlpath

    # Any header information
    if ((hdrinfo != None) and (hdrinfo != {})):
        hdr = hdrinfo
        if (echo == 'Values'):
            print('{}'.format(hdr))  # The order may differ from below.
    else:
        hdr = {}
            
    # Any GET or POST data
    if (appdata != None):
        data = appdata
        url_values = urllib.parse.urlencode(data)
        
        if (echo == 'Values'):
            print('{}'.format(url_values))  # The order may differ
                                            # from below.

        full_url = url + '?' + url_values

    else:
        full_url = url

    if ((g_or_p == 'GET') or (g_or_p == None)):
        req = urllib.request.Request(full_url, data=None, headers=hdr)
        
    elif (g_or_p == 'POST'):
        url_b_values = url_values.encode('ascii')
        req = urllib.request.Request(url, data=url_b_values, headers=hdr)
        
    for tcount in range(1,ntries+1):
        try:
            with urllib.request.urlopen(req) as response:
                ret_data = response.read()

        # except OSError as e:
        # socket.timeout is a subclass of OSError.
        except socket.timeout as e:
            print('URL request failed. {}. Try {} of {}'.\
                          format(e, tcount, ntries))
            if (tcount >= ntries):
                return None
            
        except URLError as e:
            if hasattr(e, 'reason'):
                print('URL request failed. Reason: {}. Try {} of {}'.\
                          format(e.reason, tcount, ntries))
            elif hasattr(e, 'code'):
                print('URL request failed. Code: {}. Try {} of {}'.\
                          format(e.code, tcount, ntries))
            if (tcount >= ntries):
                return None

        else:
            # everything is fine, and break out of the loop
            if (echo == True):
                print ('Connected OK.')
            break

    if (echo != False):
        j = ret_data.splitlines()
        for i in j:
            print ('{}'.format(i))

    return ret_data

