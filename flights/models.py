from django.db import models
from django.contrib.auth.models import User
import math

class Airport(models.Model):
    iata = models.CharField(max_length=3, blank=True)
    icao = models.CharField(max_length=4, blank=True)
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    elevation = models.FloatField()
    opened = models.DateField(blank=True, null=True, help_text='YYYY-MM-DD')
    closed = models.DateField(blank=True, null=True, help_text='YYYY-MM-DD')
    
    def __str__(self):
        if self.iata is not '':
            return self.iata
        elif self.icao is not '':
            return self.icao
        else:
            return self.name[:4] + '...'
    
    def distance_to(self, airport):
        lat1 = self.latitude
        lat2 = airport.latitude
        lon1 = self.longitude
        lon2 = airport.longitude
        
        theta = lon2 - lon1
        distance = math.acos(math.sin(lat1) * math.sin(lat2) + math.cos(lat1) * math.cos(lat2) * math.cos(theta))
        if distance < 0:
            distance = distace + math.pi
        distance = distance * 6371.2 
        
        return distance