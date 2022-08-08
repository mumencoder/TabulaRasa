
import os, sys, time, random
import mysql.connector
import lupa

lua = lupa.LuaRuntime(unpack_returned_tuples=True)

with open('./settings/default/network.lua', "r") as f:
    network_settings = f.read()
lua.execute( network_settings )

settings = lua.globals().xi.settings

def wait_for_db():
    db = None
    while db is None:
        try:
            db = mysql.connector.connect(
                host=settings.network.SQL_HOST, 
                user=settings.network.SQL_USER, 
                passwd=settings.network.SQL_PASSWORD, 
                database=settings.network.SQL_DATABASE)
        except mysql.connector.errors.DatabaseError as e:
            # 2003: connection error
            if e.errno != 2003:
                raise
            time.sleep(5.0)

    cur = db.cursor()
    waiting = True
    while waiting is True:
        cur.execute("SELECT 1 FROM zone_weather LIMIT 1")
        rows = cur.fetchall()
        if len(rows) > 0:
            waiting = False
        else:
            time.sleep(5.0)
            print("waiting for db...")
    return db

def assign_zone_ips():
    db = wait_for_db()
    cur = db.cursor()

    base_zoneport = 22222
    zoneports = []
    for i in range(0,1):
        zoneports.append( base_zoneport + i)

    zone_assigns = []
    cur.execute("SELECT zoneid FROM `zone_settings`")
    for row in cur.fetchall():
        zone_assigns.append( (row[0], random.choice(zoneports)) )

    for (zoneid, zoneport) in zone_assigns:
        cur.execute(f"""UPDATE `zone_settings` SET zoneip="{os.getenv('XI_NETWORK_MAP_HOST')}",zoneport = %s WHERE zoneid = %s""", (zoneport, zoneid) )
        cur.fetchall()