
import sqlite3
import numpy as np
from astropy.io import fits
import glob, os, sys

def create_images_table(conn):

  conn.execute(
      '''create table if not exists images
           ( name           text   not null,
             path           text   not null,
             thumbpath      text,
             naxis          int,
             naxis1         int,
             naxis2         int,
             dateobs        text,
             exptime        real,
             ccdtemp        real,
             xbinning       int,
             ybinning       int,
             xorgsubf       int,
             yorgsubf       int,
             readoutm       text,
             isospeed       text,
             filter         text,
             imagetyp       text,
             traktime       real,
             egain          real,
             focuspos       int,
             object         text,
             objctra        text,
             objctdec       text,
             objctha        text,
             jd             real,
             jdhelio       real);''')


if __name__ == "__main__":

  n = len(sys.argv)
  if (n != 2):
    print("usage: ingest_fits directory")
    sys.exit(2)

  this_dir = "../../data/" + sys.argv[1]

  # Get the path to the database.
  this_path, this_file = os.path.split(os.path.abspath(__file__))
  db_path = this_path + "/../../db/PW17QSI.db"
  print(db_path)

  conn = sqlite3.connect(db_path)
  cursor = conn.cursor()

  # Create table if it does not exist.
  create_images_table(conn)

  # For each FITS file (extension = .fit) in the specified directory.
  # Read the header and extract some keywords, read the thumbnail file.
  # Add the file to the database.
  count = 0
  for infile in glob.glob(this_dir + "/*.fit"):
    print(infile)
    file_base_name=os.path.basename(infile)
    print (file_base_name)
    file_base_no_ext, ext = os.path.splitext(file_base_name)
    print (file_base_no_ext)
    dir_base_name=os.path.basename(this_dir)
    myfile, ext = os.path.splitext(infile)
    thumbfile = myfile + ".png"
    #path = os.path.abspath(infile)
    #thumbpath = os.path.abspath(thumbfile)
    path = dir_base_name + "/" + file_base_no_ext + ".fit"
    thumbpath = dir_base_name + "/" + file_base_no_ext + ".png"

    hdul = fits.open(infile)
    naxis = hdul[0].header["NAXIS"]
    naxis1 = hdul[0].header["NAXIS1"]
    naxis2 = hdul[0].header["NAXIS2"]
    dateobs = hdul[0].header["DATE-OBS"]
    print("do = " + dateobs)
    exptime = hdul[0].header["EXPTIME"]
    try:
      ccdtemp = hdul[0].header["CCD-TEMP"]
    except KeyError:
      ccdtemp = "NONE"
    xbinning = hdul[0].header["XBINNING"]
    ybinning = hdul[0].header["YBINNING"]
    xorgsubf = hdul[0].header["XORGSUBF"]
    yorgsubf = hdul[0].header["YORGSUBF"]
    readoutm = hdul[0].header["READOUTM"]
    isospeed = hdul[0].header["ISOSPEED"]
    try:
      filt = hdul[0].header["FILTER"]
    except KeyError:
      filt = "NONE"
    imtype = hdul[0].header["IMAGETYP"]
    try:
      traktime = hdul[0].header["TRAKTIME"]
    except KeyError:
      traktime = "NONE"
    egain = hdul[0].header["EGAIN"]
    try:
      focuspos = hdul[0].header["FOCUSPOS"]
    except KeyError:
      focuspos = "NONE"
    try:
      objectX = hdul[0].header["OBJECT"]
    except KeyError:
      objectX = "NONE"
    try:
      objctra = hdul[0].header["OBJCTRA"]
    except KeyError:
      objctra = "NONE"
    try:
      objctdec = hdul[0].header["OBJCTDEC"]
    except KeyError:
      objctdec = "NONE"
    try:
      objctha = hdul[0].header["OBJCTHA"]
    except KeyError:
      objctha = "NONE"
    jd = hdul[0].header["JD"]
    jdhelio = hdul[0].header["JD-HELIO"]

    hdul.close()

    sqcommand = "insert into images ( \
      name, path, thumbpath,  \
      naxis, naxis1, naxis2, \
      dateobs, exptime, ccdtemp, \
      xbinning, ybinning, \
      xorgsubf, yorgsubf, \
      readoutm, isospeed, \
      filter, imagetyp, traktime, \
      egain, focuspos, object, \
      objctra, objctdec, objctha, \
      jd, jdhelio) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, \
      ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? );"

    intuple = (file_base_name, path, thumbpath, naxis, naxis1, naxis2, \
      dateobs, exptime, ccdtemp, xbinning, ybinning, \
      xorgsubf, yorgsubf, readoutm, isospeed, filt, \
      imtype, traktime, egain, focuspos, objectX, \
      objctra, objctdec, objctha, jd, jdhelio)

    # Check to see if this file is already in the database.
    cursor.execute("select * from images where name=? and path=?", (file_base_name,path,))
    rows = cursor.fetchall()
    if (len(rows) == 0):
      cursor.execute(sqcommand, intuple)
      conn.commit()

    count = count + 1
    #if (count > 20): break

  conn.close()


