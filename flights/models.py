from django.db import models
from django.contrib.auth.models import User
import math

class Airport(models.Model):
    iata = models.CharField('IATA', max_length=3, blank=True)
    icao = models.CharField('ICAO', max_length=4, blank=True)
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100, blank=True)
    region_iso = models.CharField('Region code', max_length=10, blank=True, help_text='ISO 3166-2')
    country = models.CharField(max_length=100)
    country_iso = models.CharField('Country code', max_length=100, help_text='ISO 3166-1 alpha-2')
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

    def html_name(self):
        if self.country in ['United States', 'United Kingdom', 'Australia', 'Germany', 'Canada', 'Italy', 'Switzerland', 'China', 'United Arab Emirates']:
            location = self.city + ', ' + self.region + ', ' + self.country
        else:
            location = self.city + ', ' + self.country
        return '<abbr title="' + self.name + ', ' + location + '">' + str(self) + '</abbr>'

    def distance_to(self, airport, dim='mi'):
        lat1 = self.latitude * math.pi/180.0
        lat2 = airport.latitude * math.pi/180.0
        lon1 = self.longitude * math.pi/180.0
        lon2 = airport.longitude * math.pi/180.0

        theta = lon2 - lon1
        distance = math.acos(math.sin(lat1) * math.sin(lat2) + math.cos(lat1) * math.cos(lat2) * math.cos(theta))

        if distance < 0:
            distance = -1 * distance

        if dim == 'mi':
            return distance * 3959.0
        elif dim == 'km':
            return distance * 6371.0
        else:
            raise ValueError('Invalid dimensions')

class Flight(models.Model):
    origin = models.ForeignKey('Airport', on_delete=models.PROTECT, related_name='origins')
    destination = models.ForeignKey('Airport', on_delete=models.PROTECT, related_name='destinations')
    date = models.DateField(blank=True, null=True, help_text='YYYY-MM-DD')
    number = models.CharField(max_length=10, blank=True)
    airline = models.CharField(max_length=100, blank=True)
    aircraft = models.CharField(max_length=100, blank=True)
    aircraft_registration = models.CharField(max_length=10, blank=True)
    distance = models.FloatField(default=-1)

    travel_class = models.CharField(max_length=100, blank=True)
    seat = models.CharField(max_length=10, blank=True)
    operator = models.CharField(max_length=100, blank=True)
    comments = models.TextField(max_length=10000, blank=True)

    sortid = models.IntegerField(default=-1) # Assigned manually at creation
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owners')

    picture = models.ImageField(upload_to='flights/user_pics', blank=True)
    picture_link = models.URLField(blank=True)

    def calculate_distance(self, dim='mi'):
        return self.origin.distance_to(self.destination, dim)

    def set_distance(self):
        self.distance = self.calculate_distance()
        self.save()

    def nice_distance(self):
        return format(round(self.distance()), ",")

class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='profile', on_delete=models.PROTECT)
    public = models.BooleanField(default=True)
    years_only = models.BooleanField(default=False)
    public_delay = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return 'Profile of user: {}'.format(self.user.username)
