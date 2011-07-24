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
import traceback


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

    def __init__(self, remote_addr = '', output_dir = '/var/log/bot'):
#        self.active = False
        self.terminated = False
        self.remote_addr = remote_addr
        self.output_dir = output_dir
        self.emergencyAddress = 's.stasishin@gmail.com'
        
    def start(self, data_dict):

        data = trackingData.TrackingData()
        data.loadFromDict(data_dict)
        data.ip_addr = self.remote_addr
        data.script = os.path.dirname(os.path.abspath(__file__))
        # Проверяем на корректность номера поездов и даты
        checker = pageChecker.MZAErrorChecker()
        res = 255
        ret = {}
        for i in range(len(data.trains)):
            self.itemIndex = i
            while res == 255:
                try:
                    request = urllib2.Request(url="http://www.mza.ru/?exp=1", data=data.getPostAsString(i))
                    response = urllib2.urlopen(request)
                except urllib2.HTTPError as err:
                    ret["code"] = 1
                    ret["HTTPError"] = str(err.code)
                    return ret
                except urllib2.URLError as err:
                    ret["code"] = 1
                    ret["HTTPError"] = str(err.reason)
                    return ret
                res = checker.CheckPage(response.read())
                if res == 1: #express-3 request error
                    ret["code"] = 2
                    ret["TrainIndex"] = i
                    ret["ExpressError"] = checker.errorText
                    return ret
                elif res == 2: #station name is ambiguous
                    ret["code"] = 3
                    ret["StationNum"] = checker.stationNum
                    ret["StationOptions"] = checker.options
                    for station in ret["StationOptions"]:
                        station.append(data.getStationById(station[0].encode('utf-8')))
                    f.close()
                    return ret
                elif res == 3: #station name is incorrect
                    ret["code"] = 4
                    ret["Station"] = checker.station
                    ret["StationError"] = checker.errorText
                    return ret

        #return on error
        if res != 0:
            ret["code"] = res
            return ret

        try:
            self.daemonize(target = self.newTracking, args = (data, False))
        except:
            self.emergencyMail("Daemonize exception", "Daemonize exception occured:\n %s\n" % (str(traceback.format_exc())))
            os._exit(1)

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
                        "Ваша заявка %d принята (%s - %s)" % (data.uid, data.route_from, data.route_to),
                        "plain",
                        "Ваша заявка принята и запущена в работу. Вы будете получать оповещения на этот адрес в случае появления новых свободных мест.\nЗаявке присвоен номер %s. Используйте этот номер для отмены заявки." % data.uid)
        
            self.sms.send("vpoezde.com", "Заявка принята. Используйте номер %s для отмены заявки" % data.uid, data)
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
        total_prevs = [0 for i in range(len(data.trains))]
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
                filter.applyFilter(parser.result, data)
                curr = filter.getMatchedCount()
                total_curr = filter.getTotalCount()
                if curr > prevs[i]:
                    # new tickets have arrived!!!
                    #print "%d ==> %d" % (prevs[i], curr)
                    self.mailer.send('vpoezde.com', '<robot@vpoezde.com>',
                                data.emails,
                                "Билеты (+%d новых) [Заявка %d: %s - %s]" % (total_curr - total_prevs[i], data.uid, data.route_from, data.route_to),
                                "plain",
                                self.makeEmailText(data, i, filter.totalPlaces))
                    if data.sms_count < 29:
                        self.sms.send("vpoezde.com", "%d билетов (%d новых): %s, поезд %s" % (total_curr, total_curr - total_prevs[i], data.trains[i][0].strftime("%d.%m.%Y"), data.trains[i][1]), data)
                    if data.sms_count == 29:
                        self.sms.send("vpoezde.com", "Для заявки %d достигнут предел количества sms-сообщений!" % (data.uid), data)
                prevs[i] = curr
                total_prevs[i] = total_curr
            
            time.sleep(data.period)

        if self.terminated:
            self.mailer.send('vpoezde.com', '<robot@vpoezde.com>', 
                        data.emails,
                        "Заявка %d (%s - %s) завершена" % (data.uid, data.route_from, data.route_to),
                        "plain",
                        "Заявка %d завершена. Спасибо за использование сервиса!" % (data.uid))

    def makeEmailText(self, data, train_index, places):
        text = data.trains[train_index][0].strftime("%d.%m.%Y")
        text += "\n%s - %s\n" % (data.route_from, data.route_to)
        text += "Поезд %s\n" % data.trains[train_index][1]
        text += "В продаже имеются следующие места:\n"
        # TODO: передавать тип вагона полностью
        for car in places:
