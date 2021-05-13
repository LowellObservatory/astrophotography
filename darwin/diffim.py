import os
import sys
from PIL import Image
import argparse
import matplotlib.pyplot as mpl
import matplotlib.image as mim
import numpy as np
import astropy.io.fits as pyfits
import scipy.misc
import glob

dark_data =  pyfits.getdata("20210226-0001D180.fit")
light_data = pyfits.getdata("20210226-0003R.fit")

result = light_data-dark_data
super_threshold_indices = result > 65000
result[super_threshold_indices] = 0

hdu = pyfits.PrimaryHDU(result)
hdul = pyfits.HDUList([hdu])
hdul.writeto('dark_sub_003R.fits')
