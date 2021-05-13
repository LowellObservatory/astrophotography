from astropy.io import fits
import os

#directory = os.fsencode("02-24-2021")

for filename in os.listdir("03-20-2021"):
#     filename = os.fsdecode(file)
     if filename.endswith(".fit"):
         file_with_path = os.path.join("03-20-2021", filename)
         hdul = fits.open(file_with_path)
         #if (hdul[0].header['IMAGETYP'] == 'Dark Frame'):
         #if (hdul[0].header['IMAGETYP'] == 'Bias Frame'):
         #if (hdul[0].header['IMAGETYP'] == 'Flat Field'):
         #if (hdul[0].header['IMAGETYP'] == 'Light Frame'):
         if (True):
           print(filename, end='')
           print('        ', end='')
           print(hdul[0].header['EXPTIME'], end='')
           print('        ', end='')
           try:
               print(hdul[0].header['FILTER'], end='')
               print('                ', end='')
           except KeyError:
               print("no filter", end='')
               print('                ', end='')
           print(hdul[0].header['IMAGETYP'])
           print('        ', end='')
           print(hdul[0].header['NAXIS1'], end='')
           print('        ', end='')
         continue
     else:
         continue


