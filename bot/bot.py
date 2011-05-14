#coding=utf-8

from datetime import date
from datetime import datetime
from datetime import timedelta
import time
from multiprocessing import Process
import os
import urllib2
import signal
import sys
#import daemon
import simplejson


import pageChecker
from mailer import Mailer
import getter
import trackingData
from sms import SMS
from parser import MZAParser
from filter import PlacesFilter

        
class Bot:
    """The main class"""

    def __init__(self):
#        self.active = False
        self.terminated = False

    def start(self, data_dict):

        data = trackingData.TrackingData()
        data.loadFromDict(data_dict)
        # Проверяем на корректность номера поездов и даты
        checker = pageChecker.MZAErrorChecker()
        res = 0
        ret = {}
        for i in range(len(data.trains)):
            self.itemIndex = i
            try:
                request = urllib2.Request(url="http://www.mza.ru/?exp=1", data=data.getPostAsString(i))
                response = urllib2.urlopen(request)
            except urllib2.HTTPError as err:
                ret["code"] = 3
                ret["HTTPError"] = str(err.code)
                return ret
            except urllib2.URLError as err:
                ret["code"] = 3
                ret["HTTPError"] = str(err.reason)
                return ret
            res = checker.CheckPage(response.read())
            if res == 1: #express-3 request error
                ret["code"] = 1
                ret["TrainIndex"] = i
                ret["ExpressError"] = checker.errorText
                return ret
            elif res == 2: #train number is ambiguous
                ret["code"] = 2
                ret["TrainIndex"] = i
                ret["TrainOptions"] = checker.options
                return ret
        
        #return on error
        if res != 0:    
            ret["code"] = res
            return ret
        
        data.expires = sorted(data.trains)[len(data.trains) - 1][0] + timedelta(1)
        
        #start new bot
        self.p = Process(target = self.newTracking, args = (data, False))
        #p.daemon = True
        self.p.start()
            
        ret["code"] = 0
        return ret
        
    def newTracking(self, data, isRestart):
        self.mailer = Mailer()
        self.sms = SMS()
        data.pid = os.getpid()
        if not isRestart:
            if not data.saveToDB():
                self.mailer.send("robot@rzdtickets.ru", 
                            data.emails + ["s.stasishin@gmail.com"],
                            "Ошибка базы данных",
                            "plain",
                            "Произошла ошибка записи в базу данных. Пожалуйста, повторите попытку.")
                return
            self.mailer.send("robot@rzdtickets.ru", 
                        data.emails,
                        "Ваша заявка принята (%s - %s)" % (data.route_from, data.route_to),
                        "plain",
                        "Ваша заявка принята и запущена в работу. Заявке присвоен номер %s. Используйте этот номер для отмены заявки." % data.uid)
        
            self.sms.send("Tickets", "Заявка принята. Используйте номер %s для отмены заявки" % data.uid, data.sms)
        else:
            data.updateDynamicInfo()
        #signal.signal(signal.SIGHUP, self.activate)
        signal.signal(signal.SIGINT, self.shutdown)
        
        self.run(data)
        
                    
    def activate(self, signum, frame):
        self.active = True
        
    def shutdown(self, signum, frame):
        print "SHUTDOWNED"
        self.terminated = True
             
    def run(self, data):
        print "RUNNED"
        prevs = [0 for i in range(len(data.trains))]
        print "1"
        while not self.terminated and data.expires > date.today():
            print "2"
            if datetime.now().hour == 3:
                time.sleep(60)
                continue
            print "3"
            for i in range(len(data.trains)):
                print "4"
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
                if parser.ParsePage(response.read()) != 0:
                    continue
                
                print "5"
                filter = PlacesFilter()
                curr = filter.applyFilter(parser.result, data)
                if curr > prevs[i]:
                    # new tickets have arrived!!!
                    print "%d ==> %d" % (prevs[i], curr)
                    self.makeEmailText(data, i, filter.filteredPlaces)
                    self.mailer.send("robot@rzdtickets.ru", 
                                data.emails,
                                "Билеты (+%d новых) [%s - %s]" % (curr - prevs[i], data.route_from, data.route_to),
                                "plain",
                                self.makeEmailText(data, i, filter.filteredPlaces))
                    self.sms.send("Tickets", "%d билетов (%d новых): %s, поезд %s" % (curr, curr - prevs[i], data.trains[i][0].strftime("%d.%m.%Y"), data.trains[i][1]), data.sms)
                prevs[i] = curr
            
            print "6"
            time.sleep(data.period)

        print self.terminated, data.expires <= date.today()
        if self.terminated:
            self.mailer.send("robot@rzdtickets.ru", 
                        data.emails,
                        "Заявка %d (%s - %s) завершена" % (data.uid, data.route_from, data.route_to),
                        "plain",
                        "Заявка %d завершена. Спасибо за использование сервиса!" % (data.uid))
        print "BYE!"

    def makeEmailText(self, data, train_index, places):
        text = data.trains[train_index][0].strftime("%d.%m.%Y")
        text += "\n%s - %s\n" % (data.route_from, data.route_to)
        text += "Поезд %s\n" % data.trains[train_index][1]
        text += "В продаже имеются следующие места:"
        for car in places:
            type = ""
            if car[1] == 1:
                type = "Плацкартный"
            elif car[1] == 2:
                type = "Купейный"
            elif car[1] == 3:
                type = "СВ"
            text += "\nВагон №%02d (%s): " % (car[0], type)
            for place in car[2]:
                text += str(place[0])
                if len(place) > 1:
                    if place[1] == 0:
                        text += "Ц"
                    elif place[1] == 1:
                        text += "М"
                    elif place[1] == 2:
                        text += "Ж"
                    elif place[1] == 3:
                        text += "С"
                if place != car[2][len(car[2]) - 1]:
                    text += ", "
        return text

    def stop(self, uid, email):
        data = trackingData.TrackingData()
        ret = {}
        ret["code"] = data.loadFromDB(uid)
        if not ret["code"] == 0:
            return ret
        if not email in data.emails:
            ret["code"] = 3
            return ret
        if data.pid == -1:
            ret["code"] = 4
            return ret
        print "killing ", data.pid
        os.kill(data.pid, signal.SIGINT)
        data.removeDynamicData()
        return ret
        
    def call(self, request_text):
        try:
            rawreq = simplejson.loads(request_text)
            method = rawreq['method']
            params = rawreq.get('params', [])

            responseDict = {}

            try:
                response = getattr(self, method, None)(*params)
                responseDict['result'] = response
                responseDict['error'] = None
            except Exception as err:
                responseDict['error'] = err.args

            json_str = simplejson.dumps(responseDict)
        except:
            raise
        else:
            pass
        return json_str
        
