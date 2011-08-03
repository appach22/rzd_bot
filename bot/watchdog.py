#coding=utf-8

import os
import trackingData
from db import db
from datetime import date
from datetime import datetime
from datetime import timedelta
import time
import sys
import fcntl
import errno

sys.path.remove(os.path.dirname(os.path.realpath(__file__)))

host = "localhost"
database = "rzdtickets.ru"
user = "rzdbot"
passw = "rzdtickets22"

datestr = ''

def DoRequest(row, sleep):
    script = row[3]
    if script == None or script == '':
        script = os.path.dirname(os.path.realpath(__file__))
    # Передаем в качестве параметров номер заявки и время для сна перед запросом
    os.system('(sleep %d; python %s/bot.py %d) &' % (sleep, script, row[0]))


def CheckAll():

    global datestr
    # check if watchdog enabled
    if os.path.exists('/home/user/dont-watch'):
        return 0

    datestr = str(datetime.now())
    try:
        # prevent parallel execution
        lockfd = open('/tmp/bot-watchdog.lock', 'w')
        fcntl.flock(lockfd, fcntl.LOCK_EX)
    except IOError as (err, strerr):
        print datestr, "I/O error({0}): {1}".format(err, strerr)
        return 1

    database = db()
    if not database.query('SELECT * FROM bot_dynamic_info'):
        return 1
    for row in database.rows:
        # Сначала удалим просроченные заявки
        if date.today() >= row[2]:
            data = trackingData.TrackingData()
            data.uid = row[0]
            print datestr, "Tracking %d has expired" % data.uid
            data.removeDynamicData()
            continue
        sleep = 0
        now = datetime.today()
        # Если текущее время больше времени следующего запуска - запускаем
        if now >= row[4]:
            # Добавим случайную составляющую, дабы исключить одновременный запуск
            sleep = row[4].second
        # Если текущее время почти дошло до времени след. запуска (разница меньше минуты) - запускаем
        elif row[4] - now < timedelta(minutes=1):
            diff = row[4] - now
            # Доспим оставшееся время
            sleep = diff.seconds + diff.days * 24 * 3600
        else:
            continue
        pid = row[1]
        if pid != -1:
            # Если это не первый запуск, проверим: а вдруг все еще выполняется предыдущий экземпляр
            try:
                os.kill(pid, 0)
            except OSError, err:
                if not err.errno == errno.EPERM:
                    # Если предыдущий экземпляр закончил работу - то запускаем
                    DoRequest(row, sleep)
                else:
                    print datestr, "Not enough permissions to signal the process"
        else:
            DoRequest(row, sleep)

    return 0

CheckAll()
