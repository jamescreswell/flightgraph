from django.db import models
from django.contrib.auth.models import User

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