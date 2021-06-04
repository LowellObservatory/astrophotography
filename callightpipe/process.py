import argparse
from pathlib import Path
import numpy as np
from astropy import units as u
import ccdproc

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="""
  This program calibrates a "light" FITS file.
  """, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("-out", default="calibrated.jpg",
    help="output file name for calibrated image (FITS))")
  parser.add_argument("-input", default="20210519-0002R.fit", 
    help="input FITS file to calibrate")
  parser.add_argument("-dark", default="Dark.fit", 
    help="input dark FITS file that still contains bias")
  parser.add_argument("-bias", default="bias.fit", 
    help="input bias FITS file (will be subtracted from flat")
  parser.add_argument("-flat", default="Flat.fit", 
    help="input flat (FITS file) (still contains bias)")
  
  args = parser.parse_args()

  infile = args.input
  dark = args.dark
  bias = args.bias
  flat = args.flat
  outputfilename = args.out

  print(outputfilename, infile, dark, bias, flat)

  ccdin = ccdproc.CCDData.read(infile, unit="adu")
  ccddark = ccdproc.CCDData.read(dark, unit="adu")
  ccdbias = ccdproc.CCDData.read(bias, unit="adu")
  ccdflat = ccdproc.CCDData.read(flat, unit="adu")

  flat_bias_subtracted = ccdproc.subtract_bias(ccdflat, ccdbias)

  in_dark_subtracted = ccdproc.subtract_dark(ccdin, ccddark,
      dark_exposure=180*u.second, data_exposure=180*u.second,)

  final_im = ccdproc.flat_correct(in_dark_subtracted, flat_bias_subtracted)

  final_im.write(outputfilename)
