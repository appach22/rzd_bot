#coding=utf-8

from datetime import date
from datetime import datetime
from datetime import timedelta
import time
from multiprocessing import Process
import os
import dl
import urllib2
import signal
import sys
#import daemon
import simplejson
from syslog import syslog


import pageChecker
from mailer import Mailer
import getter
import trackingData
from sms import SMS
from pageParser import MZAParser
from pageParser import MZATrainsListParser
from filter import PlacesFilter


class Bot:
    """The main class"""

    def __init__(self, remote_addr = ''):
#        self.active = False
        self.terminated = False
        self.remote_addr = remote_addr

    def start(self, data_dict):

        data = trackingData.TrackingData()
        data.loadFromDict(data_dict)
        data.ip_addr = self.remote_addr
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

        try:
            self.daemonize(target = self.newTracking, args = (data, False))
        except:
            ret["code"] = 255
            return ret
            
        ret["code"] = 0
        return ret
        
    def newTracking(self, data, isRestart):
        self.mailer = Mailer()
        self.sms = SMS()
        data.pid = os.getpid()
        if not isRestart:
            if not data.saveToDB():
                self.mailer.send('vpoezde.com', '<robot@vpoezde.com>',
                            data.emails + ["s.stasishin@gmail.com"],
                            "Ошибка базы данных",
                            "plain",
                            "Произошла ошибка записи в базу данных. Пожалуйста, повторите попытку.")
                return
            self.mailer.send('vpoezde.com', '<robot@vpoezde.com>',
                        data.emails,
                        "Ваша заявка принята (%s - %s)" % (data.route_from, data.route_to),
                        "plain",
                        "Ваша заявка принята и запущена в работу. Заявке присвоен номер %s. Используйте этот номер для отмены заявки." % data.uid)
        
            self.sms.send("Tickets", "Заявка принята. Используйте номер %s для отмены заявки" % data.uid, data)
        else:
            data.updateDynamicData()
            
        #signal.signal(signal.SIGHUP, self.activate)
        signal.signal(signal.SIGINT, self.shutdown)

        self.run(data)
        
                    
    def activate(self, signum, frame):
        self.active = True
        
    def shutdown(self, signum, frame):
        self.terminated = True
             
    def run(self, data):
        prevs = [0 for i in range(len(data.trains))]
        while not self.terminated and data.expires > date.today():
            if datetime.now().hour == 3:
                time.sleep(60)
                continue
            for i in range(len(data.trains)):
                try:
                    request = urllib2.Request(url="http://www.mza.ru/?exp=1", data=data.getPostAsString(i))
                    response = urllib2.urlopen(request)
                except urllib2.HTTPError as err:
                    #self.HTTPError = err.code
                    time.sleep(60)
                    continue
                except urllib2.URLError as err:
                    #self.HTTPError = err.reason
                    time.sleep(60)
                    continue

                page = response.read()
                checker = pageChecker.MZAErrorChecker()
                if not checker.CheckPage(page) == 0:
                    time.sleep(60)
                    continue
                parser = MZAParser()
                if parser.ParsePage(page) != 0:
                    time.sleep(60)
                    continue

                filter = PlacesFilter()
                curr = filter.applyFilter(parser.result, data)
                if curr > prevs[i]:
                    # new tickets have arrived!!!
                    #print "%d ==> %d" % (prevs[i], curr)
                    self.makeEmailText(data, i, filter.filteredPlaces)
                    self.mailer.send('vpoezde.com', '<robot@vpoezde.com>',
                                data.emails,
                                "Билеты (+%d новых) [%s - %s]" % (curr - prevs[i], data.route_from, data.route_to),
                                "plain",
                                self.makeEmailText(data, i, filter.filteredPlaces))
                    self.sms.send("Tickets", "%d билетов (%d новых): %s, поезд %s" % (curr, curr - prevs[i], data.trains[i][0].strftime("%d.%m.%Y"), data.trains[i][1]), data)
                prevs[i] = curr
            
            time.sleep(data.period)

        if self.terminated:
            self.mailer.send('vpoezde.com', '<robot@vpoezde.com>', 
                        data.emails,
                        "Заявка %d (%s - %s) завершена" % (data.uid, data.route_from, data.route_to),
                        "plain",
                        "Заявка %d завершена. Спасибо за использование сервиса!" % (data.uid))
        os.exit(0)

    def makeEmailText(self, data, train_index, places):
        text = data.trains[train_index][0].strftime("%d.%m.%Y")
        text += "\n%s - %s\n" % (data.route_from, data.route_to)
        text += "Поезд %s\n" % data.trains[train_index][1]
        text += "В продаже имеются следующие места:"
        # TODO: передавать тип вагона полностью
        for car in places:
            type = ""
            if car[1] == 1:
                type = "Сидячий"
            if car[1] == 2:
                type = "Плацкартный"
            elif car[1] == 3:
                type = "Купейный"
            elif car[1] == 4:
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
        try:
            os.kill(data.pid, signal.SIGINT)
        except:
            ret["code"] = 5
            return ret
        data.removeDynamicData()
        return ret
        
    def getTrainsList(self, route_from, route_to, departure_date):
        ret = {}
        try:
            request = urllib2.Request(url="http://www.mza.ru/?exp=1", data="""ScheduleRoute_DepDate=%s
                                                             &ScheduleRoute_StationFrom=%s
                                                             &ScheduleRoute_StationTo=%s
                                                             &spr=ScheduleRoute
                                                             &submit=Показать
                                                             &ScheduleRoute_ArvTimeFrom=
                                                             &ScheduleRoute_ArvTimeTo=
                                                             &ScheduleRoute_DepTimeFrom=
                                                             &ScheduleRoute_DepTimeTo=""" % \
                                                             (date.fromtimestamp(departure_date).strftime("%d.%m.%Y"),
                                                             route_from.encode('utf-8'), route_to.encode('utf-8')))
            response = urllib2.urlopen(request)
        except urllib2.HTTPError as err:
            ret["code"] = 1
            ret["HTTPError"] = str(err.code)
            return ret
        except urllib2.URLError as err:
            ret["code"] = 1
            ret["HTTPError"] = str(err.reason)
            return ret
        checker = pageChecker.MZAErrorChecker()
        page = response.read()
        res = checker.CheckPage(page)
        if res == 1: #express-3 request error
            ret["code"] = 1
            ret["ExpressError"] = checker.errorText
            return ret
        parser = MZATrainsListParser()
        trains = parser.GetTrainsList(page)
        ret['code'] = 0
        ret['trains'] = trains
        return ret


    def call(self, request_text):
        try:
            rawreq = simplejson.loads(request_text)
            method = rawreq['method']
            params = rawreq.get('params', [])

            responseDict = {}
            responseDict['id'] = rawreq['id']
            responseDict['jsonrpc'] = rawreq['jsonrpc']

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


    def daemonize(self, target, args):
        # fork the first time (to make a non-session-leader child process)
        try:
            pid = os.fork()
        except OSError, e:
            raise RuntimeError("1st fork failed: %s [%d]" % (e.strerror, e.errno))
        if pid == 0:
            # detach from controlling terminal (to make child a session-leader)
            os.setsid()
            libc = dl.open('/lib/libc.so.6')
            libc.call('prctl', 15, 'bot', 0, 0, 0)
            try:
                pid = os.fork()
            except OSError, e:
                raise RuntimeError("2nd fork failed: %s [%d]" % (e.strerror, e.errno))
                raise Exception, "%s [%d]" % (e.strerror, e.errno)
            if pid == 0:
                os.chdir("/")
                os.umask(0)
            else:
                # child process is all done
                os._exit(0)
        else:
            # parent (calling) process is all done
            return
        # grandchild process now non-session-leader, detached from parent
        # grandchild process must now close all open files
        try:
            maxfd = os.sysconf("SC_OPEN_MAX")
        except (AttributeError, ValueError):
            maxfd = 1024

        for fd in range(maxfd):
            try:
               os.close(fd)
            except OSError: # ERROR, fd wasn't open to begin with (ignored)
               pass

        # redirect stdin, stdout and stderr to /dev/null
        os.open("/usr/local/bot/outputs/bot.%d.out" % os.getpid(), os.O_RDWR + os.O_CREAT, 0644) # standard input (0)
        os.dup2(0, 1)
        os.dup2(0, 2)

        libc = dl.open('/lib/libc.so.6')
        libc.call('prctl', 15, 'bot', 0, 0, 0)
        
        target(*args)
        os.exit(0)

