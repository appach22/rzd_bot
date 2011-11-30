#coding=utf-8

from datetime import date
from datetime import datetime
from datetime import timedelta
import time
import os
import urllib2
import sys
import simplejson
import traceback
import signal

import pageChecker
from mailer import Mailer
import getter
import trackingData
from trackingData import TrackingData
from sms import SMS
from pageParser import MZAParser
from pageParser import MZATrainsListParser
from filter import PlacesFilter


lastRequest = datetime.today()
lastSuccessfullRequest = datetime.today()
emergencyAddress = 's.stasishin@gmail.com'
ip_addr = ''

#def setGlobalParameters(remote_addr = '', out_dir = '/var/log/bot'):
#    global ip_addr
#    global output_dir
#    ip_addr = remote_addr
#    output_dir = out_dir

def log(message):
    print "%s: %s" % (datetime.today().strftime("%Y-%m-%d %H:%M:%S"), message)
    
def start(data_dict):
    global ip_addr
    data = trackingData.TrackingData()
    data.loadFromDict(data_dict)
    data.ip_addr = ip_addr
    data.script = os.path.dirname(os.path.abspath(__file__))
    # Проверяем на корректность номера поездов и даты
    checker = pageChecker.MZAErrorChecker()
    ret = {}
    for train in data.trains:
        res = 255
        while res == 255:
            try:
                request = urllib2.Request(url="http://www.mza.ru/?exp=1", data=data.getPostAsString(train))
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
                #ret["TrainIndex"] = i
                ret["ExpressError"] = checker.errorText
                return ret
            elif res == 2: #station name is ambiguous
                ret["code"] = 3
                ret["StationNum"] = checker.stationNum
                ret["StationOptions"] = checker.options
                for station in ret["StationOptions"]:
                    station.append(data.getStationById(station[0].encode('utf-8')))
                return ret
            elif res == 3: #station name is incorrect
                ret["code"] = 4
                ret["Station"] = checker.station
                ret["StationError"] = checker.errorText
                return ret

    mailer = Mailer()
    sms = SMS()
    if not data.saveToDB():
        mailer.send('vpoezde.com', '<robot@vpoezde.com>',
                    data.emails + ["s.stasishin@gmail.com"],
                    "Ошибка базы данных",
                    "Произошла ошибка записи в базу данных. Пожалуйста, повторите попытку.",
                    "<html></html>")
        return
    
    # Сигнализируем демону об изменениях в bot_dynamic_table
    daemonPid = open('/tmp/bot/bot-daemon.pid', 'r')
    pid = int(daemonPid.read())
    daemonPid.close()
    os.kill(pid, signal.SIGHUP)

    tmpl = open('templates/hello.tmpl')
    html = tmpl.read()
    mailer.send('vpoezde.com', '<robot@vpoezde.com>',
                data.emails,
                "Ваша заявка %d принята (%s - %s)" % (data.uid, data.route_from, data.route_to),
                "Ваша заявка принята и запущена в работу. Вы будете получать оповещения на этот адрес в случае появления новых свободных мест.\nЗаявке присвоен номер %s. Используйте этот номер для отмены заявки." % data.uid,
                html)

    sms.send("vpoezde.com", "Заявка принята. Используйте номер %s для отмены заявки" % data.uid, data)

    ret["code"] = res
    return ret


