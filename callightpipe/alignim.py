import argparse
import astropy.io.fits as pyfits
import glob
import astroalign as aa

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="""
  This program aligns an input list
  of FITS images specified by a path.
  """, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument("-outprefix", default="aligned_",
    help="prefix to prepend to each file name to make output filename ")
  parser.add_argument("-path", default="tobealigned?.fit", 
    help="input path for input files")
  
  args = parser.parse_args()

  path = args.path
  outputprefix = args.outprefix


  count = 1
  for filename in glob.glob(path):
    print(filename, outputprefix+filename)
    if (count == 1):
      imgtarget =  pyfits.getdata(filename)
      imgtarget = imgtarget.astype(float)
      hdu = pyfits.PrimaryHDU(imgtarget)
      hdul = pyfits.HDUList([hdu])
      hdul.writeto(outputprefix + filename)
    else:
      img =  pyfits.getdata(filename)
      img = img.astype(float)
      registered_image, footprint = aa.register(img, imgtarget)
      hdu = pyfits.PrimaryHDU(registered_image)
      hdul = pyfits.HDUList([hdu])
      hdul.writeto(outputprefix + filename)
    count = count + 1
