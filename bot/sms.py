#coding=utf-8

from getter import Getter
import urllib2

class SMS():
    
    def send(self, sender, text, data):
        numbers = data.sms
        if not len(numbers):
            return
        request = """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>
                     <request>
                     <message>
                     <sender>""" + sender + """</sender>
                     <text>""" + text + "</text>"
        i = 1
        for num in numbers:
            request += '<abonent phone="%s" number_sms="%d"/>' % (num, i)
            i += 1
        request += """</message>
                      <security>
                      <login value=\"appach\" />
                      <password value=\"rzdtickets22\" />
                      </security>
                      </request>"""
        try:
            req = urllib2.Request(url='https://my.smskanal.ru/xml/',
                                  data=request, headers={"Content-type": "text/xml; charset=\"utf-8\""})
            f = urllib2.urlopen(req)
            #TODO: проверять ответ (необходимо для случая нескольких номеров)
            #print f.read()
            data.incrementSmsCount()
        except urllib2.HTTPError as err:
            print "HTTP error %s during SMS send" % str(err.code)
        except urllib2.URLError as err:
            print "URL error %s during SMS send" % str(err.reason)
        except:
            print "Database error during SMS send"
