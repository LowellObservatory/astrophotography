import argparse
from PIL import Image
import numpy as np
import astropy.io.fits as pyfits
from skimage.transform import rescale, resize, downscale_local_mean
from skimage.exposure import (rescale_intensity, adjust_log,
    equalize_hist, equalize_adapthist)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="""
  This program combines three monochrome FITS images into a color jpeg.
  """, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("-out", default="color_composite.jpg",
    help="output file name for color composite jpeg file")
  parser.add_argument("-R", default="red.fit", 
    help="input FITS file for red channel")
  parser.add_argument("-G", default="green.fit", 
    help="input FITS file for green channel")
  parser.add_argument("-B", default="blue.fit", 
     help="input FITS file for blue channel")
  parser.add_argument("--log", default=False, type=bool,
    help="Should we take the log of each channel?")
  parser.add_argument("-prcntmin", default=0.4, type=float,
    help="min percentile when not taking log")
  parser.add_argument("-prcntmax", default=99.9, type=float,
    help="max percentile when not taking log")
  parser.add_argument("-prcntminlog", default=20.0, type=float,
    help="min percentile when taking log")
  parser.add_argument("-prcntmaxlog", default=99.9, type=float,
    help="max percentile when taking log")
  
  args = parser.parse_args()

  takelog = args.log
  redfile = args.R
  greenfile = args.G
  bluefile = args.B
  percentilemin = args.prcntmin
  percentilemax = args.prcntmax
  percentileminlog = args.prcntminlog
  percentilemaxlog = args.prcntmaxlog
  outputfilename = args.out

  print(outputfilename, redfile,greenfile, bluefile, takelog,
    percentilemin, percentilemax, percentileminlog, percentilemaxlog)

  # Get the size of the images.
  naxis1 = pyfits.getheader(redfile)['NAXIS1']
  naxis2 = pyfits.getheader(redfile)['NAXIS2']

  # Read the data into arrays.
  imgR =  pyfits.getdata(redfile)
  imgG =  pyfits.getdata(greenfile)
  imgB =  pyfits.getdata(bluefile)

  # If directed to do so, take log of all three arrays.
  if(takelog):
    imgR[imgR<0] = .01
    imgR = np.log(imgR)
    imgG[imgG<0] = .01
    imgG = np.log(imgG)
    imgB[imgB<0] = .01
    imgB = np.log(imgB)

  # Initialize the output array.
  rgbArray = np.zeros((naxis2, naxis1, 3), 'uint8')

  # For each of the R, G, and B arrays, calculate the min and
  # max values to be used for (linear) scaling.  Then scale the arrays
  # using these values.
  if (takelog):
    v_min, v_max = np.percentile(imgR, (percentileminlog, percentilemaxlog))
  else:
    v_min, v_max = np.percentile(imgR, (percentilemin, percentilemax))
  imgR = rescale_intensity(imgR, in_range=(v_min, v_max),
    out_range=(0, 255.999))
  if (takelog):
    v_min, v_max = np.percentile(imgG, (percentileminlog, percentilemaxlog))
  else:
    v_min, v_max = np.percentile(imgG, (percentilemin, percentilemax))
  imgG = rescale_intensity(imgG, in_range=(v_min, v_max),
    out_range=(0, 255.999))
  if (takelog):
    v_min, v_max = np.percentile(imgB, (percentileminlog, percentilemaxlog))
  else:
    v_min, v_max = np.percentile(imgB, (percentilemin, percentilemax))
  imgB = rescale_intensity(imgB, in_range=(v_min, v_max),
    out_range=(0, 255.999))

  # Update the output array using the scaled R, G, B arrays.
  rgbArray[..., 0] = imgR
  rgbArray[..., 1] = imgG
  rgbArray[..., 2] = imgB

  # Write the array out as a JPEG file.
  img = Image.fromarray(rgbArray)
  img.save(outputfilename)
