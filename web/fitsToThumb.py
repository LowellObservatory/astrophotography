from skimage.io import imread, imsave
from skimage.transform import rescale, resize, downscale_local_mean
from skimage.exposure import (rescale_intensity, adjust_log, equalize_hist,
    equalize_adapthist)
import numpy as np
from astropy.io import fits
import glob, os, sys

if __name__ == "__main__":

  n = len(sys.argv)
  if (n != 2):
    print("usage: fitsToThumb directory")
    sys.exit(2)

  this_dir = sys.argv[1]

  # For each FITS file (extension = .fit) in the specified directory.
  count = 0
  for infile in glob.glob(this_dir + "/*.fit"):
    print(infile)
    file, ext = os.path.splitext(infile)
    hdul = fits.open(infile)
    width = hdul[0].header["NAXIS1"]
    image_data = hdul[0].data
    hdul.close()

    base = os.path.splitext(file)[0]
    v_min, v_max = np.percentile(image_data, (0.2, 98.0))
    image_data = rescale_intensity(image_data, in_range=(v_min, v_max),
        out_range=(0, 256))
    fraction = 300./width
    image_data = rescale(image_data, fraction)
    image_data = image_data.astype(np.uint8)
    imsave(file + ".png", image_data)
    count = count + 1
  #  if (count > 10): break

