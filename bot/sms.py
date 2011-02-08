#coding=utf-8

from getter import Getter
import urllib2

class SMS():
    
    def send(self, sender, text, numbers):
        if not len(numbers):
            return
        request = """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>
                     <request>
                     <message>
                     <sender>""" + sender + """</sender>
                     <text>""" + text + "</text>"
        i = 1            
        for num in numbers:
            request += "<abonent phone=\"" + num + "\" number_sms=\"" + str(i) + "\"/>"
            i += 1
        request += """</message>
                      <security>
                      <login value=\"appach\" />
                      <password value=\"rzdtickets22\" />
                      </security>
                      </request>"""
        req = urllib2.Request(url='https://my.smskanal.ru/xml/',
                              data=request, headers={"Content-type": "text/xml; charset=\"utf-8\""})
        f = urllib2.urlopen(req)
        #TODO: проверять ответ
        #print f.read()
