##coding=utf-8

from datetime import date
import simplejson
import pickle
import MySQLdb

host = "localhost"
database = "rzdbot"
user = "root"
passw = "123456"

class TrackingData:
    
    def __init__(self):
        self.route_from = ""
        self.route_to = ""
        self.trains = []
        self.car_type = 0
        self.emails = []
        self.sms = []
        self.expires = date.today()
        self.period = 300
        self.uid = 0
        self.pid = -1
        self.username = ""
        self.ip_addr = ""
        self.sms_count = 0
        
    def getPostAsDict(self, index):
        train = self.trains[index]
        return {"TrainPlaces_DepDate" : train[0].strftime("%d.%m.%Y"),
                "TrainPlaces_StationFrom" : self.route_from,
                "TrainPlaces_StationTo" : self.route_to,
                "TrainPlaces_TrainN" : train[1],
                "spr" : "TrainPlaces", 
                "submit_TrainPlaces" : "Показать"}

    def getPostAsString(self, index):
        train = self.trains[index]
        return  "TrainPlaces_DepDate=" + train[0].strftime("%d.%m.%Y") + \
                "&TrainPlaces_StationFrom=" + self.route_from + \
                "&TrainPlaces_StationTo=" + self.route_to + \
                "&TrainPlaces_TrainN=" + train[1] + \
                "&spr=TrainPlaces" + \
                "&submit_TrainPlaces=Показать"
                
    def getAllPosts(self):
        posts = []
        for i in range(len(self.trains)):
            posts.append(self.getPost(i))
        return posts
    
    def saveToFile(self, name):
        try:
            file = open(name, "w")
        except IOError:
            return False
        
        pickle.dump(self, file);
        file.close()    
        
    def loadFromFile(self, name):
        try:
            file = open(name, "r")
        except IOError:
            return False
        
        return pickle.load(file);
    
    def loadFromDict(self, dict):
        try:
            self.route_from = dict["route_from"].encode("utf-8")
            self.route_to = dict["route_to"].encode("utf-8")
            raw_trains = dict["trains"]
            for i in range(len(raw_trains)):
                self.trains.append([date.fromtimestamp(raw_trains[i][0]), raw_trains[i][1].encode("utf-8")])
            for i in range(3 - len(raw_trains)):
                self.trains.append([date.fromtimestamp(0), ""])
            self.car_type = dict["car_type"]
            self.emails = dict["emails"]
            self.sms = dict["sms"]
            self.expires = date.fromtimestamp(dict["expires"])
            self.period = dict["period"]
            self.uid = dict["uid"]
        except:
            raise
        
    def saveToDB(self):
        try:
            conn = MySQLdb.connect(host = host,
                                   user = user,
                                   passwd = passw,
                                   db = database,
                                   charset = "utf8", 
                                   use_unicode = True)
        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            return False
        else:
            try:
                cursor = conn.cursor()
            except MySQLdb.Error, e:
                print "Error %d: %s" % (e.args[0], e.args[1])
                return False
            else:
                try:    
                    date1 = date2 = date3 = "0000-00-00"
                    trains1 = trains2 = trains3 = ""
                    if len(self.trains) > 0:
                        date1 = self.trains[0][0].strftime("%Y-%m-%d")
                        trains1 = self.trains[0][1]
                        if len(self.trains) > 1:
                            date2 = self.trains[1][0].strftime("%Y-%m-%d")
                            trains2 = self.trains[1][1]
                            if len(self.trains) > 2:
                                date3 = self.trains[2][0].strftime("%Y-%m-%d")
                                trains3 = self.trains[2][1]
                                
                    query = """INSERT INTO bot_static_info 
                                (uid, username, emails, sms, creation_date,
                                 station_from, station_to, date1, trains1,
                                 date2, trains2, date3, trains3, car_type,
                                 ip_addr, sms_count)
                                 VALUES(%d, '%s', '%s', '%s', NOW(), '%s', '%s',
                                 '%s', '%s', '%s', '%s', '%s', '%s', %d, '%s', %d)""" % \
                                (self.uid, self.username, ','.join(str(n) for n in self.emails), 
                                 ','.join(str(n) for n in self.sms), 
                                 self.route_from, self.route_to, date1, trains1,
                                 date2, trains2, date3, trains3, self.car_type,
                                 self.ip_addr, self.sms_count)
                    cursor.execute(query)

                    query = """INSERT INTO bot_dynamic_info
                            (uid, pid, expiration_date)
                            VALUES(%d, %d, '%s')""" % \
                            (self.uid, self.pid, self.expires.strftime("%Y-%m-%d"))
                    cursor.execute(query)
                    
                except MySQLdb.Error, e:
                    print "Error %d: %s" % (e.args[0], e.args[1])
                    return False
                finally:
                    cursor.close()
            finally:
                conn.close()

        return True
        
