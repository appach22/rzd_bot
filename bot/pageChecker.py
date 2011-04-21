#coding=UTF-8

from HTMLParser import HTMLParser

class MZAErrorChecker(HTMLParser):

    err = 0
    errorText = ""
    inError = False
    inSelect = False
    inOption = False
    options = []
    
    def handle_starttag(self, tag, attrs):
        if tag == "div" and len(attrs) > 0 and attrs[0][1] == "error":
            self.inError = True
        if tag == "select":
            self.inSelect = True
        if self.inSelect and tag == "option":
            self.inOption = True
            for i in attrs:
                if i[0] == "value":
                    self.options.append([i[1]])
                    break

    def handle_endtag(self, tag):
        if tag == "select":
            self.inSelect = False
            self.err = 2
        elif tag == "option":
            self.inOption = False
        elif self.inError and tag == "div":
            self.inError = False
            self.err = 1

    def handle_data(self, data):
        if self.inError:
            self.errorText = data
            if self.errorText.find("2021") != -1: #ignore "Мест нет" error
                self.inError = False
        if self.inOption:
            self.options[len(self.options) - 1].append(data)

    def CheckPage(self, page):
        self.err = 0
        self.feed(page)
        return self.err
