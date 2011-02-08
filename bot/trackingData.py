﻿from datetime import date
import pickle

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
##        file.write("<bot>\n")
##        file.write("<from>" + self.route_from + "</from>\n")
##        file.write("<to>" + self.route_to + "</to>\n")
##        file.write("<trains>\n")
##        for i in range(len(self.trains)):
##            file.write("<train><date>" + self.trains[i][0].strftime("%d.%m.%Y") + "</date>")
##            file.write("<number>" + self.trains[i][1] + "</number></train>\n")
##        file.write("</trains>\n")
##        file.write("<car_type>" + str(self.car_type) + "</car_type>\n")
##        file.write("<period>" + str(self.period) + "</period>\n")
##        file.write("<expires>" + self.expires.strftime("%d.%m.%Y") + "</expires>\n")
##        file.write("<emails>\n")
##        for i in range(len(self.emails)):
##            file.write("<email>" + self.emails[i] + "</email>\n")
##        file.write("</emails>\n")
##        file.write("<sms>" + self.sms + "</sms>\n")
##        file.write("</bot>\n")
        file.close()    
        
    def loadFromFile(self, name):
        try:
            file = open(name, "r")
        except IOError:
            return False
        
        return pickle.load(file);
