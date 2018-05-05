from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden, UnreadablePostError
from django.core import serializers
from django.core.exceptions import PermissionDenied
from .models import Airport, Flight, UserProfile
from .forms import FlightForm
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
import numpy as np
import time
from django.db.models import Q, Count, Sum
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
import json


def get_airport(request, airport_id):
    airport = Airport.objects.get(pk=airport_id)
    return JsonResponse({
        'name': airport.name,
        'iata': airport.iata if airport.icao else " · ",
        'icao': airport.icao if airport.icao else " · ",
        'city': airport.city,
        'region': airport.region,
        'region_iso': airport.region_iso,
        'country': airport.country,
        'country_iso': airport.country_iso,
        'latitude': airport.latitude,
        'longitude': airport.longitude,
        'elevation': airport.elevation
    })
    
    
def get_airport_flights(request, username, airport_id):
    user = User.objects.get(username=username)
    airport = Airport.objects.get(pk=airport_id)
    
    flights = Flight.objects.filter(owner=user).filter(Q(origin=airport) | Q(destination=airport))
    
    flights_dictionary = [
        {"number": flight.number,
         "origin": str(flight.origin),
         "destination": str(flight.destination),
         "direction": 'departure' if flight.origin.pk == airport_id else 'arrival',
         'city': flight.origin.city if flight.destination.pk == airport_id else flight.destination.city,
         "date": str(flight.date),
         "airline": flight.airline,
         "plane": flight.aircraft,
         'registration': flight.aircraft_registration,
         'picture': flight.picture_link,
         'distance': int(flight.distance),
         'duration': np.round((30.0 + flight.distance/500.0 * 60.0) / 60.0),
         'operator': flight.operator,
         'seat': flight.seat,
         'class': flight.travel_class,
         'origin_lat': flight.origin.latitude,
         'destination_lat': flight.destination.latitude,
         'origin_long': flight.origin.longitude,
         'destination_long': flight.destination.longitude,
         'airport_pk': airport_id
        } 
        for flight in flights[::-1]
    ]
    
    return JsonResponse(flights_dictionary, safe=False)
    
@csrf_exempt # This disables all CSRF security, please fix as soon as possible (JS fetch POSTs without credentials...)
def search_airports(request):
    if request.method == 'POST':
        try: 
            airport = Airport.objects.get(iata=request.body.decode('utf-8').strip().upper())
            # if multiple hits, take the most recent
            # if no iata, not possible from this function
            return JsonResponse({'status': 1, 'name': airport.name, 'iata': airport.iata, 'pk': airport.pk})
        except:
            return JsonResponse({'status': 0});