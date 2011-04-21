#coding=utf-8

from datetime import date
import simplejson
from bot import Bot
from trackingData import TrackingData


bot = Bot()
res_str = bot.call('''{ "method":"start",
                    "params": [                    
                    {   "route_from":"САНКТ-ПЕТЕРБУРГ",
                        "route_to":"МОСКВА",
                        "trains":[[1234567, "143"], [1273478, "577"]],
                        "car_type":1,
                        "emails":["s.stasishin@gmail.com", "stasishin@speechpro.com"],
                        "sms":["79062714417"],
                        "expires":12378789,
                        "period":3600
                    }]
                  }''')
res = simplejson.loads(res_str)
print res                
if res == -1:
    print "Server error:", bot.HTTPError
elif res == 1:
    print "Express-3 error:", bot.errorText
elif res == 2:
    text = ""
    for i in range(len(bot.options)):
        text = text + '<b>' + bot.options[i][0] + '</b> - ' + '<i>' + bot.options[i][1] + '</i><br/>'
    testMailer = mailer.Mailer()
    testMailer.send("robot@rzdtickets.ru", ["s.stasishin@gmail.com"], "Тестовое сообщение", "html", text)
elif res == 3:
    print "Error: date range is too large"
else:
    print "OK"
