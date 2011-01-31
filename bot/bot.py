from datetime import date
from datetime import timedelta
from multiprocessing import Process
import os

import pageChecker
import mailer
import getter
import trackingData

    
    
class Bot:
    """The main class"""
    
    post_data = []

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
            page_getter = getter.Getter()
            if not page_getter.postRequest("www.mza.ru", "/?exp=1", data.getPost(i)):
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
        
        #return on error
        if res != 0:    
            return res
        
        data.expires = sorted(data.trains)[len(data.trains) - 1][0] + timedelta(1)
        
        #start new bot
        p = Process(target = self.newTracking, args = (data, ))
        p.start()
            
        return 0
    
    def newTracking(self, data):
        data.saveToFile("./pending/" + str(os.getpid()))
        
    def run(self, route_from, route_to, dates_and_trains, car_type):
        
        print os.getpid()


