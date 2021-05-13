import sqlite3
from bottle import route, static_file, run, debug, template, url

@route('/data/<filepath:path>', name='data')
def server_static(filepath):
    return static_file(filepath, root='./data')

@route('/assets/<filepath:path>', name='assets')
def server_static(filepath):
    return static_file(filepath, root='./assets')

@route('/astrobrowse')
def astro_browse():
    conn = sqlite3.connect('PW17QSI.db')
    c = conn.cursor()
    c.execute("SELECT name, dateobs, " + 
            "exptime, filter, imagetyp, thumbpath FROM images WHERE imagetyp='Light Frame'")
    result = c.fetchall()
    c.close()
    output = template('templates/make_table', rows=result, url=url)
    return output

run(reloader = True, host='0.0.0.0', port=5000, debug=True)
