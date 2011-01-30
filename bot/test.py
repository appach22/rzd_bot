from datetime import date
from datetime import timedelta
import PageChecker
import mailer
import getter

class Bot:
    """The main class"""

    def run(self, route_from, route_to, dates_and_trains, car_type):
        # Проверяем диапазон дат    
        dates = sorted(dates_and_trains.keys())
        if (dates[len(dates) - 1] - dates[0]) > timedelta(2):
            return 3 #Date range is too large
        # Проверяем на корректность номера поездов и даты
        checker = PageChecker.MZAErrorChecker()
        res = 0
        self.itemIndex = -1
        for d, t in dates_and_trains.items():
            self.itemIndex += 1
            post_data = {"TrainPlaces_DepDate" : d.strftime("%d.%m.%Y"),
                         "TrainPlaces_StationFrom" : route_from,
                         "TrainPlaces_StationTo" : route_to,
                         "TrainPlaces_TrainN" : t,
                         "spr" : "TrainPlaces", 
                         "submit_TrainPlaces" : "Показать"}
            page_getter = getter.Getter()
            if not page_getter.postRequest("www.mza.ru", "/?exp=1", post_data):
                res = -1; #server error: check Bot.HTTPError
                self.HTTPError = page_getter.status
                break
            res = checker.CheckPage(page_getter.data)
            if res == 1: #express-3 request error: check Bot.errorText
                self.errorText = checker.errorText
                break
            elif res == 2: #train number is ambiguous: check Bot.options
                self.options = checker.options
                break
            
        return res


bot = Bot()
dates = [date(2011, 3, 1)]
res = bot.run("ВАРШАВА", "МОСКВА", {dates[0]: "143А"}, 1)
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