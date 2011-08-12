#coding=utf-8

from datetime import date
from datetime import datetime
from datetime import timedelta
import time
import threading
import os
import sys
import random
import signal

import bot
from db import db
from trackingData import TrackingData

staticThreadsCount = 50
threadsTable = []
dataList = []
wasHup = False
wasTerm = False
    
def run(index):
    global threadsTable
    global wasTerm
    localData = threadsTable[index]
    while True:
        if wasTerm:
            break
        if not localData.runned:
            time.sleep(10)
            continue

        # Доспим оставшееся время
        now = datetime.today()
        sleep = 0
        if now < localData.data.nextRequest:
            diff = localData.data.nextRequest - now
            sleep = diff.seconds + diff.days * 24 * 3600
        time.sleep(sleep)
        
        # Делаем запрос
        bot.doRequest(localData.data.tracking)
        localData.data.nextRequest = datetime.today() + timedelta(seconds=localData.data.tracking.period)
        ##bot.log("%d: Next request on %s" % (localData.data.tracking.uid, localData.data.nextRequest.strftime("%Y-%m-%d %H:%M:%S")))
        localData.data.busy = False
        localData.runned = False
        
def runOnce(data):
    # Доспим оставшееся время
    now = datetime.today()
    sleep = 0
    if now < data.nextRequest:
        diff = data.nextRequest - now
        sleep = diff.seconds + diff.days * 24 * 3600
    time.sleep(sleep)
    
    # Делаем запрос
    bot.doRequest(data.tracking)
    data.nextRequest += timedelta(seconds=data.tracking.period)
    data.busy = False
        
class ThreadsTableEntry:
    def __init__(self, index):
        self.thread = threading.Thread(target=run, args=(index,))
        self.runned = False
        
    def start(self):
        self.thread.start()

class DataListEntry:
    busy = False
    nextRequest = datetime.today()
    
def TrackingInDataList(uid):
    global dataList
    for entry in dataList:
        if entry.tracking.uid == uid:
            return True
    return False

def RemoveStopped(rows):
    global dataList
    for entry in dataList:
        found = False
        for row in rows:
            if entry.tracking.uid == row[0]:
                found = True
                break
        if not found:
            bot.log("Tracking %d stopped" % entry.tracking.uid)
            dataList.remove(entry)
    
def RefreshDataList():
    global dataList
    database = db()
    if not database.query('SELECT * FROM bot_dynamic_info'):
        bot.emergencyMail('Database error', 'Error querying bot_dynamic_info: unable to refresh dataList!!!')
        return
    for row in database.rows:
        if row[3] != os.getcwd():
            continue
        entry = DataListEntry()
        entry.tracking = TrackingData()
        entry.tracking.loadFromDB(row[0])
        if not TrackingInDataList(entry.tracking.uid):
            entry.tracking.expires = row[2]
            entry.nextRequest += timedelta(seconds=random.randint(0, 59))
            entry.busy = False
            dataList.append(entry)
            bot.log("Tracking %d started" % entry.tracking.uid)
        RemoveStopped(database.rows)

def SigHandler(signum, frame):
    global wasHup
    global wasTerm
    if signum == signal.SIGHUP:
        wasHup = True
    elif signum == signal.SIGTERM:
        wasTerm = True





output_dir = '/var/log/bot'
so = se = open('%s/bot-daemon.out' % (output_dir), 'a', 0)
# re-open stdout without buffering
sys.stdout = os.fdopen(sys.stdout.fileno(), 'a', 0)
# redirect stdout and stderr to the log file opened above
os.dup2(so.fileno(), sys.stdout.fileno())
os.dup2(se.fileno(), sys.stderr.fileno())

bot.log("Starting...")
signal.signal(signal.SIGHUP, SigHandler)
signal.signal(signal.SIGTERM, SigHandler)

try:
    os.mkdir('/tmp/bot')
except:
    pass
pidfile = open('/tmp/bot/bot-daemon.pid', 'w')
pidfile.write(str(os.getpid()))
pidfile.close()

for i in range(staticThreadsCount):
    newThread = ThreadsTableEntry(i)
    threadsTable.append(newThread)
    newThread.start()

RefreshDataList()

bot.log("Started.")
bot.emergencyMail("Started", "bot-daemon.py has been started!")

# Главный цикл
while True:
    if wasTerm:
        break
    if wasHup:
        RefreshDataList()
        wasHup = False
        
    for tracking in dataList:
        # Если в данный момент выполняется запрос по данной заявке - пропускаем
        if tracking.busy:
            continue
        # Сначала удалим просроченные заявки
        if date.today() >= tracking.tracking.expires:
            bot.log("Tracking %d has expired" % tracking.tracking.uid)
            tracking.tracking.removeDynamicData()
            dataList.remove(tracking)
            continue
        
        # Проверим, не пора ли запустить заявку
        now = datetime.today()
        if now >= tracking.nextRequest or tracking.nextRequest - now < timedelta(minutes=1):
            # Если пора - ищем свободный поток
            found = False
            for threadData in threadsTable:
                if not threadData.runned:
                    # Нашли свободный - запускаем
                    threadData.data = tracking
                    tracking.busy = True
                    threadData.runned = True
                    found = True
                    break
            # Если не нашли свободного потока - создаем новый
            if not found:
                bot.log("Running %d in new thread" % tracking.tracking.uid)
                newThread = threading.Thread(target=runOnce, args=(tracking, ))
                tracking.busy = True
                newThread.start()
    if bot.lastRequest > bot.lastSuccessfullRequest and \
    bot.lastRequest - bot.lastSuccessfullRequest > timedelta():
        bot.emergencyMail("Request error", "There was no successfull requests during the last 10 minutes!")
        bot.log("Request error: there was no successfull requests during the last 10 minutes!")
    open('/tmp/bot/bot-daemon.tick', 'w').close()
    os.utime('/tmp/bot/bot-daemon.tick', None)
    time.sleep(60)
