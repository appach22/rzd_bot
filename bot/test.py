#coding=utf-8

from datetime import date
import simplejson
from bot import Bot
from trackingData import TrackingData
import sys

bot = Bot()
#res_str = bot.call('''{"method":"getStations", "params":["value=САН"]}''')
#print "Result: ", res_str
#sys.exit(0)
res_str = bot.call('''{ "method":"start",
                    "params": [                    
                    {   "route_from":"САНКТ-ПЕТЕРБУРГ",
                        "route_to":"МОСКВА",
                        "trains":[[1305147600, "055А"], [1305147600, "051А"]],
                        "car_type":1,
                        "emails":["stasishin@speechpro.com"],
                        "sms":[],
                        "expires":12378789,
                        "period":60,
                        "uid":123461
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
        
##if res == -1:
##    print "Server error:", bot.HTTPError
##elif res == 1:
##    print "Express-3 error:", bot.errorText
##elif res == 2:
##    text = ""
##    for i in range(len(bot.options)):
##        text = text + '<b>' + bot.options[i][0] + '</b> - ' + '<i>' + bot.options[i][1] + '</i><br/>'
##    testMailer = mailer.Mailer()
##    testMailer.send("robot@rzdtickets.ru", ["s.stasishin@gmail.com"], "Тестовое сообщение", "html", text)
##elif res == 3:
##    print "Error: date range is too large"
##else:
##    print "OK"
