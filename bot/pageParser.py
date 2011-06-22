#coding=UTF-8

import sys
from HTMLParser import HTMLParser

class MZAParser(HTMLParser):

    def prepare(self):
        self.h = 0
        self.inType = False
        self.inHeader = False
        self.inPlaces = False
        self.inCar = False
        self.count = 0
        self.err = 0
        self.carType = 0
        self.result = []

    def handle_starttag(self, tag, attrs):
      if tag == "h3" :
        self.h = 1
      if tag == "td" and len(attrs) > 0 :
        self.inHeader = False
        self.inPlaces = False
        self.inCar = False
        td_class = attrs[0][1]
        if td_class == "h" :
          self.inHeader = True
          self.prices = []
        if td_class == "tb" and self.inType :
          self.inPlaces = True
        if td_class == "bb" and self.inType :
          self.inCar = True


#    def handle_endtag(self, tag):
#        print "Encountered the end of a %s tag" % tag

    def handle_data(self, data):
      if self.h == 1 :
        self.h = 0
      if self.inHeader :
        if data.find(u"Сидячий") != -1:
          self.inType = True
          self.carType = 1
          self.carName = data.encode('utf-8')
        elif data.find(u"Плацкартный") != -1:
          self.inType = True
          self.carType = 2
          self.carName = data.encode('utf-8')
        elif data.find(u"Купейный") != -1:
          self.inType = True
          self.carType = 3
          self.carName = data.encode('utf-8')
        elif data.find(u"Вагон СВ") != -1:
          self.inType = True
          self.carType = 4
          self.carName = data.encode('utf-8')
        elif data.find(u"Стоимость:") != -1:
          self.prices.append((data.split(' ')[1]).encode('utf-8'))
      if self.inPlaces :
        pos = data.find(u"Свободные места: ")
        if pos != -1 :
          places = [self.parsePlace(s) for s in data[pos+17:].split(", ")]
          self.result.append([self.car, self.carType, places, self.prices, self.carName])
          self.count += len(places)
      if self.inCar :
        pos = data.find(u"вагон №: ")
        if pos != -1 :
          self.car = int(data[pos+9:pos+11])
        
    def parsePlace(self, place):
        p = int(place[0:3])
        if len(place) < 4:
            return [p]
        t = -1
        if (place[3] == u"Ц"):
            t = 0
        elif (place[3] == u"М"):
            t = 1
        elif (place[3] == u"Ж"):
            t = 2
        elif (place[3] == u"С"):
            t = 3
        return [p, t]

    def ParsePage(self, page):
        self.prepare()
        self.feed(page.decode('utf-8'))
        return self.err

class MZATrainsListParser(HTMLParser):

    def prepare(self):
        self.inList = False
        self.inTrain = False
        self.column = 0
        self.currentData = ""
        self.currentTrain = {}
        self.trainsList = []

    def handle_starttag(self, tag, attrs):
      if tag == "h3" :
        self.inList = True
        self.trainsList = []
      if tag == "tr" and self.inList :
        self.inTrain = True
        self.column = 0
        self.currentTrain = {}
      if tag == "td" and self.inTrain :
        if len(attrs) == 0 :
          self.column += 1
          self.currentData = ""
        else :
          self.inTrain = False

    def handle_endtag(self, tag):
        if self.inTrain and tag == "td":
            if self.column == 1:
                self.currentTrain['train'] = self.currentData
            elif self.column == 2:
                self.currentTrain['departure'] = self.currentData
            elif self.column == 3:
                self.currentTrain['arrival'] = self.currentData
            elif self.column == 4:
                self.currentTrain['onway'] = self.currentData
            elif self.column == 6:
                self.currentTrain['vip'] = self.currentData

        if self.inTrain and tag == "tr":
            if len(self.currentTrain):
                self.trainsList.append(self.currentTrain)
            self.inTrain = False
            self.column = 0
        if self.inList and tag == "div":
            self.inList = False
            self.inTrain = False

    def handle_data(self, data):
        if self.column > 0:
            self.currentData += data
            self.currentData += " "

    def GetTrainsList(self, page):
        self.prepare()
        self.feed(page.decode('utf-8'))
        return self.trainsList

