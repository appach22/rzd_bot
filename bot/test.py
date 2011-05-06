#coding=utf-8

from datetime import date
import time
import simplejson
from bot import Bot
from trackingData import TrackingData
import sys

bot = Bot()
##res_str = bot.call('''{ "method":"stop",
##                        "params":[123460, "s.stasishin@gmail.com"]}
##                   ''')
##print res_str
##sys.exit(0)
res_str = bot.call('''{ "method":"start",
                    "params": [
                    {   "route_from":"САНКТ-ПЕТЕРБУРГ",
                        "route_to":"МОСКВА",
                        "trains":[[1305147600, "055А"],
                                  [1305320400, "049А"],
                                  [1305234000, "117А"],
                                  [1305147600, "051А"],
                                  [1305234000, "135А"],
                                  [1305234000, "111А"],
                                  [1305147600, "055А"],
                                  [1305320400, "175Н"],
                                  [1305320400, "175Н"],
                                  [1305320400, "145А"],
                                  [1305320400, "081М"],
                                  [1305320400, "121А"],
                                  [1305320400, "199А"],
                                  [1305147600, "055А"], 
                                  [1305147600, "055А"], 
                                  [1305511100, "121А"],
                                  [1305511100, "333А"],
                                  [1305234000, "029А"],
                                  [1305147600, "051А"]],
                        "car_type":1,
                        "emails":["s.stasishin@gmail.com", "stasishin@speechpro.com"],
                        "sms":[],
                        "expires":12378789,
                        "period":60,
                        "uid":123474
                    }]
                  }''')
ret = simplejson.loads(res_str)
if ret["error"] != None:
    print "Error:", ret["error"]
else:
    res = ret["result"]
    res_code = res["code"]
    if res_code == 1:
        print "Express-3 error in position", res["TrainIndex"]
        print res["ExpressError"].encode("utf-8")
    elif res_code == 3:
        print res["HTTPError"].encode("utf-8")
    elif res_code == 2:
        print "Ambiguous train number in position", res["TrainIndex"]
        options = res["TrainOptions"]
        for i in range(len(options)):
            print options[i][0].encode("utf-8"), "-", options[i][1].encode("utf-8")
    elif res_code == 0:
        print "OK!"
        
        time.sleep(60)
        res_str = bot.call('''{ "method":"stop",
                        "params":[123474, "s.stasishin@gmail.com"]}
                   ''')
        print res_str
