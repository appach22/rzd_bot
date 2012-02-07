#coding=UTF-8

import sys
import os
from HTMLParser import HTMLParser

class ProxyParser(HTMLParser):

    def prepare(self):
        self.h = 0
        self.inTable = False
        self.inTr = False
        self.inIP = False
        self.inPort = False
        self.wasIP = False
        self.gotProxy = False
        self.count = 0
        self.ip = ""
        self.port = ""
        self.fd = open("/tmp/proxies.list", "w")

    def handle_starttag(self, tag, attrs):
      if tag == "table" :
        self.inTable = True
      if tag == "tr" and self.inTable :
        self.inTr = True
      if tag == "span" and self.inTr :
        self.count += 1
        if self.count == 2:
            self.inIP = True
            self.wasIP = True
      if tag == "td" and self.wasIP :
        self.inPort = True
        self.wasIP = False


    def handle_endtag(self, tag):
        if tag == "tr" and self.inTable and self.gotProxy:
            self.fd.write("%s:%d\n" % (self.ip, int(self.port)))
            self.inIP = False
            self.inPort = False
            self.inTr = False
            self.gotProxy = False
            self.ip = ""
            self.port = ""
            self.count = 0
        if tag == "table":
            self.inTable = False
            self.fd.close()

    def handle_data(self, data):
        if self.inIP:
            self.ip = data
            self.inIP = False
            #print data
        if self.inPort:
            self.port = data
            self.inPort = False
            self.gotProxy = True
            #print data

os.system("""wget --post-data="a%5B%5D=3&a%5B%5D=4&ac=on&c%5B%5D=China&c%5B%5D=Indonesia&c%5B%5D=Brazil&c%5B%5D=United%20States&c%5B%5D=Colombia&c%5B%5D=Iran&c%5B%5D=Russian%20Federation&c%5B%5D=India&c%5B%5D=Korea%2C%20Republic%20of&c%5B%5D=Turkey&c%5B%5D=Argentina&c%5B%5D=Egypt&c%5B%5D=Chile&c%5B%5D=Thailand&c%5B%5D=Taiwan%2C%20Republic%20of%20China&c%5B%5D=Venezuela&c%5B%5D=Germany&c%5B%5D=Poland&c%5B%5D=Hong%20Kong&c%5B%5D=Ukraine&c%5B%5D=Ecuador&c%5B%5D=Peru&c%5B%5D=Czech%20Republic&c%5B%5D=Canada&c%5B%5D=Nigeria&c%5B%5D=South%20Africa&c%5B%5D=Japan&c%5B%5D=Romania&c%5B%5D=Malaysia&c%5B%5D=Italy&c%5B%5D=Bangladesh&c%5B%5D=Sweden&c%5B%5D=Mexico&c%5B%5D=Latvia&c%5B%5D=Austria&c%5B%5D=Hungary&c%5B%5D=Kenya&c%5B%5D=Qatar&c%5B%5D=Serbia&c%5B%5D=Moldova%2C%20Republic%20of&c%5B%5D=France&c%5B%5D=Philippines&c%5B%5D=Palestinian%20Territory%2C%20Occupied&c%5B%5D=Lebanon&c%5B%5D=United%20Arab%20Emirates&c%5B%5D=Viet%20Nam&c%5B%5D=Bulgaria&c%5B%5D=Denmark&c%5B%5D=Netherlands&c%5B%5D=Bosnia%20and%20Herzegovina&c%5B%5D=Paraguay&c%5B%5D=United%20Kingdom&c%5B%5D=Slovakia&c%5B%5D=Norway&c%5B%5D=Spain&c%5B%5D=Greece&c%5B%5D=Azerbaijan&c%5B%5D=Macedonia&c%5B%5D=Pakistan&c%5B%5D=Cambodia&c%5B%5D=Iraq&c%5B%5D=Honduras&c%5B%5D=Malta&c%5B%5D=Europe&c%5B%5D=Brunei%20Darussalam&c%5B%5D=Kuwait&c%5B%5D=Puerto%20Rico&c%5B%5D=Zambia&c%5B%5D=Afghanistan&c%5B%5D=Switzerland&c%5B%5D=Albania&c%5B%5D=Slovenia&c%5B%5D=Lithuania&c%5B%5D=Ghana&c%5B%5D=Kazakhstan&c%5B%5D=Sudan&c%5B%5D=Namibia&c%5B%5D=Georgia&c%5B%5D=Seychelles&c%5B%5D=Luxembourg&c%5B%5D=Asia%2FPacific%20Region&c%5B%5D=Algeria&c%5B%5D=Zaire&c%5B%5D=Botswana&c%5B%5D=Uganda&c%5B%5D=Cote%20D'Ivoire&c%5B%5D=Singapore&c%5B%5D=Israel&c%5B%5D=Ireland&c%5B%5D=Angola&c%5B%5D=Chad&c%5B%5D=Trinidad%20and%20Tobago&c%5B%5D=Saudi%20Arabia&c%5B%5D=Bolivia&c%5B%5D=Estonia&c%5B%5D=Armenia&c%5B%5D=Portugal&c%5B%5D=Benin&c%5B%5D=Australia&ct%5B%5D=2&ct%5B%5D=3&o=0&p=&pl=on&pp=2&pr%5B%5D=0&s=0&sortBy=date&sp%5B%5D=2&sp%5B%5D=3" -O /tmp/proxies.html http://www.hidemyass.com/proxy-list/search-226162""")
parser = ProxyParser()
parser.prepare()
f = open("/tmp/proxies.html", "r")
parser.feed(f.read())
f.close()
