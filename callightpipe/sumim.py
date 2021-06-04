import os
import sys
import argparse
import numpy as np
import astropy.io.fits as pyfits
import glob

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="""
  This program produces a summed FITS image from an input list
  of FITS images specified by a path.
  """, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("-out", default="summed_image.fit",
    help="output file name for summed FITS file")
  parser.add_argument("-path", default="final_red?.fit", 
    help="input path for input files")
  
  args = parser.parse_args()

  path = args.path
  outputfilename = args.out

  print(outputfilename, path)
  
  count = 1
  for filename in glob.glob(path):

      print(filename)
      img =  pyfits.getdata(filename)
      if (count == 1):
        imgout = img
      else:
        imgout = imgout + img

      count = count + 1

  hdu = pyfits.PrimaryHDU(imgout)
  hdul = pyfits.HDUList([hdu])
  hdul.writeto(outputfilename)
