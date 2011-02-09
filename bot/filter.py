#coding=utf-8

class PlacesFilter:
    
    def applyFilter(self, places, data):
        self.filteredPlaces = []
        count = 0
        if data.car_type == 0:
            self.filteredPlaces = places
        else:
            self.filteredPlaces = [car for car in places if car[1] == data.car_type]
            
        return self.getCount(self.filteredPlaces)
    
    def getCount(self, places):
        count = 0
        for car in places:
            count += len(car[2])
        return count
        