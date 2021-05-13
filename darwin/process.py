from pathlib import Path

from matplotlib import pyplot as plt
import numpy as np

from astropy import units as u
import ccdproc


ccddark = ccdproc.CCDData.read('20210227-0002D180.fit', unit="adu")
ccdbias = ccdproc.CCDData.read('20210227-0006Bias.fit', unit="adu")
ccdred = ccdproc.CCDData.read('20210227-0015R.fit', unit="adu")
ccdgreen = ccdproc.CCDData.read('20210227-0015G.fit', unit="adu")
ccdblue = ccdproc.CCDData.read('20210227-0015B.fit', unit="adu")
ccdredflat = ccdproc.CCDData.read('20210227-0018FlatRed.fit', unit="adu")
ccdgreenflat = ccdproc.CCDData.read('20210227-0018FlatGreen.fit', unit="adu")
ccdblueflat = ccdproc.CCDData.read('20210227-0018FlatBlue.fit', unit="adu")

#master_bias = ccdproc.CCDData(ccdbias,unit=u.electron)

red_flat_bias_subtracted = ccdproc.subtract_bias(ccdredflat, ccdbias)
green_flat_bias_subtracted = ccdproc.subtract_bias(ccdgreenflat, ccdbias)
blue_flat_bias_subtracted = ccdproc.subtract_bias(ccdblueflat, ccdbias)

red_dark_subtracted = ccdproc.subtract_dark(ccdred, ccddark,
    dark_exposure=180*u.second, data_exposure=180*u.second,)
green_dark_subtracted = ccdproc.subtract_dark(ccdgreen, ccddark,
    dark_exposure=180*u.second, data_exposure=180*u.second,)
blue_dark_subtracted = ccdproc.subtract_dark(ccdblue, ccddark,
    dark_exposure=180*u.second, data_exposure=180*u.second,)

final_red = ccdproc.flat_correct(red_dark_subtracted, red_flat_bias_subtracted)
final_green = ccdproc.flat_correct(green_dark_subtracted, green_flat_bias_subtracted)
final_blue = ccdproc.flat_correct(blue_dark_subtracted, blue_flat_bias_subtracted)

final_red.write('final_red.fit')
final_green.write('final_green.fit')
final_blue.write('final_blue.fit')