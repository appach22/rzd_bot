# coding=UTF-8

from HTMLParser import HTMLParser
import sys

class MZAParser(HTMLParser):

    def prepare(self):
        self.h = 0
        self.inType = False
        self.inHeader = False
        self.inPlaces = False
        self.inCar = False
        self.count = 0
        self.err = 0
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
        data = unicode(data, "UTF-8")
        if data.find(u"Плацкартный") != -1:
          self.inType = True
          self.carType = 1
        elif data.find(u"Купейный") != -1:
          self.inType = True
          self.carType = 2
        elif data.find(u"Вагон СВ") != -1:
          self.inType = True
          self.carType = 3
      if self.inPlaces :
        data = unicode(data, "UTF-8")
        pos = data.find(u"Свободные места: ")
        if pos != -1 :
          places = [self.parsePlace(s) for s in data[pos+17:].split(", ")]
          self.result.append([self.car, self.carType, places])
          self.count += len(places)
      if self.inCar :
        data = unicode(data, "UTF-8")
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
        self.feed(page)
        return self.err
