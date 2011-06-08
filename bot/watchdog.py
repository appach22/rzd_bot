import os
import errno
import MySQLdb
import trackingData
#from bot import Bot
from datetime import date
import time
from syslog import syslog
import sys
import fcntl

sys.path.remove(os.path.dirname(os.path.realpath(__file__)))

host = "localhost"
database = "rzdtickets.ru"
user = "rzdbot"
passw = "rzdtickets22"

def RestartTracking(uid):
    print "Restarting %d" % (uid)
    syslog("Restarting %d" % uid)
    data = trackingData.TrackingData()
    if data.loadFromDB(uid) == 0:
        # remove old dates
        while data.trains[0][0] < date.today():
            print "Removing old date", data.trains[0][0].strftime("%Y-%m-%d")
            del data.trains[0]
        if data.script == None or data.script == '':
            data.script = os.path.dirname(os.path.realpath(__file__))
        sys.path.append(data.script)
        from bot import Bot
        bot = Bot()
        bot.daemonize(target=bot.newTracking, args=(data, True))
        time.sleep(10)
        sys.path.remove(data.script)
    else:
        print "Error loading tracking %d from the main table" % uid

    
def CheckAll():
    # prevent parallel execution
    lockfd = open('/tmp/bot-watchdog.lock', 'w')
    fcntl.flock(lockfd, fcntl.LOCK_EX)

    try:
        conn = MySQLdb.connect(passwd = passw,
                               db = database,
                               user = user,
                               charset = "utf8", 
                               use_unicode = True)
##        conn = MySQLdb.connect(host = host,
##                               user = user,
##                               passwd = passw,
##                               db = database,
##                               charset = "utf8", 
##                               use_unicode = True)
    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
        return 1
    else:
        try:
            cursor = conn.cursor()
        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            return 1
        else:
            try:
                query = """SELECT * FROM bot_dynamic_info"""
                cursor.execute(query)
                row = cursor.fetchone()
                while not row == None:
                    if date.today() >= row[2]:
                        data = trackingData.TrackingData()
                        data.uid = row[0]
                        print "Tracking %d has expired" % data.uid
                        data.removeDynamicData()
                        row = cursor.fetchone()
                        continue
                    pid = row[1]
                    try:
                        os.kill(pid, 0)
                    except OSError, err:
                        if not err.errno == errno.EPERM:
                            RestartTracking(row[0])
                        else:
                            print "Not enough permissions to signal the process"
                    row = cursor.fetchone()
            except MySQLdb.Error, e:
                print "Error %d: %s" % (e.args[0], e.args[1])
                return 1
            finally:
                cursor.close()
        finally:
            conn.close()

    return 0

CheckAll()
