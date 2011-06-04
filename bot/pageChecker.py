#coding=UTF-8

from HTMLParser import HTMLParser

class MZAErrorChecker(HTMLParser):

    err = 255
    errorText = ''
    inError = False
    isStationError = False
    inSelect = False
    inOption = False
    station = ''
    options = []

    def handle_starttag(self, tag, attrs):
        if self.err == 255:
            self.err = 0
        if tag == "div" and len(attrs) > 0 and attrs[0][1] == "error":
            self.inError = True
        elif tag == "select" and not len(self.errorText):
            self.inSelect = True
            self.errorText = 'Уточните название станции'
            if len(self.station):
                self.stationNum = 2
            else:
                self.stationNum = 1
        elif self.inSelect and tag == "option":
            self.inOption = True
            for i in attrs:
                if i[0] == "value":
                    self.options.append([i[1]])
                    break
        # Save station name
        elif tag == "input" and not len(self.errorText):
            iclass = ''
            ivalue = ''
            for attr in attrs:
                if attr[0] == 'class':
                    iclass = attr[1]
                elif attr[0] == 'value':
                    ivalue = attr[1].strip()
            if iclass == 'station' and len(ivalue):
                self.station = ivalue
        elif tag == "div" and len(attrs) > 0 and attrs[0][1] == "validation":
            if not len(self.errorText):
                self.inError = True
                self.isStationError = True
            
    def handle_endtag(self, tag):
        if tag == "select":
            self.inSelect = False
            self.err = 2
        elif tag == "option":
            self.inOption = False
        elif self.inError and tag == "div":
            self.inError = False
            if self.isStationError:
                self.err = 3
            else:
                self.err = 1

    def handle_data(self, data):
        if self.inError:
            self.errorText = data
            if self.errorText.find("2021") != -1: #ignore "Мест нет" error
                self.inError = False
        if self.inOption:
            self.options[len(self.options) - 1].append(data)

    def CheckPage(self, page):
        self.err = 255
        self.feed(page.decode('utf-8'))
        return self.err
