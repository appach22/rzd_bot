#coding=utf-8

from datetime import date
from bot import Bot
from trackingData import TrackingData


data = TrackingData()
data.route_from = "САНКТ-ПЕТЕРБУРГ" 
data.route_to = "МОСКВА" 
data.trains.append([date(2011, 3, 3), "143А"])
data.trains.append([date(2011, 3, 1), "143А"])
data.emails.append("s.stasishin@gmail.com")
bot = Bot()
res = bot.start(data)
if res == -1:
    print "Server error:", bot.HTTPError
elif res == 1:
    print "Express-3 error:", bot.errorText
elif res == 2:
    text = ""
    for i in range(len(bot.options)):
        text = text + '<b>' + bot.options[i][0] + '</b> - ' + '<i>' + bot.options[i][1] + '</i><br/>'
    testMailer = mailer.Mailer()
    testMailer.send("robot@rzdtickets.ru", "s.stasishin@gmail.com", "Тестовое сообщение", "html", text)
elif res == 3:
    print "Error: date range is too large"
else:
    print "OK"
