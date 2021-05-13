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

path = "new*.fits"
for filename in glob.glob(path):

    img =  pyfits.getdata(filename)[0:600, 0:600]

    limg = np.log2(img)
    limg = np.flipud(limg)
    limg = limg / limg.max()
    low = np.percentile(limg, 0.05)
    high = np.percentile(limg, 99.8)
    opt_img  = skie.exposure.rescale_intensity(limg, in_range=(low,high))

    mim.imsave(filename + '.png', opt_img, cmap="gray")
