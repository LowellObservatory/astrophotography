from astropy.io import fits
import argparse
import os
import glob

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="""
  This program produces a list of images defined by a path
  along with various useful keywords from the FITS header of
  the images.
  """, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("-path", default="*.fit",
    help="input path for input files")

  args = parser.parse_args()

  path = args.path

  print(path)


  for filename in glob.glob(path):
    if filename.endswith(".fit"):
      hdul = fits.open(filename)
      print(filename, end='')
      print('        ', end='')
      print(hdul[0].header['EXPTIME'], end='')
      print('        ', end='')
      try:
        print(hdul[0].header['FILTER'], end='')
        print('                ', end='')
      except KeyError:
        print("no filter", end='')
        print('                ', end='')
      print(hdul[0].header['IMAGETYP'], end='')
      print('        ', end='')
      print(hdul[0].header['NAXIS1'], end='')
      print('')
    else:
      continue