def doRequest(data):
    global lastRequest
    global lastSuccessfullRequest

    now = datetime.now()
    if now.hour == 3:
        return
    if now.hour == 5 and now.minute == 40:
        return

    mailer = Mailer()
    sms = SMS()
    today = date.today()
    for train in data.trains:
        if train.date < today:
            continue
        #log("Requesting %d..." % data.uid)
        request_ok = False
        for i in range(3):
            try:
                lastRequest = datetime.today()
                request = urllib2.Request(url="http://www.mza.ru/?exp=1", data=data.getPostAsString(train))
                response = urllib2.urlopen(request)
                page = response.read()
                request_ok = True
                break
            except urllib2.HTTPError as err:
                log("%d: HTTPError: %d" % (data.uid, err.code))
                time.sleep(1)
                continue
            except urllib2.URLError as err:
                log("%d: URLError: %s" % (data.uid, err.reason))
                time.sleep(1)
                continue
            except:
                print str(traceback.format_exc())

        if not request_ok:
            log("%d: Request error" % data.uid)
            #emergencyMail("Request error", "Check %s/bot-%.6d.out" % (output_dir, data.uid))
            #data.updateDynamicData()
            return

        lastSuccessfullRequest = datetime.today()      
        checker = pageChecker.MZAErrorChecker()
        chkres = checker.CheckPage(page)
        if not chkres == 0:
            if not chkres == 255 and checker.errorText.encode('utf-8').find("Повторите Ваш запрос позже") == -1:
                log("%d: Checker error: %s" % (data.uid, checker.errorText.encode('utf-8')))
            time.sleep(3)
            continue
        parser = MZAParser()
        if parser.ParsePage(page) != 0:
            log("%d: Parser error" % data.uid)
            time.sleep(1)
            continue

        filter = PlacesFilter()
        filter.applyFilter(parser.result, train)
        curr = filter.getMatchedCount()
        total_curr = filter.getTotalCount()
        if curr > train.prev:
            # new tickets have arrived!!!
            mailer.send('vpoezde.com', '<robot@vpoezde.com>',
                        data.emails,
                        "Билеты (+%d новых) [Заявка %d: %s - %s]" % (total_curr - train.total_prev, data.uid, data.route_from, data.route_to),
                        "plain",
                        makeEmailText(data, train, filter.totalPlaces))
            if data.sms_count < 29:
                sms.send("vpoezde.com", "%d билетов (%d новых): %s, поезд %s" % (total_curr, total_curr - train.total_prev, train.date.strftime("%d.%m.%Y"), train.number), data)
            if data.sms_count == 29:
                sms.send("vpoezde.com", "Для заявки %d достигнут предел количества sms-сообщений!" % (data.uid), data)
        train.prev = curr
        train.total_prev = total_curr
        time.sleep(2)
##        data.updateTrain(train)
##        data.updateDynamicData()


def makeEmailText(data, train, places):
    text = train.date.strftime("%d.%m.%Y")
    text += "\n%s - %s\n" % (data.route_from, data.route_to)
    text += "Поезд %s\n" % train.number
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


def stop(uid, email):
    data = trackingData.TrackingData()
    ret = {}
    ret["code"] = data.loadFromDB(uid)
    if not ret["code"] == 0:
        return ret
    if not email in data.emails:
        ret["code"] = 3
        return ret
    if not data.getDynamicData(uid):
        ret["code"] = 4
        return ret
    data.removeDynamicData()

    # Сигнализируем демону об изменениях в bot_dynamic_table
    daemonPid = open('/tmp/bot/bot-daemon.pid', 'r')
    pid = int(daemonPid.read())
    daemonPid.close()
    os.kill(pid, signal.SIGHUP)
    
    mailer = Mailer()
    mailer.send('vpoezde.com', '<robot@vpoezde.com>', 
                data.emails,
                "Заявка %d (%s - %s) завершена" % (data.uid, data.route_from, data.route_to),
                "plain",
                "Заявка %d завершена. Спасибо за использование сервиса!" % (data.uid))
    return ret


def getTrainsList(route_from, route_to, departure_date):
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


def getTrainStatistics(station_from, station_to, train):
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


def call(request_text):
    try:
        rawreq = simplejson.loads(request_text)
        method = rawreq['method']
        params = rawreq.get('params', [])

        responseDict = {}
        responseDict['id'] = rawreq['id']
        responseDict['jsonrpc'] = rawreq['jsonrpc']

        try:
            response = globals()[method](*params)
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


def emergencyMail(subject, text):
    global emergencyAddress
    mailer = Mailer()
    mailer.send('vpoezde.com', '<robot@vpoezde.com>', [emergencyAddress], subject, "plain", text)
    return

#if len(sys.argv) > 1:
#    doRequest(int(sys.argv[1]))
