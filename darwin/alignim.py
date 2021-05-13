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
import astroalign as aa

imgtarget =  pyfits.getdata("qsi-0001trk.fit")
path = "qsi-*trk.fit"
count = 1
for filename in glob.glob(path):

    img =  pyfits.getdata(filename)

    registered_image, footprint = aa.register(img, imgtarget)

    hdu = pyfits.PrimaryHDU(registered_image)
    hdul = pyfits.HDUList([hdu])
    hdul.writeto('new' + str(count) + '.fits')
    count = count + 1