#            type = ""
#            if car[1] == 1:
#                type = "сидячий"
#            if car[1] == 2:
#                type = "плацкартный"
#            elif car[1] == 3:
#                type = "купейный"
#            elif car[1] == 4:
#                type = "СВ"
            price = '/'.join(car[3])
            text += "\nВагон №%02d\nТип: %s\nСтоимость: %s\nСвободные места: " % (car[0], car[4], price)
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
                    elif place[1] > 255:
                        text += unichr(place[1]).encode('utf-8')
                if place != car[2][len(car[2]) - 1]:
                    text += ", "
            text += '\n'
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
        i = 0
        while i < 5:
            try:
                os.kill(data.pid, 0)
            except:
                break
            time.sleep(1)
            i += 1
        if i < 5:
            data.removeDynamicData()
        else:
            ret["code"] = 6
            self.emergencyMail("Kill error", "Tracking %d process %d is still alive!" % (data.uid, data.pid))
        return ret


    def getTrainsList(self, route_from, route_to, departure_date):
        ret = {}
        try:
            data = trackingData.TrackingData()
            id = data.getStationId(route_from.encode('utf-8'))
            if not id == 0:
                sfrom = str(id)
            else:
                sfrom = route_from.encode('utf-8')
            id = data.getStationId(route_to.encode('utf-8'))
            if not id == 0:
                sto = str(id)
            else:
                sto = route_to.encode('utf-8')

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
                                                             sfrom, sto))
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
            ret["code"] = 2
            ret["ExpressError"] = checker.errorText
            return ret
        elif res == 2: #station name is ambiguous
            ret["code"] = 3
            ret["StationNum"] = checker.stationNum
            ret["StationOptions"] = checker.options
            return ret
        elif res == 3: #station name is incorrect
            ret["code"] = 4
            ret["Station"] = checker.station
            ret["StationError"] = checker.errorText
            return ret
        parser = MZATrainsListParser()
        trains = parser.GetTrainsList(page)
        ret['code'] = 0
        ret['trains'] = trains
        return ret


    def getTrainStatistics(self, station_from, station_to, train):
        ret = {}
        ret['places'] = [[], [], [], []]
        request_date = date.today()
        data = trackingData.TrackingData()
        id = data.getStationId(station_from.encode('utf-8'))
        if not id == 0:
            sfrom = str(id)
        else:
            sfrom = station_from.encode('utf-8')
        id = data.getStationId(station_to.encode('utf-8'))
        if not id == 0:
            sto = str(id)
        else:
            sto = station_to.encode('utf-8')

        for day in range(45):
            request_text = "TrainPlaces_DepDate=" + request_date.strftime("%d.%m.%Y") + \
                    "&TrainPlaces_StationFrom=" + sfrom + \
                    "&TrainPlaces_StationTo=" + sto + \
                    "&TrainPlaces_TrainN=" + train.encode('utf-8') + \
                    "&spr=TrainPlaces" + \
                    "&submit_TrainPlaces=Показать"
            success = False
            cnt = 0
            while (not success) and cnt < 7:
                cnt += 1
                try:
                    print "requesting", request_date
                    request = urllib2.Request(url="http://www.mza.ru/?exp=1", data=request_text)
                    response = urllib2.urlopen(request)
                except urllib2.HTTPError as err:
                    time.sleep(1)
                except urllib2.URLError as err:
                    time.sleep(1)
                else:
                    page = response.read()
                    checker = pageChecker.MZAErrorChecker()
                    res = checker.CheckPage(page)
                    if not res == 0 and not checker.errorCode == 2010: #игнорируем ошибку "неверная дата отправления"
                        time.sleep(1)
                        continue
                    success = True
                    break
            if not success:
                request_date += timedelta(days=1)
                continue
            parser = MZAParser()
            parser.ParsePage(page)
            places = [0, 0, 0, 0]
            for car in parser.result:
                places[car[1] - 1] += len(car[2])
            datestr = request_date.strftime("%d.%m")
            for i in range(4):
                ret['places'][i].append([datestr, places[i]])
            request_date += timedelta(days=1)

        ret['code'] = 0
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
        # detect libc location
        libc_path = '/lib/libc.so.6'
        if os.path.exists('/lib/i386-linux-gnu'):
            libc_path = '/lib/i386-linux-gnu/libc.so.6'
        # fork the first time (to make a non-session-leader child process)
        try:
            pid = os.fork()
        except OSError, e:
            raise RuntimeError("1st fork failed: %s [%d]" % (e.strerror, e.errno))
        if pid == 0:
            # detach from controlling terminal (to make child a session-leader)
            os.setsid()
            libc = dl.open(libc_path)
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
            return 0
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
        os.open("%s/bot.%d.out" % (self.output_dir, os.getpid()), os.O_RDWR + os.O_CREAT, 0644) # standard input (0)
        os.dup2(0, 1)
        os.dup2(0, 2)

        libc = dl.open(libc_path)
        libc.call('prctl', 15, 'bot', 0, 0, 0)

        target(*args)
        os._exit(0)

    def emergencyMail(self, subject, text):
        mailer = Mailer()
        mailer.send('vpoezde.com', '<robot@vpoezde.com>', [self.emergencyAddress], subject, "plain", text)
        return
