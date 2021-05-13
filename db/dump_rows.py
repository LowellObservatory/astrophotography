import sqlite3
import glob, os, sys

conn = None
try:
  conn = sqlite3.connect("../../db/PW17QSI.db")
except Error as e:
  print(e)

cur = conn.cursor()
date = "2021-03-09"
cur.execute("SELECT exptime,dateobs FROM images  \
                 where dateobs >= date(?) \
                 and dateobs <  date(?, '+1 day') limit 100 ",(date, date,))

rows = cur.fetchall()

for row in rows:
  print(row)
