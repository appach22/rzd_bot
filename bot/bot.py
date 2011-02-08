from datetime import date
from datetime import datetime
import time
from datetime import timedelta
from multiprocessing import Process
import os
import urllib2
import signal
import sys
import daemon

import pageChecker
from mailer import Mailer
import getter
import trackingData
from sms import SMS
from parser import MZAParser

        
class Bot:
    """The main class"""
    
    post_data = []
    active = False
    terminated = False

    def start(self, data):
##        # Проверяем диапазон дат    
##        dates = sorted(data.trains.keys())
##        if (dates[len(dates) - 1] - dates[0]) > timedelta(2):
##            return 3 #Date range is too large
        # Проверяем на корректность номера поездов и даты
        checker = pageChecker.MZAErrorChecker()
        res = 0
        for i in range(len(data.trains)):
            self.itemIndex = i
            try:
                request = urllib2.Request(url="http://www.mza.ru/?exp=1", data=data.getPostAsString(i))
                response = urllib2.urlopen(request)
            except urllib2.HTTPError as err:
                self.HTTPError = err.code
                res = -1
                break
            except urllib2.URLError as err:
                self.HTTPError = err.reason
                res = -1
                break
            res = checker.CheckPage(response.read())
            if res == 1: #express-3 request error: check Bot.errorText
                self.errorText = checker.errorText
                break
            elif res == 2: #train number is ambiguous: check Bot.options
                self.options = checker.options
                break
        
        #return on error
        if res != 0:    
            return res
        
        data.expires = sorted(data.trains)[len(data.trains) - 1][0] + timedelta(1)
        
        #start new bot
        self.p = Process(target = self.newTracking, args = (data, ))
        #p.daemon = True
        self.p.start()
            
        return 0
        
    def newTracking(self, data):
        self.mailer = Mailer()
        data.uid = str(os.getpid())
        print "pid=%s" % data.uid
        if (data.saveToFile("./pending/" + data.uid)):
            self.mailer.send("robot@rzdtickets.ru", 
                        ["s.stasishin@gmail.com"],
                        "Tracker error",
                        "plain",
                        "Error saving tracking data!")
            return
        self.mailer.send("robot@rzdtickets.ru", 
                    data.emails,
                    "Ваша заявка принята (%s - %s)" % (data.route_from, data.route_to),
                    "plain",
                    "Ваша заявка принята. Заявке присвоен номер %s. Используйте этот номер для отмены заявки." % data.uid)
        
        self.sms = SMS()
        self.sms.send("Tickets", "Заявка принята. Используйте номер %s для отмены заявки" % data.uid, data.sms)
        
        signal.signal(signal.SIGHUP, self.activate)
        signal.signal(signal.SIGINT, self.shutdown)
        
        self.runPending(data)
        
                    
    def activate(self, signum, frame):
        self.active = True
        
    def shutdown(self, signum, frame):
        print "SHUTDOWNED"
        self.terminated = True
        
    def runPending(self, data):
        while not self.active:
            time.sleep(60)
            if self.terminated:
                sys.exit(0)
                
        os.rename("./pending/" + data.uid, "./working/" + data.uid)
        self.mailer.send("robot@rzdtickets.ru", 
                    data.emails,
                    "Заявка %s активирована" % data.uid,
                    "plain",
                    "Заявка %s запущена в работу" % data.uid)
        self.sms.send("Tickets", "Заявка %s запущена в работу" % data.uid, data.sms)
        self.run(data)
        
    def run(self, data):
        print "RUNNED"
        prevs = [0 for i in range(len(data.trains))]
        while True:
            if datetime.now().hour == 3:
                time.sleep(60)
                continue
            print data.trains
            for i in range(len(data.trains)):
                try:
                    request = urllib2.Request(url="http://www.mza.ru/?exp=1", data=data.getPostAsString(i))
                    response = urllib2.urlopen(request)
                except urllib2.HTTPError as err:
                    self.HTTPError = err.code
                    continue
                except urllib2.URLError as err:
                    self.HTTPError = err.reason
                    continue
                parser = MZAParser()
                if parser.ParsePage(response.read()) == 0:
                    print parser.result
            
            time.sleep(data.period)
