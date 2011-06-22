#coding=utf-8

from datetime import date
import time
import simplejson
from bot import Bot
from trackingData import TrackingData
import sys
from pageParser import MZATrainsListParser
import pageChecker
import urllib2
from filter import PlacesFilter
from pageParser import MZAParser


bot = Bot()
res = bot.call('''{ "id":1, "jsonrpc":2, "method":"getTrainStatistics", "params": ["Санкт-Петербург", "Курск", "143А"]}''')
print res
sys.exit(0)

parser = MZAParser()
f = open('../tests/index.php', 'r')
page = f.read()
f.close()
parser.ParsePage(page)
print parser.result
sys.exit(0)

data = TrackingData()
data.loadFromDict({     "route_from":"",\
                        "route_to":"",\
                        "trains":[\
                                  [1305510400, "049"],\
                                  [1305511100, "121"]\
                                  ],\
                        "car_type":3,\
                        "emails":["s.stasishin@gmail.com", "stasishin@speechpro.com"],\
                        "sms":[],\
                        "expires":12378789,\
                        "period":60,\
                        "uid":123474,\
                        "range":[9, 28],\
                        "parity":1\
                    })
filt = PlacesFilter()
places = [[2, 2, [[1], [2], [26]]], [5, 3, [[1], [2], [8], [9], [23], [24], [25], [28], [33]]], [6, 3, [[9], [10], [11], [12], [13]]]]
#places = [[2, 2, [[1], [2], [26]]], [5, 3, [[1], [2], [8], [9], [23], [24], [25], [28], [33]]], [6, 3, [[5], [6], [7], [8], [9], [10], [11], [12], [13], [14], [33], [34]]]]
filt.applyFilter(places, data)
print filt.totalPlaces
print filt.filteredPlaces
sys.exit(0)

bot = Bot()
res = bot.call('''{ "id":1, "jsonrpc":2, "method":"getTrainsList", "params": ["Санкт-Петербург", "Москва", 1305839921]}''')
print res
sys.exit(0)

request = urllib2.Request(url="http://www.mza.ru/?exp=1", data="""ScheduleRoute_DepDate=20.05.2011
                                                             &ScheduleRoute_StationFrom=САНКТ-ПЕТЕРБУРГ
                                                             &ScheduleRoute_StationTo=МОСКВА
                                                             &spr=ScheduleRoute
                                                             &submit=Показать
                                                             &ScheduleRoute_ArvTimeFrom=
                                                             &ScheduleRoute_ArvTimeTo=
                                                             &ScheduleRoute_DepTimeFrom=
                                                             &ScheduleRoute_DepTimeTo=""")
response = urllib2.urlopen(request)
checker = pageChecker.MZAErrorChecker()
page = response.read()
res = checker.CheckPage(page)
if not res == 0:
    print "Error: res=%d" % res
    if res == 1:
        print checker.errorText
    sys.exit(1)
parser = MZATrainsListParser()
trains = parser.GetTrainsList(page)
for t in trains:
    print t['train']
    print t['departure']
    print t['arrival']
    print t['onway']
    print t['vip']
sys.exit(0)

bot = Bot()
res_str = bot.call('''{ "method":"start",
                    "params": [
                    {   "route_from":"САНКТ-ПЕТЕРБУРГ",
                        "route_to":"МОСКВА",
                        "trains":[
                                  [1305510400, "049А"],
                                  [1305511100, "121А"]
                                  ],
                        "car_type":1,
                        "emails":["s.stasishin@gmail.com", "stasishin@speechpro.com"],
                        "sms":[],
                        "expires":12378789,
                        "period":60,
                        "uid":123474
                    }]
                  }''')
ret = simplejson.loads(res_str)
if ret["error"] != None:
    print "Error:", ret["error"]
else:
    res = ret["result"]
    res_code = res["code"]
    if res_code == 1:
        print "Express-3 error in position", res["TrainIndex"]
        print res["ExpressError"].encode("utf-8")
    elif res_code == 3:
        print res["HTTPError"].encode("utf-8")
    elif res_code == 2:
        print "Ambiguous train number in position", res["TrainIndex"]
        options = res["TrainOptions"]
        for i in range(len(options)):
            print options[i][0].encode("utf-8"), "-", options[i][1].encode("utf-8")
    elif res_code == 0:
        print "OK!"
        
        time.sleep(60)
        res_str = bot.call('''{ "method":"stop",
                        "params":[8, "s.stasishin@gmail.com"]}
                   ''')
        print res_str
