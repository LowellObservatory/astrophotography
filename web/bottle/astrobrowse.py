#!/usr/bin/python3
import sqlite3
from bottle import route, static_file, run, debug, template, url
import bottle
import os
from os import listdir
from os.path import isdir, join

app = application = bottle.Bottle()

@app.route('/data/<filepath:path>', name='data')
def server_static(filepath):
    return bottle.static_file(filepath, root='./data')

@app.route('/assets/<filepath:path>', name='assets')
def server_static(filepath):
    return bottle.static_file(filepath, root='./assets')

@app.route('/astrobrowse')
@app.route('/astrobrowse/<date>')
def astro_browse(date='UT20210227'):
    # Get a list of the daily directories.
    onlydirs = [f for f in listdir("data") if (isdir(join("data", f)) and f != "color")]
    onlydirs.sort()
    # move this date to the top of the list.
    onlydirs.insert(0, onlydirs.pop(onlydirs.index(date)))
    # restructure the date for database
    year = date[2:6]
    month = date[6:8]
    day = date[8:]
    date = year + "-" + month + "-" + day
    print("date = " + date)
    conn = sqlite3.connect('PW17QSI.db')
    c = conn.cursor()
    c.execute("select name,dateobs,naxis1,exptime,filter, \
                 imagetyp,thumbpath FROM images \
                 where dateobs >= date(?) \
                 and dateobs <  date(?, '+1 day') order by imagetyp desc",(date, date,))
                # where imagetyp='Light Frame' \

    result = c.fetchall()
    print(result)
    c.close()

    output = template('templates/main', url=url, dirlist=onlydirs,
      imlist = result)
    return output

class StripPathMiddleware(object):
    '''
    Get that slash out of the request
    '''
    def __init__(self, a):
        self.a = a
    def __call__(self, e, h):
        e['PATH_INFO'] = e['PATH_INFO'].rstrip('/')
        return self.a(e, h)

if (__name__ == "__main__"):
  bottle.run(app=StripPathMiddleware(app),
      reloader = True,
      host='0.0.0.0',
      port=6000,
      debug=True)
