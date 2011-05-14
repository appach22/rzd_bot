##coding=utf-8

from datetime import date
from datetime import timedelta
import simplejson
import pickle
import MySQLdb

host = "localhost"
database = "rzdtickets.ru"
user = "root"
passw = "rzdtickets22"

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
        self.creation_date = date.fromtimestamp(0)
        
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
            temp_trains = []
            for i in range(len(raw_trains)):
                temp_trains.append([date.fromtimestamp(raw_trains[i][0]), raw_trains[i][1].encode("utf-8")])
            for i in range(3 - len(raw_trains)):
                temp_trains.trains.append([date.fromtimestamp(0), ""])
            # Удаляем повторы    
            temp_trains.sort()
            last = temp_trains[-1]
            for i in range(len(temp_trains)-2, -1, -1):
                if last == temp_trains[i]:
                    del temp_trains[i]
                else:
                    last = temp_trains[i]
            temp_trains.sort()
            # Вырезаем лишние даты
            dates = 0
            temp_trains1 = []
            for i in range(len(temp_trains)):
                if i > 0 and temp_trains[i][0] != temp_trains[i-1][0]:
                    dates += 1
                if dates >= 3:
                    break
                temp_trains1.append(temp_trains[i])
            # Вырезаем лишние поезда
            repeat = 0
            for i in range(len(temp_trains1)):
                if i > 0 and temp_trains1[i][0] == temp_trains1[i-1][0]:
                    repeat += 1
                else:
                    repeat = 0
                if (repeat < 5):
                    self.trains.append(temp_trains1[i])
            # Проверяем диапазон дат. Удаляем даты, выходящие за диапазон
            while (self.trains[len(self.trains) - 1][0] - self.trains[0][0]) > timedelta(2):
                del self.trains[len(self.trains) - 1]

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
                    dates = [] 
                    trains = []
                    all_trains = list(self.trains)
                    date1 = date2 = date3 = "0000-00-00"
                    trains1 = trains2 = trains3 = ""
                    i = 0
                    while len(all_trains):
                        dates.append(all_trains[0][0].strftime("%Y-%m-%d"))
                        trains_list = [t[1] for t in all_trains if t[0] == all_trains[0][0]]
                        trains.append(','.join(str(t) for t in trains_list))
                        j = 0
                        train = all_trains[0][0]
                        while j < len(all_trains):
                            if (all_trains[j][0] == train):
                                del all_trains[j]
                            else:
                                j += 1
                        
                        if len(dates) > 0:
                            date1 = dates[0]
                            trains1 = trains[0]
                            if len(dates) > 1:
                                date2 = dates[1]
                                trains2 = trains[1]
                                if len(dates) > 2:
                                    date3 = dates[2]
                                    trains3 = trains[2]
                                                                
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
        
    def loadFromDB(self, uid):
        try:
            conn = MySQLdb.connect(host = host,
                                   user = user,
                                   passwd = passw,
                                   db = database,
                                   charset = "utf8", 
                                   use_unicode = True)
        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            return 1
        else:
            try:
                cursor = conn.cursor()
            except MySQLdb.Error, e:
                print "Error %d: %s" % (e.args[0], e.args[1])
                return 1
            else:
                try:    
                    query = """SELECT * FROM bot_static_info WHERE uid = %d""" % uid
                    cursor.execute(query)
                    row = cursor.fetchone()
                    if row == None:
                        return 2
                    self.uid = row[0]
                    self.username = row[1]
                    self.emails = row[2].split(',')
                    self.sms = row[3].split(',')
                    self.creation_date = row[4]
                    self.route_from = row[5].encode("utf-8")
                    self.route_to = row[6].encode("utf-8")
                    trains = row[8].split(',')
                    for t in trains:
                        self.trains.append([row[7], t])
                    trains = row[10].split(',')
                    for t in trains:
                        self.trains.append([row[9], t])
                    trains = row[12].split(',')
                    for t in trains:
                        self.trains.append([row[11], t])
                    self.car_type = row[16]
                    self.ip_addr = row[17]
                    self.sms_count = row[18]
                    
                    print row[5].encode("utf-8")
##                    print "Found %d, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %d, %s, %d" % \
##                    (row[0], row[1], row[2], row[3], row[4], row[5].encode("utf-8"), row[6].encode("utf-8"), row[7],
##                     row[8], row[9], row[10], row[11], row[12], row[16], row[17], row[18])
                    print self.trains

                    query = """SELECT * FROM bot_dynamic_info WHERE uid = %d""" % uid
                    cursor.execute(query)
                    row = cursor.fetchone()
                    if not row == None:
                        self.pid = row[1]
                        self.expires = row[2]

                except MySQLdb.Error, e:
                    print "Error %d: %s" % (e.args[0], e.args[1])
                    return 1
                finally:
                    cursor.close()
            finally:
                conn.close()

        return 0

    def removeDynamicData(self):
        try:
            conn = MySQLdb.connect(host = host,
                                   user = user,
                                   passwd = passw,
                                   db = database,
                                   charset = "utf8", 
                                   use_unicode = True)
        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            return 1
        else:
            try:
                cursor = conn.cursor()
            except MySQLdb.Error, e:
                print "Error %d: %s" % (e.args[0], e.args[1])
                return 1
            else:
                try:    
                    query = """DELETE FROM bot_dynamic_info WHERE uid = %d""" % self.uid
                    cursor.execute(query)
                except MySQLdb.Error, e:
                    print "Error %d: %s" % (e.args[0], e.args[1])
                    return 1
                finally:
                    cursor.close()
            finally:
                conn.close()

        return 0
