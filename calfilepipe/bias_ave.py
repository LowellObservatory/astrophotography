import sqlite3
import glob, os, sys
import cal_tools

# Usage: average_bias.py date

def get_file_list(date):
  """ Find all the biases in the database from the supplied date.
      If a date isn't supplied, find the most recent bias in the
      database and then find all the biases in the database taken
      on the date of that most recent bias.

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
    "SELECT dateobs FROM images WHERE imagetyp='Bias Frame' \
     ORDER BY date(dateobs) DESC Limit 1")

    rows = cur.fetchall()
    date = rows[0][0]
    # print(date)

  # Now we have the date, either supplied or most recent.
  # get all the bias frames from that date along with the binning factor.
  cur.execute("select dateobs,path,xbinning FROM images \
    WHERE imagetyp='Bias Frame' \
    AND dateobs >= date(?) \
    AND dateobs <  date(?, '+1 day')",(date, date,))
  rows = cur.fetchall()

  return_list = []
  for row in rows:
    return_list.append((this_path + "/../../data/" + row[1], row[2]))

  return (return_list)

def compute_median_biases(bias_dict, this_path):
  # For each entry in the dictionary, which represents a binning, do.
  for key in bias_dict:
    binning = key
    binning_list = bias_dict[key]
    im_list = []
    for img in binning_list:
      im_list.append(img[0])

    # Calculate a median bias from this set of biases.
    # Place the median bias in the "../../currcal" directory
    output_file = this_path + "median_bias_" + str(int(binning)) + ".fit"
    print("writing median_bias" + str(int(binning)) + ".fit")
    cal_tools.median_im(im_list, output_file)


if __name__ == "__main__":
  nargs = len(sys.argv)
  if (nargs == 2):
    date = sys.argv[1]
  else:
    date = None

  # Get the path to the database
  this_path, this_file = os.path.split(os.path.abspath(__file__))
  db_path = this_path + "/../../db/PW17QSI.db"
  
  # Get the list of bias frames to use.
  input_list = get_file_list(date)

  # Now we have all the bias frames from the supplied cal day or
  # the most recent cal day.

  # Debug print....
  for item in input_list:
    print(item)

  # Group the biases by binning. Output is a dictionary.
  # {binning1:[(),(),()], binning2:[()()()]}
  bias_dict = {}
  for x, y in input_list:
    if y in bias_dict:
        bias_dict[y].append((x, y))
    else:
        bias_dict[y] = [(x, y)]

  currcal_path = this_path + "/../../currcal/"

  # Calculate an average bias from each binning set of biases.
  # Place the average biases in the "../../currcal" directory
  compute_median_biases(bias_dict, currcal_path)


