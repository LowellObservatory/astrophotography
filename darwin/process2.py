from pathlib import Path

from matplotlib import pyplot as plt
import numpy as np

from astropy import units as u
import ccdproc

from astropy.io import fits


hdu_dark = fits.open('20210320-0011d2.fit')
hdu_red1 = fits.open('20210320-0001B.fit')
hdu_red2 = fits.open('20210320-0002B.fit')
hdu_red3 = fits.open('20210320-0003B.fit')

dark_data = hdu_dark[0].data
red1_data = hdu_red1[0].data
red2_data = hdu_red2[0].data
red3_data = hdu_red3[0].data

red1_data = red1_data - dark_data
red2_data = red2_data - dark_data
red3_data = red3_data - dark_data

final = red1_data + red2_data + red3_data

outfile = 'blue_final.fit'

hdu = fits.PrimaryHDU(final)
hdu.writeto(outfile, overwrite=True)

