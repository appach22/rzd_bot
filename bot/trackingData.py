#coding=utf-8

from datetime import date
from datetime import datetime
from datetime import timedelta
import simplejson
import pickle
from syslog import syslog
from db import db

class Train:
    
    def __init__(self, date, number):
        self.number = number
        self.date = date
        self.car_type = 255
        self.places_parity = 3
        self.places_range = [0, 120]
        self.prev = 0
        self.total_prev = 0

    def __cmp__(self, other):
        if self.date < other.date:
            return -1
        if self.date == other.date and self.number < other.number:
            return -1
        if self.date == other.date and self.number == other.number:
            return 0
        return 1

    def __repr__(self):
        return self.date.strftime("%d.%m.%Y") + ", " + self.number


class TrackingData:
    
    def __init__(self):
        self.route_from = ""
        self.route_to = ""
        self.id_from = 0
        self.id_to = 0
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
        self.script = ''
        self.places_parity = 3 #both, upper and lower
        self.places_range = [0, 200]
        self.db = db()
        
    def getStationId(self, station):
        if not self.db.query("SELECT station_code FROM `stations_t4you.ru` WHERE `station_name` LIKE '%s'" % station):
            return 0
        if len(self.db.rows) == 0:
            return 0
        return self.db.rows[0][0]

    def getPostAsDict(self, index):
        train = self.trains[index]
        if not self.id_from == 0:
            sfrom = str(self.id_from)
        else:
            sfrom = self.route_from
        if not self.id_to == 0:
            sto = str(self.id_to)
        else:
            sto = self.route_to
        return {"TrainPlaces_DepDate" : train.date.strftime("%d.%m.%Y"),
                "TrainPlaces_StationFrom" : sfrom,
                "TrainPlaces_StationTo" : sto,
                "TrainPlaces_TrainN" : train.number,
                "spr" : "TrainPlaces", 
                "submit_TrainPlaces" : "Показать"}

    def getPostAsString(self, train):
        if not self.id_from == 0:
            sfrom = str(self.id_from)
        else:
            sfrom = self.route_from
        if not self.id_to == 0:
            sto = str(self.id_to)
        else:
            sto = self.route_to
        return  "TrainPlaces_DepDate=" + train.date.strftime("%d.%m.%Y") + \
                "&TrainPlaces_StationFrom=" + sfrom + \
                "&TrainPlaces_StationTo=" + sto + \
                "&TrainPlaces_TrainN=" + train.number + \
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
            self.id_from = self.getStationId(self.route_from)
            self.id_to = self.getStationId(self.route_to)
            raw_trains = dict["trains"]
            temp_trains = []
            for i in range(len(raw_trains)):
                temp_trains.append(Train(date.fromtimestamp(raw_trains[i][0]), raw_trains[i][1].encode("utf-8")))
            #for i in range(3 - len(raw_trains)):
            #    temp_trains.trains.append([date.fromtimestamp(0), ""])
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
                if i > 0 and temp_trains[i].date != temp_trains[i-1].date:
                    dates += 1
                if dates >= 3:
                    break
                temp_trains1.append(temp_trains[i])
            # Вырезаем лишние поезда
            repeat = 0
            for i in range(len(temp_trains1)):
                if i > 0 and temp_trains1[i].date == temp_trains1[i-1].date:
                    repeat += 1
                else:
                    repeat = 0
                if (repeat < 5):
                    self.trains.append(temp_trains1[i])
            # Проверяем диапазон дат. Удаляем даты, выходящие за диапазон
            while (self.trains[len(self.trains) - 1].date - self.trains[0].date) > timedelta(2):
                del self.trains[len(self.trains) - 1]

            car_type = int(dict["car_type"])
            if car_type == 0:
                self.car_type = 255
            else:
                self.car_type = 1 << (car_type - 1)
            self.emails = list(dict["emails"])
            self.sms = list(dict["sms"])
            self.expires = self.trains[len(self.trains) - 1].date + timedelta(1)
            self.period = 300
            self.places_parity = dict["parity"]
            self.places_range = list(dict["range"])
            self.uid = 0
        except:
            raise
        
    def saveToDB(self):
        query = """INSERT INTO bot_static_info
                    (username, emails, sms, creation_date,
                     station_from, station_to, ip_addr, sms_count, period)
                     VALUES('%s', '%s', '%s', NOW(), '%s', '%s', '%s', %d, %d)""" % \
                     (self.username,
                     ','.join(str(n) for n in self.emails),
                     ','.join(str(n) for n in self.sms),
                     self.route_from, self.route_to,
                     self.ip_addr, self.sms_count, self.period)
        if not self.db.query(query):
            return False
        self.uid = self.db.lastrowid

        queries = []
        for train in self.trains:
            queries.append("""INSERT INTO trains
                (uid, number, date, car_type, places_parity,
                 places_range_low, places_range_high, prev, total_prev)
                VALUES(%d, '%s', '%s', %d, %d, %d, %d, %d, %d)""" % \
                (self.uid, train.number, train.date.strftime("%Y-%m-%d"),
                self.car_type, self.places_parity, self.places_range[0],
                self.places_range[1], train.prev, train.total_prev))
        if not self.db.queries(queries):
            return False

        query = """INSERT INTO bot_dynamic_info
                (uid, pid, expiration_date, script, next_request)
                VALUES(%d, %d, '%s', '%s', '%s')""" % \
                (self.uid, self.pid, self.expires.strftime("%Y-%m-%d"),
                self.script, self.next_request.strftime("%Y-%m-%d %H:%M:%S"))
        if not self.db.query(query):
            return False

        return True

    def loadFromDB(self, uid):
        if not self.db.query('SELECT * FROM bot_static_info WHERE uid = %d' % uid):
            return 1
        if len(self.db.rows) == 0:
            return 2
        row = self.db.rows[0]
        self.uid = row[0]
        self.username = row[1]
        self.emails = row[2].split(',')
        if len(row[3]):
            self.sms = row[3].encode('utf-8').split(',')
        else:
            self.sms = []
        self.creation_date = row[4]
        self.route_from = row[5].encode("utf-8")
        self.route_to = row[6].encode("utf-8")
        self.id_from = self.getStationId(self.route_from)
        self.id_to = self.getStationId(self.route_to)
        self.ip_addr = row[7]
        self.sms_count = row[8]
        self.period = row[9]

        if not self.db.query('SELECT * FROM trains WHERE uid = %d' % uid):
            return 1
        if len(self.db.rows) == 0:
            return 3
        for row in self.db.rows:
            train = Train(row[2], row[1].encode('utf-8'))
            train.car_type = self.car_type = row[3]
            train.places_parity = self.places_parity = row[4]
            train.places_range[0] = self.places_range[0] = row[5]
            train.places_range[1] = self.places_range[1] = row[6]
            train.prev = row[7]
            train.total_prev = row[8]
            self.trains.append(train)

        return 0

    def removeDynamicData(self):
        if not self.db.query('DELETE FROM bot_dynamic_info WHERE uid = %d' % self.uid):
            return 1
        return 0

    def getDynamicData(self, uid):
        if not self.db.query('SELECT * FROM bot_dynamic_info WHERE uid = %d' % uid):
            return False
        if len(self.db.rows) == 0:
            return False
        self.pid = self.db.rows[0][1]
        return True

    def updateDynamicData(self):
        self.next_request = datetime.today() + timedelta(seconds=self.period)
        if not self.db.query("UPDATE bot_dynamic_info SET pid = %d, next_request = '%s' WHERE uid = %d" % (self.pid,
                        self.next_request.strftime("%Y-%m-%d %H:%M:%S"), self.uid)):
            return 1
        return 0

    def updateTrain(self, train):
        if not self.db.query("UPDATE trains SET prev = %d, total_prev = %d WHERE uid = %d AND number = '%s' AND date = '%s'" \
                             % (train.prev, train.total_prev, self.uid, train.number, train.date.strftime('%Y-%m-%d'))):
            return 1
        return 0

    def incrementSmsCount(self):
        self.sms_count += 1
        if not self.db.query('UPDATE bot_static_info SET sms_count = %d WHERE uid = %d' % (self.sms_count, self.uid)):
            return 1
        return 0

    def getStationById(self, stationId):
        res = stationId
        if not self.db.query("SELECT `station_name`,`trainway_name` FROM `stations_t4you.ru` WHERE `station_code`='%s'" % (stationId)):
            return ""
        if len(self.db.rows) == 0:
            return ""
        res = self.db.rows[0][0] + ' (' + stationId + '), ' + self.db.rows[0][1]
        return res
