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
from django.core import serializers
from django.utils import dateformat

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
         'airport_pk': airport_id,
         'origin_pk': flight.destination.pk,
         'destination_pk': flight.origin.pk,
         'pk': flight.pk,
        }
        for flight in flights[::-1]
    ]

    return JsonResponse(flights_dictionary, safe=False)

def get_route(request, id1, id2):
    airport1 = Airport.objects.get(pk=id1)
    airport2 = Airport.objects.get(pk=id2)
    return JsonResponse({
        'origin_name': airport1.name,
        'origin_iata': airport1.iata if airport1.icao else " · ",
        'origin_icao': airport1.icao if airport1.icao else " · ",
        'origin_city': airport1.city,
        'origin_region': airport1.region,
        'origin_region_iso': airport1.region_iso,
        'origin_country': airport1.country,
        'origin_country_iso': airport1.country_iso,
        'origin_latitude': airport1.latitude,
        'origin_longitude': airport1.longitude,
        'origin_elevation': airport1.elevation,
        'destination_name': airport2.name,
        'destination_iata': airport2.iata if airport2.icao else " · ",
        'destination_icao': airport2.icao if airport2.icao else " · ",
        'destination_city': airport2.city,
        'destination_region': airport2.region,
        'destination_region_iso': airport2.region_iso,
        'destination_country': airport2.country,
        'destination_country_iso': airport2.country_iso,
        'destination_latitude': airport2.latitude,
        'destination_longitude': airport2.longitude,
        'destination_elevation': airport2.elevation,
        'distance': int(airport1.distance_to(airport2)),
        'duration': np.round((30.0 + airport1.distance_to(airport2)/500.0 * 60.0) / 60.0),
    })

def get_route_flights(request, username, id1, id2):
    user = User.objects.get(username=username)
    airport1 = Airport.objects.get(pk=id1)
    airport2 = Airport.objects.get(pk=id2)
    flights = Flight.objects.filter(owner=user).filter(Q(origin=airport1,destination=airport2) | Q(destination=airport1,origin=airport2))

    flights_dictionary = [
        {"number": flight.number,
         "origin": str(flight.origin),
         "destination": str(flight.destination),
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
         'origin_pk': flight.destination.pk,
         'destination_pk': flight.origin.pk,
         'origin_city': flight.origin.city,
         'destination_city': flight.destination.city,
         'pk': flight.pk,
        }
        for flight in flights[::-1]
    ]

    return JsonResponse(flights_dictionary, safe=False)

def get_flights(request, username):
    flights_list = Flight.objects.filter(owner__username=username).order_by('-sortid')

    flights_dictionary = [
        {"number": flight.number,
         "origin": str(flight.origin),
         "destination": str(flight.destination),
         'day': flight.date.strftime('%A'),
         'date': flight.date.strftime('%d %b %Y'),
         'daymonth': flight.date.strftime('%d %b'),
         'year': flight.date.strftime('%Y'),
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
         'origin_pk': flight.destination.pk,
         'destination_pk': flight.origin.pk,
         'origin_city': flight.origin.city,
         'destination_city': flight.destination.city,
         'pk': flight.pk,
         'origin_html_name': flight.origin.html_name(),
         'destination_html_name': flight.destination.html_name(),
        }
        for flight in flights_list
    ]

    return JsonResponse(flights_dictionary, safe=False)

def get_flight_details(request, id):
    flight = Flight.objects.get(pk=id)
    print(flight.aircraft)
    flight_dictionary = {
        'id': flight.pk,
        'number': flight.number,
        'day': flight.date.strftime('%A'),
        'date': dateformat.format(flight.date, 'jS F Y'),
        'isodate': flight.date,
        'origin': {
            'name': flight.origin.name,
            'iata': flight.origin.iata,
            'city': flight.origin.city,
            'country': flight.origin.country,
        },
        'destination': {
            'name': flight.destination.name,
            'iata': flight.destination.iata,
            'city': flight.destination.city,
            'country': flight.destination.country,
        },
        'distance': int(flight.distance),
        'duration': np.round((30.0 + flight.distance/500.0 * 60.0) / 60.0),
        'aircraft': flight.aircraft,
        'registration': flight.aircraft_registration,
        'airline': flight.airline,
        'operator': flight.operator,
        'class': flight.travel_class,
        'seat': flight.seat,
        'pictureLink': flight.picture_link,
        #'origin': serializers.serialize("json", [flight.origin]),
        #'destination': serializers.serialize("json", [flight.destination]),
    }

    return JsonResponse(flight_dictionary, safe=False)

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
