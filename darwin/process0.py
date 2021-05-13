from pathlib import Path

from matplotlib import pyplot as plt
import numpy as np

from astropy import units as u
import ccdproc


ccddark = ccdproc.CCDData.read('20210320-0011d2.fit', unit="adu")
ccdred = ccdproc.CCDData.read('20210320-0003R.fit', unit="adu")

red_dark_subtracted = ccdproc.subtract_dark(ccdred, ccddark,
    dark_exposure=180*u.second, data_exposure=180*u.second,)

red_dark_subtracted.write('test.fit')
