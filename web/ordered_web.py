import numpy as np
from astropy.io import fits
import glob, os, sys
import sqlite3

n = len(sys.argv)
if (n != 2):
  print("usage: ordered_web directory")
  sys.exit(2)

this_dir = sys.argv[1]


# open output file.
with open(this_dir + '/index.html', 'w') as fp:
  fp.write('''<!doctype html>\n
<html lang="en">
<head>
  <meta charset="utf-8">\n
  <title>index of images</title>\n
  <link rel="stylesheet" href="styles.css">\n
</head>\n
<body>\n''' )
  fp.write('<div class="grid-container">\n')
  count = 0
  for infile in glob.glob(this_dir + "/*.fit"):
      file, ext = os.path.splitext(infile)
      base = os.path.basename(file)
      thumb_image = base + ".png"
      hdul = fits.open(infile)
      exptime = hdul[0].header["EXPTIME"]
      try:
        filt = hdul[0].header["FILTER"]
      except KeyError:
        filt = "NONE"
      imtype = hdul[0].header["IMAGETYP"]
      datetime = hdul[0].header["DATE-OBS"]
      width = hdul[0].header["NAXIS1"]
      hdul.close()

      fp.write('<div class="grid-item">\n')
      fp.write('<figure>\n')
      fp.write("  <img src=\"{}\"/>\n".format(thumb_image))
      fp.write("  <figcaption>file: {}</figcaption>\n".format(file))
      fp.write("  <figcaption>width: {}</figcaption>\n".format(width))
      fp.write("  <figcaption>datetime: {}</figcaption>\n".format(datetime))
      fp.write("  <figcaption>exptime: {}</figcaption>\n".format(exptime))
      fp.write("  <figcaption>filter: {}</figcaption>\n".format(filt))
      fp.write("  <figcaption>image type: {}</figcaption>\n".format(imtype))
      fp.write('</figure>\n')
      fp.write('''</div>''')

      count = count + 1
      #if (count > 10): break

  fp.write('''</div>''')
  fp.write('''</body>\n
</html>\n''')
