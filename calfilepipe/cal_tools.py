import os
import sys
from PIL import Image
import argparse
import matplotlib.pyplot as mpl
import matplotlib.image as mim
import numpy as np
import astropy.io.fits as pyfits
import skimage.morphology as morph
import skimage.exposure as skie
import scipy.misc
import glob

def median_im(input_list, output_file):
  arrays = []
  for filename in input_list:

    img = pyfits.getdata(filename)
    arrays.append(img)

  data_stack = np.stack(arrays)
  data_median = np.median(data_stack, axis=0)

  hdu = pyfits.PrimaryHDU(data_median)
  hdul = pyfits.HDUList([hdu])
  hdul.writeto(output_file, overwrite=True)


def average_im(input_list, output_file):
  arrays = []
  for filename in input_list:

    img = pyfits.getdata(filename)
    arrays.append(img)

  data_stack = np.stack(arrays)
  data_average = np.average(data_stack, axis=0)

  hdu = pyfits.PrimaryHDU(data_average)
  hdul = pyfits.HDUList([hdu])
  hdul.writeto(output_file, overwrite=True)
