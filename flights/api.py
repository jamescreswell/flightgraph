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
import datetime
from django.db.models import Q, Count, Sum
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
import json
from django.core import serializers
from django.utils import dateformat
import matplotlib
matplotlib.use('Agg') # Server has no GUI
import matplotlib.pyplot as plt
#from mpl_toolkits.basemap import Basemap
import datetime # I hope this doesn't mess up the Django datetime ...

@login_required
def add_flight(request):
    payload = json.loads(request.body)
    user = request.user
    try:
        origin_airport = Airport.objects.get(pk=payload['origin_pk'])
        destination_airport = Airport.objects.get(pk=payload['destination_pk'])
        try:
            next_sortid = Flight.objects.filter(owner=request.user).order_by('-sortid')[0].sortid + 1
        except:
            next_sortid = 0
        #print("Printing payload['image_file']...")
        #print(payload['image_file'])
        f = Flight(date = payload['date'],
                   number = payload['number'],
                   origin = origin_airport,
                   destination = destination_airport,
                   airline = payload['airline'],
                   aircraft = payload['aircraft'],
                   aircraft_registration = payload['registration'],
                   owner=request.user,
                   seat=payload['seat'],
                   travel_class=payload['class'],
                   operator=payload['operator'],
                   comments=payload['comments'],
                   picture_link=payload['image_link'],
                   #picture=payload['image_file'],
                   distance=-1.0,
                   sortid=next_sortid)
        f.save()
        #new_flight.distance = new_flight.origin.distance_to(new_flight.destination)
        #new_flight.save()
        f.set_distance()
        #return redirect(index)
    except:
        return HttpResponse("Form validation error")

    dict = {'status': 1,
            'number': payload['number'],
            'city': destination_airport.city,
            'today': payload['today'],
            }
    return JsonResponse(dict)

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
    user_profile = UserProfile.objects.get(user=user)
    airport = Airport.objects.get(pk=airport_id)

    flights = Flight.objects.filter(owner=user).filter(Q(origin=airport) | Q(destination=airport))

    flights_dictionary = [
        {"number": flight.number,
         "origin": str(flight.origin),
         "destination": str(flight.destination),
         "direction": 'departure' if flight.origin.pk == airport_id else 'arrival',
         'city': flight.origin.city if flight.destination.pk == airport_id else flight.destination.city,
         "date": str(flight.date) if not user_profile.years_only else 'test',
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
        'comments': flight.comments,
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
            return JsonResponse({'status': 1, 'name': airport.name, 'iata': airport.iata, 'pk': airport.pk, 'city': airport.city})
        except:
            return JsonResponse({'status': 0});

def get_airports(request, username):
    user = User.objects.get(username=username)

    flights_list = Flight.objects.filter(owner=user)

    top_airports = Airport.objects.annotate(
        id__count=Count('origins', filter=Q(origins__in=flights_list), distinct=True)+Count('destinations', filter=Q(destinations__in=flights_list), distinct=True)
    ).filter(Q(id__count__gt=0)).order_by('-id__count')

    airports_list = [
        {'id': airport.id,
         'count': airport.id__count,
         'iata': airport.iata,
         'icao': airport.icao,
         'name': airport.name,
         'html_name': airport.html_name(),
         'city': airport.city,
         'percent': np.round(airport.id__count / (len(flights_list)*2.0) * 100, decimals=1),
        } for airport in top_airports
    ]

    return JsonResponse(airports_list, safe=False)

def get_filtered_flights_list(username, airline, aircraft, airport, year):
    user = User.objects.get(username=username)
    flights_list = Flight.objects.filter(owner=user)
    if airline != 'all':
        flights_list = flights_list.filter(airline=airline)
    if aircraft != 'all':
        flights_list = flights_list.filter(aircraft=aircraft)
    if airport != 'all':
        flights_list = flights_list.filter(Q(origin__iata=airport) | Q(destination__iata=airport))
    if year != 'all':
        flights_list = flights_list.filter(date__year=year)
    return flights_list

def get_filtered_registrations(request, username, airline, aircraft, airport, year):
    flights_list = get_filtered_flights_list(username, airline, aircraft, airport, year)

    top_registrations = flights_list.values('aircraft_registration', 'aircraft').annotate(Count('id')).order_by('-id__count')

    print(top_registrations)

    registrations_list = [
        {'registration': registration['aircraft_registration'],
         'aircraft': registration['aircraft'],
         'count': registration['id__count'],
         }
        for registration in top_registrations
    ]

    return JsonResponse(registrations_list, safe=False)

def get_filtered_countries(request, username, airline, aircraft, airport, year):
    flights_list = get_filtered_flights_list(username, airline, aircraft, airport, year)

    top_countries = Airport.objects.values('country', 'country_iso').annotate(
        id__count=Count('origins', filter=Q(origins__in=flights_list), distinct=True)+Count('destinations', filter=Q(destinations__in=flights_list), distinct=True)
    ).filter(Q(id__count__gt=0)).order_by('-id__count')

    countries_list = [
        {'country': country['country'],
         'country_iso': country['country_iso'],
         'count': country['id__count'],
        }
        for country in top_countries
    ]

    return JsonResponse(countries_list, safe=False) # Why is safe=False?

def get_filtered_airports(request, username, airline, aircraft, airport, year):
    user = User.objects.get(username=username)
    flights_list = Flight.objects.filter(owner=user)
    if airline != 'all':
        flights_list = flights_list.filter(airline=airline)
    if aircraft != 'all':
        flights_list = flights_list.filter(aircraft=aircraft)
    if airport != 'all':
        flights_list = flights_list.filter(Q(origin__iata=airport) | Q(destination__iata=airport))
    if year != 'all':
        flights_list = flights_list.filter(date__year=year)
    top_airports = Airport.objects.annotate(
        id__count=Count('origins', filter=Q(origins__in=flights_list), distinct=True)+Count('destinations', filter=Q(destinations__in=flights_list), distinct=True)
    ).filter(Q(id__count__gt=0)).order_by('-id__count')

    airports_list = [
        {'id': airport.id,
         'count': airport.id__count,
         'iata': airport.iata,
         'icao': airport.icao,
         'name': airport.name,
         'html_name': airport.html_name(),
         'city': airport.city,
         'percent': np.round(airport.id__count / (len(flights_list)*2.0) * 100, decimals=1),
        } for airport in top_airports
    ]

    return JsonResponse(airports_list, safe=False)


# def get_airlines(request, username):
#     user = User.objects.get(username=username)
#     flights_list = Flight.objects.filter(owner=user)
#     top_airlines = flights_list.values('airline').annotate(Count('id')).order_by('-id__count')
#
#     airlines_list = [
#         {'airline': airline['airline'],
#          'count': airline['id__count'],
#          'percent': np.round(airline['id__count'] / (len(flights_list)) * 100.0, decimals=1)}
#         for airline in top_airlines
#     ]
#
#     return JsonResponse(airlines_list, safe=False)

def get_filtered_airlines(request, username, airline, aircraft, airport, year):
    user = User.objects.get(username=username)
    flights_list = Flight.objects.filter(owner=user)
    if airline != 'all':
        flights_list = flights_list.filter(airline=airline)
    if aircraft != 'all':
        flights_list = flights_list.filter(aircraft=aircraft)
    if airport != 'all':
        flights_list = flights_list.filter(Q(origin__iata=airport) | Q(destination__iata=airport))
    if year != 'all':
        flights_list = flights_list.filter(date__year=year)
    top_airlines = flights_list.values('airline').annotate(Count('id')).order_by('-id__count')

    airlines_list = [
        {'airline': airline['airline'],
         'count': airline['id__count'],
         'percent': np.round(airline['id__count'] / (len(flights_list)) * 100.0, decimals=1)}
        for airline in top_airlines
    ]

    return JsonResponse(airlines_list, safe=False)

# def get_aircraft(request, username):
#     user = User.objects.get(username=username)
#     flights_list = Flight.objects.filter(owner=user)
#     top_planes = flights_list.values('aircraft').annotate(Count('id')).order_by('-id__count')
#
#     aircraft_list = [
#         {'aircraft': plane['aircraft'],
#          'count': plane['id__count'],
#          'percent': np.round(plane['id__count'] / len(flights_list) * 100.0, decimals=1)}
#         for plane in top_planes
#     ]
#
#     return JsonResponse(aircraft_list, safe=False)

def get_filtered_aircraft(request, username, airline, aircraft, airport, year):
    user = User.objects.get(username=username)
    flights_list = Flight.objects.filter(owner=user)
    if airline != 'all':
        flights_list = flights_list.filter(airline=airline)
    if aircraft != 'all':
        flights_list = flights_list.filter(aircraft=aircraft)
    if airport != 'all':
        flights_list = flights_list.filter(Q(origin__iata=airport) | Q(destination__iata=airport))
    if year != 'all':
        flights_list = flights_list.filter(date__year=year)
    top_planes = flights_list.values('aircraft').annotate(Count('id')).order_by('-id__count')

    aircraft_list = [
        {'aircraft': plane['aircraft'],
         'count': plane['id__count'],
         'percent': np.round(plane['id__count'] / len(flights_list) * 100.0, decimals=1)}
        for plane in top_planes
    ]

    return JsonResponse(aircraft_list, safe=False)

# def get_routes(request, username):
#     user = User.objects.get(username=username)
#     flights_list = Flight.objects.filter(owner=user)
#     top_routes = flights_list.values('origin__iata', 'origin__name', 'origin__city', 'origin__country', 'destination__iata', 'destination__name', 'destination__city', 'destination__country', 'origin__latitude', 'origin__longitude', 'destination__latitude', 'destination__longitude').annotate(Count('id')).order_by('-id__count')
#
#     routes_list = [
#         {'origin': route['origin__iata'],
#          'destination': route['destination__iata'],
#          'count': route['id__count'],
#          'percent': np.round(route['id__count'] / len(flights_list) * 100.0, decimals=1)}
#         for route in top_routes
#     ]
#
#     return JsonResponse(routes_list, safe=False)

def get_filtered_routes(request, username, airline, aircraft, airport, year):
    user = User.objects.get(username=username)
    flights_list = Flight.objects.filter(owner=user)
    if airline != 'all':
        flights_list = flights_list.filter(airline=airline)
    if aircraft != 'all':
        flights_list = flights_list.filter(aircraft=aircraft)
    if airport != 'all':
        flights_list = flights_list.filter(Q(origin__iata=airport) | Q(destination__iata=airport))
    if year != 'all':
        flights_list = flights_list.filter(date__year=year)
    top_routes = flights_list.values('origin__iata', 'origin__name', 'origin__city', 'origin__country', 'destination__iata', 'destination__name', 'destination__city', 'destination__country', 'origin__latitude', 'origin__longitude', 'destination__latitude', 'destination__longitude').annotate(Count('id')).order_by('-id__count')

    routes_list = [
        {'origin': route['origin__iata'],
         'destination': route['destination__iata'],
         'count': route['id__count'],
         'percent': np.round(route['id__count'] / len(flights_list) * 100.0, decimals=1)}
        for route in top_routes
    ]

    def get_inverse_count(origin, destination):
        for route in routes_list:
            if route['destination'] == origin and route['origin'] == destination:
                return route['count']
        return 0

    new_routes_list = [
        {'origin': route['origin'],
         'destination': route['destination'],
         'count': route['count'] + get_inverse_count(route['origin'], route['destination']),
         'percent': np.round(route['count'] / len(flights_list) * 100.0, decimals=1)}
         for route in routes_list
    ]

    for route in new_routes_list:
        for route2 in new_routes_list:
            if route2['origin'] == route['destination'] and route2['destination'] == route['origin']:
                new_routes_list.remove(route2)

    new_routes_list.sort(key=lambda x: -1*x['count'])

    return JsonResponse(new_routes_list, safe=False)

# def get_aggregates(request, username):
#     user = User.objects.get(username=username)
#     flights_list = Flight.objects.filter(owner=user)
#
#     try:
#         distance_mi = flights_list.aggregate(Sum('distance'))['distance__sum']
#         distance_km = distance_mi * 6371.0/3959.0
#     except:
#         # flights_list is empty
#         distance_mi = distance_km = 0
#
#     dictionary = {
#         'flights': len(flights_list),
#         'distance_mi': "{:,}".format(int(distance_mi)),
#         'distance_km': "{:,}".format(int(distance_km)),
#     }
#
#     return JsonResponse(dictionary, safe=False)

def get_filtered_aggregates(request, username, airline, aircraft, airport, year):
    user = User.objects.get(username=username)
    flights_list = Flight.objects.filter(owner=user)
    if airline != 'all':
        flights_list = flights_list.filter(airline=airline)
    if aircraft != 'all':
        flights_list = flights_list.filter(aircraft=aircraft)
    if airport != 'all':
        flights_list = flights_list.filter(Q(origin__iata=airport) | Q(destination__iata=airport))
    if year != 'all':
        flights_list = flights_list.filter(date__year=year)

    try:
        distance_mi = flights_list.aggregate(Sum('distance'))['distance__sum']
        distance_km = distance_mi * 6371.0/3959.0
    except:
        # flights_list is empty
        distance_mi = distance_km = 0

    dictionary = {
        'flights': len(flights_list),
        'distance_mi': "{:,}".format(int(distance_mi)),
        'distance_km': "{:,}".format(int(distance_km)),
    }

    return JsonResponse(dictionary, safe=False)

def get_filtered_superlatives(request, username, airline, aircraft, airport, year):
    user = User.objects.get(username=username)
    flights_list = Flight.objects.filter(owner=user)
    if airline != 'all':
        flights_list = flights_list.filter(airline=airline)
    if aircraft != 'all':
        flights_list = flights_list.filter(aircraft=aircraft)
    if airport != 'all':
        flights_list = flights_list.filter(Q(origin__iata=airport) | Q(destination__iata=airport))
    if year != 'all':
        flights_list = flights_list.filter(date__year=year)

    longest_flight = flights_list.order_by('-distance')[0]
    shortest_flight = flights_list.order_by('distance')[0]

    top_airports = Airport.objects.annotate(
        id__count=Count('origins', filter=Q(origins__in=flights_list), distinct=True)+Count('destinations', filter=Q(destinations__in=flights_list), distinct=True)
    ).filter(Q(id__count__gt=0)).order_by('-latitude')
    ## This works but it's slow as hell...

    northernmost_airport = top_airports[0]
    southernmost_airport = top_airports[len(top_airports) - 1]

    northernmost_latitude, southernmost_latitude = str(int(abs(northernmost_airport.latitude))) + '°', str(int(abs(southernmost_airport.latitude))) + '°'
    northernmost_latitude += 'N' if northernmost_airport.latitude > 0 else 'S'
    southernmost_latitude += 'N' if southernmost_airport.latitude > 0 else 'S'

    top_airports = top_airports.order_by('-elevation')
    highest_airport = top_airports[0]
    lowest_airport = top_airports[len(top_airports) - 1]

    dictionary = {
        'longest_origin': longest_flight.origin.html_name(),
        'longest_destination': longest_flight.destination.html_name(),
        'longest_distance_mi': "{:,}".format(int(longest_flight.distance)),
        'longest_distance_km': "{:,}".format(int(longest_flight.distance * 6371.0/3959.0)),
        'longest_duration': np.round((30.0 + longest_flight.distance/500.0 * 60.0) / 60.0),
        'shortest_origin': shortest_flight.origin.html_name(),
        'shortest_destination': shortest_flight.destination.html_name(),
        'shortest_distance_mi': "{:,}".format(int(shortest_flight.distance)),
        'shortest_distance_km': "{:,}".format(int(shortest_flight.distance * 6371.0/3959.0)),
        'shortest_duration': np.round((30.0 + shortest_flight.distance/500.0 * 60.0) / 60.0),
        'northernmost_airport': northernmost_airport.html_name(),
        'northernmost_city': northernmost_airport.city,
        'northernmost_latitude': northernmost_latitude,
        'southernmost_airport': southernmost_airport.html_name(),
        'southernmost_city': southernmost_airport.city,
        'southernmost_latitude': southernmost_latitude,
        'highest_airport': highest_airport.html_name(),
        'highest_city': highest_airport.city,
        'highest_elevation': highest_airport.elevation,
        'lowest_airport': lowest_airport.html_name(),
        'lowest_city': lowest_airport.city,
        'lowest_elevation': lowest_airport.elevation, # Replace hyphen with minus sign
    }

    return JsonResponse(dictionary, safe=False)




def mileage_graph(request, user1, user2, year1, year2):
    if user2 != 'null':
        usernames = [user1, user2]
    else:
        usernames = [user1,]
    dates, dists = {}, {}
    for user in usernames:
        flights = Flight.objects.filter(owner__username=user).order_by('date')
        dates[user] = []
        dists[user] = [0]
        for flight in flights:
            dates[user].append(matplotlib.dates.date2num(flight.date))
            dists[user].append(dists[user][-1] + flight.distance)



    #response = HttpResponse(content_type='image/png')

    plt.figure()

    for user in usernames:
        plt.plot_date(dates[user], dists[user][1:], marker=None, linestyle='-', xdate=True, label=user)

    plt.legend()
    plt.xlabel('Date')
    plt.ylabel('Distance (mi)')
    plt.xlim([datetime.date(year1, 1, 1), datetime.date(year2, 12, 31)])

    import io
    buf = io.BytesIO()


    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    response = HttpResponse(buf.getvalue(), content_type='image/png')
    return response

def airport_graph(request, user1, user2):
    if user2 != 'null':
        usernames = [user1, user2]
    else:
        usernames = [user1,]
    dates, airport_count, airports_visited = {}, {}, {}
    for user in usernames:
        flights = Flight.objects.filter(owner__username=user).order_by('date')
        dates[user] = []
        airport_count[user] = [0]
        airports_visited[user] = set()
        for flight in flights:
            dates[user].append(matplotlib.dates.date2num(flight.date))
            airports_visited[user].add(flight.origin.pk)
            airports_visited[user].add(flight.destination.pk)
            airport_count[user].append(len(airports_visited[user]))



    #response = HttpResponse(content_type='image/png')

    plt.figure()

    for user in usernames:
        plt.plot_date(dates[user], airport_count[user][1:], marker=None, linestyle='-', xdate=True, label=user)

    plt.legend()
    plt.xlabel('Date')
    plt.ylabel('Airports visited')
    import io
    buf = io.BytesIO()


    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    response = HttpResponse(buf.getvalue(), content_type='image/png')
    return response

def country_graph(request, user1, user2):
    if user2 != 'null':
        usernames = [user1, user2]
    else:
        usernames = [user1,]
    dates, country_count, countries_visited = {}, {}, {}
    for user in usernames:
        flights = Flight.objects.filter(owner__username=user).order_by('date')
        dates[user] = []
        country_count[user] = [0]
        countries_visited[user] = set()
        for flight in flights:
            dates[user].append(matplotlib.dates.date2num(flight.date))
            countries_visited[user].add(flight.origin.country)
            countries_visited[user].add(flight.destination.country)
            country_count[user].append(len(countries_visited[user]))



    #response = HttpResponse(content_type='image/png')

    plt.figure()

    for user in usernames:
        plt.plot_date(dates[user], country_count[user][1:], marker=None, linestyle='-', xdate=True, label=user)

    plt.legend()
    plt.xlabel('Date')
    plt.ylabel('Countries visited')
    import io
    buf = io.BytesIO()


    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    response = HttpResponse(buf.getvalue(), content_type='image/png')
    return response



# make abstract version of the top_x_graph method...

def aggregate_graph(request, type, username, other_usernames=None):
    # type = 'airport', 'airline', 'aircraft', 'country'
    usernames = [username]
    if other_usernames is not None:
        for other_username in other_usernames.split(','):
            usernames.append(other_username)
    dates, count, visited = {}, {}, {}

    if type == 'airport':
        for user in usernames:
            flights = Flight.objects.filter(owner__username=user).order_by('date')
            dates[user] = []
            count[user] = [0]
            visited[user] = set()
            for flight in flights:
                dates[user].append(matplotlib.dates.date2num(flight.date))
                visited[user].add(flight.origin.pk)
                visited[user].add(flight.destination.pk)
                count[user].append(len(visited[user]))

    if type == 'country':
        for user in usernames:
            flights = Flight.objects.filter(owner__username=user).order_by('date')
            dates[user] = []
            count[user] = [0]
            visited[user] = set()
            for flight in flights:
                dates[user].append(matplotlib.dates.date2num(flight.date))
                visited[user].add(flight.origin.country)
                visited[user].add(flight.destination.country)
                count[user].append(len(visited[user]))



    #response = HttpResponse(content_type='image/png')

    if other_usernames is not None:
        all_dates = []
        for user in usernames:
            all_dates.extend(dates[user])
        last_date = np.max(np.array(all_dates).flatten())
        for user in usernames:
            dates[user].append(last_date)
            count[user].append(count[user][-1])



    plt.figure()


    for user in usernames:
        plt.plot_date(dates[user], count[user][1:], marker=None, linestyle='-', xdate=True, label=user)

    if len(usernames) > 1:
        plt.legend()

    ylabels = {
        'airport': 'Airports visited',
        'airline': 'Airlines flown',
        'aircraft': 'Aircraft flown',
        'country': 'Countries visited',
    }
    plt.ylabel(ylabels[type])
    plt.xlabel('Date')

    import io
    buf = io.BytesIO()

    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    response = HttpResponse(buf.getvalue(), content_type='image/png')
    return response

def stackplot(request, type, username, draw_mode='zero', max=10):
    # type = 'airport', 'airline', 'aircraft', 'country'
    # draw_type = 'sym', 'wiggle', 'weighted_wiggle'
    flights = Flight.objects.filter(owner__username=username).order_by('date')
    dates = []
    counts = {}
    if type == 'airport':
        visited = Airport.objects.filter(Q(origins__in=flights) | Q(destinations__in=flights)).distinct()
    elif type == 'country':
        visited = Airport.objects.filter(Q(origins__in=flights)|Q(destinations__in=flights)).distinct().values('country')
    elif type == 'airline' or type == 'aircraft':
        visited = flights.values(type).annotate(Count('id')).order_by('-id__count')


    for visit in visited:
        if type == 'airport':
            counts[visit.pk] = [visit.iata, 0]
        if type == 'country':
            counts[visit['country']] = [visit['country'], 0]
        if type == 'aircraft' or type == 'airline':
            counts[visit[type]] = [visit[type], 0]

    switcher = {
        'airport': lambda flight, visit: counts[visit.pk].append(counts[visit.pk][-1] + 1 * int(visit == flight.origin or visit == flight.destination)),
        'country': lambda flight, visit: counts[visit['country']].append(counts[visit['country']][-1] + 1 * int(visit['country'] == flight.origin.country or visit['country'] == flight.destination.country)),
        'aircraft': lambda flight, visit: counts[visit[type]].append(counts[visit[type]][-1] + 1 * int(visit[type] == getattr(flight, type))),
        'airline': lambda flight, visit: counts[visit[type]].append(counts[visit[type]][-1] + 1 * int(visit[type] == getattr(flight, type))),
    }

    f = switcher.get(type)

    for flight in flights:
        dates.append(matplotlib.dates.date2num(flight.date))
        for visit in visited:
            f(flight, visit)

    lists = [l for l in counts.values()]
    lists.sort(key=lambda x: x[-1], reverse=True)
    lists = lists[:max]

    output = [np.array(l[2:]) for l in lists] # Why 2: and not 1: ????

    plt.figure()
    plt.stackplot(dates, output, labels=[l[0] for l in lists], baseline=draw_mode)
    plt.legend(loc='upper left')

    plt.ylabel('Flights')
    plt.xlabel('Date')

    import io
    buf = io.BytesIO()

    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    response = HttpResponse(buf.getvalue(), content_type='image/png')
    return response

    # fix this function so that it uses getattr

#
# def top_airports_graph(request, username):
#     flights = Flight.objects.filter(owner__username=username).order_by('date')
#     dates = []
#     airport_counts = {}
#     airports_visited = Airport.objects.filter(Q(origins__in=flights)|Q(destinations__in=flights)).distinct()
#     for airport in airports_visited:
#         airport_counts[airport.pk] = [airport.iata, 0]
#     for flight in flights:
#         dates.append(matplotlib.dates.date2num(flight.date))
#         for airport in airports_visited:
#             if flight.origin.pk == airport.pk or flight.destination.pk == airport.pk:
#                 airport_counts[airport.pk].append(airport_counts[airport.pk][-1] + 1)
#             else:
#                 airport_counts[airport.pk].append(airport_counts[airport.pk][-1])
#
#     lists = [airport_list for airport_list in airport_counts.values()]
#     lists.sort(key=lambda x: x[-1], reverse=True)
#     lists = lists[:10]
#
#     output = [np.array(lis[2:]) for lis in lists]
#
#     plt.figure()
#     plt.stackplot(dates, output, labels=[lis[0] for lis in lists], baseline='zero')
#     plt.legend(loc='upper left')
#
#     plt.ylabel('Cumulative visits')
#     plt.xlabel('Date')
#
#     import io
#     buf = io.BytesIO()
#
#     plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
#     response = HttpResponse(buf.getvalue(), content_type='image/png')
#     return response
#
# def top_airlines_graph(request, username):
#     flights = Flight.objects.filter(owner__username=username).order_by('date')
#     dates = []
#     airline_counts = {}
#     airlines_visited = flights.values('airline').annotate(Count('id')).order_by('-id__count')
#     print(airlines_visited)
#     for airline in airlines_visited:
#         airline_counts[airline['airline']] = [airline['airline'], 0]
#     for flight in flights:
#         dates.append(matplotlib.dates.date2num(flight.date))
#         for airline in airlines_visited:
#             if flight.airline == airline['airline'] or flight.airline == airline['airline']:
#                 airline_counts[airline['airline']].append(airline_counts[airline['airline']][-1] + 1)
#             else:
#                 airline_counts[airline['airline']].append(airline_counts[airline['airline']][-1])
#
#     lists = [airline_list for airline_list in airline_counts.values()]
#     lists.sort(key=lambda x: x[-1], reverse=True)
#     lists = lists[:10]
#
#     output = [np.array(lis[2:]) for lis in lists]
#
#     plt.figure()
#     plt.stackplot(dates, output, labels=[lis[0] for lis in lists], baseline='zero')
#     plt.legend(loc='upper left')
#
#     plt.ylabel('Cumulative visits')
#     plt.xlabel('Date')
#
#     import io
#     buf = io.BytesIO()
#
#     plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
#     response = HttpResponse(buf.getvalue(), content_type='image/png')
#     return response
#
# def top_aircraft_graph(request, username):
#     flights = Flight.objects.filter(owner__username=username).order_by('date')
#     dates = []
#     aircraft_counts = {}
#     aircraft_visited = flights.values('aircraft').annotate(Count('id')).order_by('-id__count')
#     print(aircraft_visited)
#     for aircraft in aircraft_visited:
#         aircraft_counts[aircraft['aircraft']] = [aircraft['aircraft'], 0]
#     for flight in flights:
#         dates.append(matplotlib.dates.date2num(flight.date))
#         for aircraft in aircraft_visited:
#             if flight.aircraft == aircraft['aircraft'] or flight.aircraft == aircraft['aircraft']:
#                 aircraft_counts[aircraft['aircraft']].append(aircraft_counts[aircraft['aircraft']][-1] + 1)
#             else:
#                 aircraft_counts[aircraft['aircraft']].append(aircraft_counts[aircraft['aircraft']][-1])
#
#     lists = [aircraft_list for aircraft_list in aircraft_counts.values()]
#     lists.sort(key=lambda x: x[-1], reverse=True)
#     lists = lists[:10]
#
#     output = [np.array(lis[2:]) for lis in lists]
#
#     plt.figure()
#     plt.stackplot(dates, output, labels=[lis[0] for lis in lists], baseline='zero')
#     plt.legend(loc='upper left')
#
#     plt.ylabel('Cumulative visits')
#     plt.xlabel('Date')
#
#     import io
#     buf = io.BytesIO()
#
#     plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
#     response = HttpResponse(buf.getvalue(), content_type='image/png')
#     return response
#
# def top_countries_graph(request, username):
#     flights_list = Flight.objects.filter(owner__username=username).order_by('date')
#     dates = []
#     country_counts = {}
#     countries_visited = Airport.objects.filter(Q(origins__in=flights_list)|Q(destinations__in=flights_list)).distinct().values('country')
#     for country in countries_visited:
#         print(country)
#         country_counts[country['country']] = [country['country'], 0]
#     for flight in flights_list:
#         dates.append(matplotlib.dates.date2num(flight.date))
#         for country in countries_visited:
#             if flight.origin.country == country['country'] or flight.destination.country == country['country']:
#                 country_counts[country['country']].append(country_counts[country['country']][-1] + 1)
#             else:
#                 country_counts[country['country']].append(country_counts[country['country']][-1])
#
#     lists = [country_list for country_list in country_counts.values()]
#     lists.sort(key=lambda x: x[-1], reverse=True)
#     lists = lists[:10]
#
#     output = [np.array(lis[2:]) for lis in lists]
#
#     plt.figure()
#     plt.stackplot(dates, output, labels=[lis[0] for lis in lists], baseline='zero')
#     plt.legend(loc='upper left')
#     plt.ylabel('Flights')
#     plt.xlabel('Days since 0001-01-01')
#
#     import io
#     buf = io.BytesIO()
#
#
#     plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
#     response = HttpResponse(buf.getvalue(), content_type='image/png')
#     return response
