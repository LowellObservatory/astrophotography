
# Usage: darks_ave.py date

import sqlite3
import glob, os, sys
import cal_tools

# Usage: average_darks.py date

def get_dark_list(date):
  """ Find all the darks in the database from the supplied date.
      If a date isn't supplied, find the most recent dark in the
      database and then find all the darks in the database taken
      on the date of that most recent dark.

      Find the exposure times for all the darks, make a list of exp times.
      For each exposure time in the list:
        Calculate an average dark from the set of darks with this exposure time.
      Place the average darks in the "current_cal_files" directory

      Argument: a date or "None"
      Return: a list of files with path."""

  # Get the path to the database.
  this_path, this_file = os.path.split(os.path.abspath(__file__))
  db_path = this_path + "/../../db/PW17QSI.db"

  # Connect to the database and get a cursor.
  conn = None
  try:
    conn = sqlite3.connect(db_path)
  except Error as e:
    print(e)

  cur = conn.cursor()

  if (date == None):
    # They didn't supply an argument to get most recent data.
    cur.execute(
    "SELECT dateobs FROM images WHERE imagetyp='Dark Frame' \
     ORDER BY date(dateobs) DESC Limit 1")

    rows = cur.fetchall()
    date = rows[0][0]
    # print(date)

    cur.execute("select dateobs,path,exptime FROM images \
    WHERE imagetyp='Dark Frame' \
      AND dateobs >= date(?) \
      AND dateobs <  date(?, '+1 day')",(date, date,))
    rows = cur.fetchall()

  else:
    # The user supplied a date, find all biases on that date.

    cur.execute("select dateobs,path,exptime FROM images \
    WHERE imagetyp='Dark Frame' \
      AND dateobs >= date(?) \
      AND dateobs <  date(?, '+1 day')",(date, date,))
    rows = cur.fetchall()

  # Return a list of tuples, each containing the path and the exptime.
  return_list = []
  for row in rows:
    return_list.append((this_path + "/../../data/" + row[1], row[2]))

  return (return_list)

def compute_ave_darks(dark_dict, this_path):
  # For each entry in the dictionary, which represents an exposure time, do.
  for key in dark_dict:
    exp = key
    exp_list = dark_dict[key]
    im_list = []
    for img in exp_list:
      im_list.append(img[0])

    # Calculate an average dark from this set of darks.
    # Place the average bias in the "../../currcal" directory
    currcal_path = this_path + "/../../currcal/"
    output_file = currcal_path + "average_dark_" + str(int(exp)) + ".fit"
    print("writing average_dark_" + str(int(exp)) + ".fit")
    cal_tools.average_im(im_list, output_file)

if __name__ == "__main__":
  nargs = len(sys.argv)
  if (nargs == 2):
    date = sys.argv[1]
  else:
    date = None

  # Get the path to the database
  this_path, this_file = os.path.split(os.path.abspath(__file__))
  db_path = this_path + "/../../db/PW17QSI.db"
  
  # Get the list of dark frames to use.
  input_list = get_dark_list(date)

  # Now we have all the dark frames from the supplied cal day or
  # the most recent cal day.  We have the (path,exptime) tuple for each.

  # Debug print....
  #for item in input_list:
  #  print(item)

  # Calculate an average darks from this set of darks.
  # Place the average darks in the "../../currcal" directory
  currcal_path = this_path + "/../../currcal/"

  # Group the darks by exposure time. Output is a dictionary.
  # {exptime1:[(),(),()], exptime2:[()()()]}
  output = {}
  for x, y in input_list:
    if y in output:
        output[y].append((x, y))
    else:
        output[y] = [(x, y)]

  compute_ave_darks(output, this_path)



