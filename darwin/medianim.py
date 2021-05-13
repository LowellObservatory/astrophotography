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

dark_stack =  pyfits.getdata("new1.fits")
path = "new*.fits"
count = 1
arrays = []
for filename in glob.glob(path):

    img =  pyfits.getdata(filename)
    arrays.append(img)
#    np.stack((dark_stack, img), axis=-1)

dark_stack = np.stack(arrays)
dark_median = np.median(dark_stack, axis=0)

hdu = pyfits.PrimaryHDU(dark_median)
hdul = pyfits.HDUList([hdu])
hdul.writeto('medianimage.fits')
