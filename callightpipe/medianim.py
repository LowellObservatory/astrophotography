import argparse
import numpy as np
import astropy.io.fits as pyfits
import glob

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="""
  This program produces a median FITS image from an input list
  of FITS images specified by a path.
  """, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("-out", default="median_image.fit",
    help="output file name for median FITS file")
  parser.add_argument("-path", default="*Dark.fit", 
    help="input path for input files")
  
  args = parser.parse_args()

  path = args.path
  outputfilename = args.out

  print(outputfilename, path)

  arrays = []
  for filename in glob.glob(path):
    print(filename)
    img =  pyfits.getdata(filename)
    arrays.append(img)

  median_stack = np.stack(arrays)
  median = np.median(median_stack, axis=0)

  hdu = pyfits.PrimaryHDU(median)
  hdul = pyfits.HDUList([hdu])
  hdul.writeto(outputfilename)
