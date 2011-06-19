#coding=utf-8

from copy import deepcopy

class PlacesFilter:
    def applyFilter(self, places, data):
        self.totalPlaces = []
        count = 0
        # Match car type
        if data.car_type == 0:
            self.totalPlaces = list(places)
        else:
            self.totalPlaces = [car for car in places if car[1] == data.car_type]
        # Match places range and parity
        self.filteredPlaces = deepcopy(self.totalPlaces)
        for car in self.filteredPlaces:
            for i in range(len(car[2]) - 1, -1, -1):
                place = car[2][i]
                if place[0] < data.places_range[0] or place[0] > data.places_range[1]:
                    car[2].remove(place)
                else:
                    parity = place[0] % 2
                    if parity == 0 and (data.places_parity & 2) == 0:
                        car[2].remove(place)
                    elif parity == 1 and (data.places_parity & 1) == 0:
                        car[2].remove(place)

    def getCount(self, places):
        count = 0
        for car in places:
            count += len(car[2])
        return count

    def getMatchedCount(self):
        return getCount(self.filteredPlaces)

    def getTotalCount(self):
        return getCount(self.totalPlaces)
