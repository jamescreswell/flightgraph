from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden, UnreadablePostError
from django.core import serializers
from django.core.exceptions import PermissionDenied
from .models import Airport, Flight, UserProfile
from .forms import FlightForm
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
import numpy as np
import time
from django.db.models import Q, Count, Sum
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
import json
import datetime


# import matplotlib
# matplotlib.use('Agg') # Server has no GUI
# import matplotlib.pyplot as plt
# #from mpl_toolkits.basemap import Basemap
import datetime # I hope this doesn't mess up the Django datetime ...

def temp(request):
    return render(request, 'flights/temp.html', {})


def index(request, error=None):
    username = request.user.username

    if username != '':
        # return home(request)
        latest_flights = Flight.objects.filter(owner__username=username).order_by('-sortid')[:4]
    else:
        latest_flights = None

    context = {'nav_id': 'index_nav',
               'name': 'index',
               'username': request.user.username,
               'duplicate_username': True if error == 'duplicate_username' else False,
               'latest_flights': latest_flights,
              }
    return render(request, 'flights/index.html', context)

def home(request, username=None):
    if username is not None:
        profile = 1
        user = User.objects.get(username=username)
    else:
        profile = 0
        user = request.user
        if not user.is_authenticated:
            return login_view(request)


    flights = Flight.objects.filter(owner=user).order_by('-sortid')

    latest_flights = Flight.objects.filter(owner=user).order_by('-sortid')[:5][::-1]

    flights_this_year = Flight.objects.filter(owner=user, date__range=[datetime.date.today() - datetime.timedelta(days=365), datetime.date.today()])

    countries = Airport.objects.values('country', 'country_iso').annotate(
        id__count=Count('origins', filter=Q(origins__in=flights), distinct=True)+Count('destinations', filter=Q(destinations__in=flights), distinct=True)
    ).filter(Q(id__count__gt=0)).order_by('-id__count')

    countries_this_year = Airport.objects.values('country', 'country_iso').annotate(
        id__count=Count('origins', filter=Q(origins__in=flights_this_year), distinct=True)+Count('destinations', filter=Q(destinations__in=flights_this_year), distinct=True)
    ).filter(Q(id__count__gt=0)).order_by('-id__count')

    top_country = countries[0]
    # top_country_this_year = countries_this_year[0]

    try:
        distance_mi = flights.aggregate(Sum('distance'))['distance__sum']
        distance_km = distance_mi * 6371.0/3959.0

        distance_mi_this_year = flights_this_year.aggregate(Sum('distance'))['distance__sum']
        distance_km_this_year = distance_mi_this_year * 6371.0/3959.0
    except:
        # flights_list is empty
        distance_mi = distance_km = 0
        distance_mi_this_year = distance_km_this_year = 0


    # Airports
    top_airports = Airport.objects.annotate(
        id__count=Count('origins', filter=Q(origins__in=flights), distinct=True)+Count('destinations', filter=Q(destinations__in=flights), distinct=True)
    ).filter(Q(id__count__gt=0)).order_by('-id__count')

    airports_list = [
        {'id': airport.id,
         'count': airport.id__count,
         'iata': airport.iata,
         'icao': airport.icao,
         'name': airport.name,
         'html_name': airport.html_name(),
         'city': airport.city,
         'percent': np.round(airport.id__count / (len(flights)*2.0) * 100, decimals=1),
        } for airport in top_airports
    ]

    new_airports = Airport.objects.annotate(
        id__count=Count('origins', filter=Q(origins__in=flights_this_year), distinct=True)+Count('destinations', filter=Q(destinations__in=flights_this_year), distinct=True)
    ).filter(Q(id__count__gt=0)).order_by('-id__count')

    # Routes
    top_routes = flights.values('origin__iata', 'origin__name', 'origin__city', 'origin__country', 'destination__iata', 'destination__name', 'destination__city', 'destination__country', 'origin__latitude', 'origin__longitude', 'destination__latitude', 'destination__longitude').annotate(Count('id')).order_by('-id__count')

    routes_list = [
        {'origin': route['origin__iata'],
         'destination': route['destination__iata'],
         'count': route['id__count'],
         'percent': np.round(route['id__count'] / len(flights) * 100.0, decimals=1)}
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
         'percent': np.round(route['count'] / len(flights) * 100.0, decimals=1)}
         for route in routes_list
    ]

    for route in new_routes_list:
        for route2 in new_routes_list:
            if route2['origin'] == route['destination'] and route2['destination'] == route['origin']:
                new_routes_list.remove(route2)

    new_routes_list.sort(key=lambda x: -1*x['count'])

    # Airlines

    top_airlines = flights.values('airline').annotate(Count('id')).order_by('-id__count')

    airlines_list = [
        {'airline': airline['airline'],
         'count': airline['id__count'],
         'percent': np.round(airline['id__count'] / (len(flights)) * 100.0, decimals=1)}
        for airline in top_airlines
    ]

    # aircraft
    top_planes = flights.values('aircraft').annotate(Count('id')).order_by('-id__count')

    aircraft_list = [
        {'aircraft': plane['aircraft'],
         'count': plane['id__count'],
         'percent': np.round(plane['id__count'] / len(flights) * 100.0, decimals=1)}
        for plane in top_planes
    ]


    home_airport = UserProfile.objects.get(user=user).home_airport

    context = {
        'latest_flights': latest_flights,
        'this_year': [datetime.date.today() - datetime.timedelta(days=365), datetime.date.today()],
        'flights_this_year': len(flights_this_year),
        'total_flights': len(flights),
        'first_flight_date': flights[len(flights)-1].date if len(flights) > 0 else datetime.date.today(),
        'distance_mi': int(distance_mi),
        'distance_km': int(distance_km),
        'distance_mi_this_year': int(distance_mi_this_year),
        'distance_km_this_year': int(distance_km_this_year),
        'airports_this_year': len(new_airports),
        'countries_this_year': len(countries_this_year),
        # 'countries_this_year': len(countries_this_year),
        'total_countries': len(countries),
        'owner': True if username == None else False,
        'top_routes': new_routes_list[:5],
        'top_airports': airports_list[:5],
        'top_airlines': airlines_list[:5],
        'top_planes': aircraft_list[:5],
        'total_routes': len(new_routes_list),
        'total_airports': len(airports_list),
        'total_aircraft': len(aircraft_list),
        'total_airlines': len(airlines_list),
        # 'top_country_this_year': top_country_this_year,
        'top_country': top_country,
        'username': user.username,
        'profile_username': user.username,
        'own': user == request.user,
        'profile': profile,
        'home_airport': home_airport,
    }
    return render(request, 'flights/home.html', context)



# THIS SHOULD BE AN API FUNCTION!!!!!! def add_flight(request):

def api_index(request):
    username = request.user.username

    context = {'nav_id': 'api_nav',
               'name': 'api',
               'username': request.user.username,
              }
    return render(request, 'flights/api.html', context)

##############
# /accounts/ #
##############

def create_account(request):
    if request.method == 'POST':
        # Get POST data
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email') # If he doesn't have an email, this is just an empty string

        # Make sure username is unique
        # Email doesn't have to be unique
        if User.objects.filter(username=username).exists():
            return index(request, error="duplicate_username")

        User.objects.create_user(username=username, email=email, password=password)
        user = authenticate(username=username, password=password)
        login(request, user)

        # Create default UserProfile
        profile = UserProfile(user=user)
        profile.save()

        # Send him to the map with newuser flag (hints)
        return redirect('map')
    else:
        raise PermissionDenied

@login_required
def settings(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)

    context = {'username': user.username,
               'email': user.email,
               'password': user.password,
               'profile_enabled': user_profile.public,
               'years_only': user_profile.years_only,
              }

    return render(request, 'flights/settings.html', context)


@login_required
def update_settings(request):
    payload = json.loads(request.body)
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    print(bool(int(payload['years_only'])))
    user_profile.public = bool(int(payload['public']))
    user_profile.years_only = bool(int(payload['years_only']))
    user_profile.save()

    dictionary = {
        'public': user_profile.public,
    }

    return JsonResponse(dictionary, safe=False)

# This view answers both GET and POST requests
# nextstring is the url string of the page to rederict after a successful login
def login_view(request, nextstring='index'):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(nextstring)
        else:
            return render(request, 'flights/login.html', {'invalid_credentials': True})
    elif request.method == 'GET':
        return render(request, 'flights/login.html', {})

def logout_view(request):
    logout(request)
    return redirect('index')

def reset_account(request):
    if request.method == 'POST':
        # Implement...
        return HttpResponse('The server has received your account reset request. If the server can identify your account, you will receive an email with your new password.')
    elif request.method == 'GET':
        return render(request, 'flights/reset_account.html', {})

















def airports(request):
    pass


def webgl(request):
    user = request.user
    airports_list = Airport.objects.filter(Q(origins__owner=user) | Q(destinations__owner=user)).distinct()
    routes_list = Flight.objects.filter(owner=user).values('origin__pk', 'origin__latitude', 'origin__longitude', 'destination__pk', 'destination__latitude', 'destination__longitude').annotate(Count('id'))
    print(routes_list)
    return render(request, 'flights/webgl.html', {'airports': airports_list, 'routes': routes_list})







def map(request, username=None, profile=False):
    if username is not None:
        user = User.objects.get(username=username)
    else:
        user = request.user

    #flights_list = Flight.objects.filter(owner=user)
    airports_list = Airport.objects.filter(Q(origins__owner=user) | Q(destinations__owner=user)).distinct()
    print(airports_list)

    routes_list = Flight.objects.filter(owner=user).values('origin__pk', 'origin__latitude', 'origin__longitude', 'destination__pk', 'destination__latitude', 'destination__longitude').annotate(Count('id'))

    context = {'airports': airports_list,
               'routes': routes_list,
               'username': user.username,
               'profile': 0 if not profile else 1,
               'profile_username': username,
              }

    return render(request, 'flights/map.html', context)

def list(request, username=None, profile=False, id=None):
    if username is not None:
        user = User.objects.get(username=username)
    else:
        user = request.user


    context = {'username': user.username,
               'profile': 0 if not profile else 1,
               'profile_username': username,
               'start_id': id,
              }

    return render(request, 'flights/list.html', context)

def statistics(request, username=None, profile=False):
    if username is not None:
        user = User.objects.get(username=username)
    else:
        user = request.user

    context = {'username': user.username,
               'profile': 0 if not profile else 1,
               'profile_username': username,
              }

    return render(request, 'flights/statistics.html', context)

def profile_map(request, username):
    if UserProfile.objects.get(user=User.objects.get(username=username)).public:
        return map(request, username, True)
    else:
        raise PermissionDenied

def profile_list(request, username):
    return list(request, username, True)

def profile_statistics(request, username):
    return statistics(request, username, True)

def testlist(request):
    return list(request, 'admin', False)

def teststats(request):
    return statistics(request, 'admin', False)



def gcmap(request):
    context = {'method': 'GET',
               'nav_id': 'gcmap_nav',
               'username': request.user.username,
              }

    return render(request, 'flights/gcmap.html', context)

def export(request):
    if request.method != 'POST':
        raise PermissionDenied

    data = request.POST

    if data['filetype'] == 'pdf':
        response = HttpResponse(content_type='application/pdf')
    elif data['filetype'] == 'png':
        response = HttpResponse(content_type='image/png')
    else:
        raise UnreadablePostError

    # Checkboxes don't POST????
    #if data['borders']:
    #    m.drawcoastlines()
    #    m.drawcountries()

    ### Start interpret search string...should be abstracted ###
    try:
        input_routes = data['search_string'].split(",")
        routes = []
        for input_route in input_routes:
            hyphen_indices = [i for i, ltr in enumerate(input_route) if ltr == '-']
            codes = [input_route[0:hyphen_indices[0]],]
            i = -1
            for i in range(len(hyphen_indices)-1):
                codes.append(input_route[hyphen_indices[i]+1:hyphen_indices[i+1]])
            codes.append(input_route[hyphen_indices[i+1]+1:])
            for i in range(len(codes)-1):
                routes.append([codes[i], codes[i+1]])
    except:
        raise ValueError('Invalid AJAX data')

    # Look up codes
    route_pairs = []
    for route in routes:
        route_airports = []
        for code in route:
            if len(code) == 3:
                match = Airport.objects.filter(iata=code.upper())
                if len(match) == 1:
                    route_airports.append(match[0])
                elif len(match) == 0:
                    pass
                else:
                    # Problems...
                    route_airports.append(match[0])
            elif len(code) == 4:
                match = Airport.objects.filter(icao=code.upper())
                if len(match) == 1:
                    route_airports.append(match[0])
                elif len(match) == 0:
                    pass
                else:
                    # Problems...
                    route_airports.append(match[0])
            else:
                # This should never happen
                raise ValueError('Invalid AJAX data')
        route_airports.append(route_airports[0].distance_to(route_airports[1]))
        route_pairs.append(route_airports)

    airports = [route_pairs[0][0], route_pairs[0][1]]
    for i in range(1, len(route_pairs)):
        if route_pairs[i-1][1] != route_pairs[i][0]:
            airports.append(route_pairs[i][0])
        airports.append(route_pairs[i][1])
    ### End interpret search string...should be abstracted ###

    lat_0 = float(sum([airport.latitude for airport in airports])) / max(len(airports), 1)
    lon_0 = float(sum([airport.longitude for airport in airports])) / max(len(airports), 1)

    llcrnrlon = min([airport.longitude for airport in airports]) - 10.0
    llcrnrlat = min([airport.latitude for airport in airports]) - 10.0
    urcrnrlon = max([airport.longitude for airport in airports]) + 10.0
    urcrnrlat = max([airport.latitude for airport in airports]) + 10.0

    plt.figure()
    if data['projection'] in ['ortho', 'robin', 'moll']:
        m = Basemap(width=10000000,
                    height=10000000,
                    projection=data['projection'],
                    lat_0=lat_0,
                    lon_0=lon_0,
                    resolution='l',
                    area_thresh=1000.0
                   )
    elif data['projection'] in ['mill', 'stere']:
        return HttpResponse('Selected projection doesn\'t work yet')
        m = Basemap(width=10000000,
                    height=10000000,
                    projection=data['projection'],
                    llcrnrlon=llcrnrlon,
                    llcrnrlat=llcrnrlat,
                    urcrnrlon=urcrnrlon-360.0,
                    urcrnrlat=urcrnrlat,
                    resolution='l',
                    area_thresh=1000.0
                   )

    m.shadedrelief(scale=0.45)

    for airport in airports:
        m.scatter(airport.longitude, airport.latitude, s=3, latlon=True, color='red', zorder=100)

    for route in route_pairs:
        m.drawgreatcircle(route[0].longitude, route[0].latitude, route[1].longitude, route[1].latitude, del_s=100.0, color='red')

    plt.savefig(response, format=data['filetype'], dpi=300)
    return response

def flights(request, username=None):
    start = time.time()

    if request.method == 'POST':
        try:
            f = FlightForm(request.POST)
            f.instance.distance = -1
            try:
                f.instance.sortid = Flight.objects.filter(owner=request.user).order_by('-sortid')[0].sortid + 1
            except:
                f.instance.sortid = 0
            f.instance.owner = request.user
            new_flight = f.save()
            new_flight.distance = new_flight.origin.distance_to(new_flight.destination)
            new_flight.save()
            new_flight.set_distance()
        except:
            return HttpRequest("Form validation error")

    if username == None:
        if request.user.is_authenticated:
            user = request.user
            nav_id = 'flights_nav'
        else:
            return redirect('login')
    else:
        user = User.objects.get(username=username)
        nav_id = None

    flights_list = Flight.objects.filter(owner=user)

    airports_list = Airport.objects.filter(Q(origins__owner=user) | Q(destinations__owner=user)).distinct()

    top_airports = airports_list.annotate(
        id__count=Count('origins', filter=Q(origins__owner=user), distinct=True)+Count('destinations', filter=Q(destinations__owner=user), distinct=True)
    ).order_by('iata')

    planes = flights_list.values('aircraft').distinct().order_by('aircraft')
    airlines = flights_list.values('airline').distinct().order_by('airline')

    routes_list = flights_list.values('origin__latitude', 'origin__longitude', 'destination__latitude', 'destination__longitude').annotate(Count('id'))
    try:
        distance_mi = flights_list.aggregate(Sum('distance'))['distance__sum']
        distance_km = distance_mi * 6371.0/3959.0
    except:
        # flights_list is empty
        distance_mi = distance_km = 0

    context = {'nav_id': nav_id,
               'username': request.user.username,
               'query_username': username,
               'display_username': user.username,
               'flights': flights_list,
               'airports': top_airports,
               'routes': routes_list,
               'planes': planes,
               'airlines': airlines,
               'loading_time': time.time() - start,
               'method': request.method,
               'distance_mi': distance_mi,
               'distance_km': distance_km,
              }

    return render(request, 'flights/flights.html', context)

def flights_map(request):
    pass

def compare(request, username1, username2):
    user1 = User.objects.get(username=username1)
    user2 = User.objects.get(username=username2)

    flights_list1 = Flight.objects.filter(owner=user1)
    flights_list2 = Flight.objects.filter(owner=user2)

    top_airports1 = Airport.objects.annotate(
        id__count=Count('origins', filter=Q(origins__in=flights_list1), distinct=True)+Count('destinations', filter=Q(destinations__in=flights_list1), distinct=True)
    ).filter(Q(id__count__gt=0)).order_by('-id__count')
    top_planes1 = flights_list1.values('aircraft').annotate(Count('id')).order_by('-id__count')
    top_airlines1 = flights_list1.values('airline').annotate(Count('id')).order_by('-id__count')
    top_routes1 = flights_list1.values('origin__iata', 'origin__name', 'origin__city', 'origin__country', 'destination__iata', 'destination__name', 'destination__city', 'destination__country', 'origin__latitude', 'origin__longitude', 'destination__latitude', 'destination__longitude').annotate(Count('id')).order_by('-id__count')



    top_countries1 = Airport.objects.values('country', 'country_iso').annotate(
        id__count=Count('origins', filter=Q(origins__in=flights_list1), distinct=True)+Count('destinations', filter=Q(destinations__in=flights_list1), distinct=True)
    ).filter(Q(id__count__gt=0))

    top_countries2 = Airport.objects.values('country', 'country_iso').annotate(
        id__count=Count('origins', filter=Q(origins__in=flights_list2), distinct=True)+Count('destinations', filter=Q(destinations__in=flights_list2), distinct=True)
    ).filter(Q(id__count__gt=0))





    top_airports2 = Airport.objects.annotate(
        id__count=Count('origins', filter=Q(origins__in=flights_list2), distinct=True)+Count('destinations', filter=Q(destinations__in=flights_list2), distinct=True)
    ).filter(Q(id__count__gt=0)).order_by('-id__count')
    top_planes2 = flights_list2.values('aircraft').annotate(Count('id')).order_by('-id__count')
    top_airlines2 = flights_list2.values('airline').annotate(Count('id')).order_by('-id__count')
    top_routes2 = flights_list2.values('origin__iata', 'origin__name', 'origin__city', 'origin__country', 'destination__iata', 'destination__name', 'destination__city', 'destination__country', 'origin__latitude', 'origin__longitude', 'destination__latitude', 'destination__longitude').annotate(Count('id')).order_by('-id__count')

    try:
        distance_mi1 = flights_list1.aggregate(Sum('distance'))['distance__sum']
        distance_km1 = distance_mi1 * 6371.0/3959.0
    except:
        # flights_list is empty
        distance_mi1 = distance_km1 = 0

    try:
        distance_mi2 = flights_list2.aggregate(Sum('distance'))['distance__sum']
        distance_km2 = distance_mi2 * 6371.0/3959.0
    except:
        # flights_list is empty
        distance_mi2 = distance_km2 = 0

    #airports_both = Airport.objects.filter(Q(origins__in=flights_list1)|Q(destinations__in=flights_list1)).filter(Q(origins__in=flights_list2)|Q(destinations__in=flights_list2)).distinct().annotate(
    #    id__count=Count('origins', filter=Q(origins__in=flights_list1), distinct=True)+Count('destinations', filter=Q(destinations__in=flights_list1), distinct=True)
    #)

    #airports1 = Airport.objects.filter(Q(origins__in=flights_list1)|Q(destinations__in=flights_list1)).values('iata', distinct=True)
    #print(airports1)
    airports_both1 = Airport.objects.filter(Q(origins__in=flights_list1)|Q(destinations__in=flights_list1)).distinct()
    airports_both2 = Airport.objects.filter(Q(origins__in=flights_list2)|Q(destinations__in=flights_list2)).distinct()
    airports_both = airports_both1.filter(pk__in=airports_both2)
    print(airports_both.query)
    #print(airports_both.get(iata='PVG'))
    #print(airports_test)
    #print(list(airports_both))
    for airport in airports_both:
        airport.count1 = top_airports1.get(pk=airport.pk).id__count
        airport.count2 = top_airports2.get(pk=airport.pk).id__count


    airports_only1 = top_airports1.exclude(pk__in=airports_both)
    airports_only2 = top_airports2.exclude(pk__in=airports_both)

    airports_both = sorted(airports_both, key=lambda x: x.count1, reverse=True)



    #countries_both = Airport.objects.filter((Q(origins__in=flights_list1)|Q(destinations__in=flights_list1)) & (Q(origins__in=flights_list2)|Q(destinations__in=flights_list2))).values('country', 'country_iso').annotate(
    #    id__count=Count('origins', filter=Q(origins__in=flights_list1), distinct=True)+Count('destinations', filter=Q(destinations__in=flights_list1), distinct=True)
    #)

    countries_both1 = Airport.objects.filter(Q(origins__in=flights_list1)|Q(destinations__in=flights_list1)).distinct().values('country')#, 'country_iso')
    countries_both2 = Airport.objects.filter(Q(origins__in=flights_list2)|Q(destinations__in=flights_list2)).distinct().values('country')#, 'country_iso')
    countries_both = countries_both1.filter(country__in=countries_both2)
    for country in countries_both:
        country['count1'] = top_countries1.get(country=country['country'])['id__count']
        country['count2'] = top_countries2.get(country=country['country'])['id__count']
        country['country_iso'] = top_countries1.get(country=country['country'])['country_iso']

    countries_only1 = top_countries1.exclude(country__in=countries_both.values('country')).order_by('-id__count')
    countries_only2 = top_countries2.exclude(country__in=countries_both.values('country')).order_by('-id__count')

    countries_both = sorted(countries_both, key=lambda x: x['count1'], reverse=True)


    planes_both = flights_list1.filter(aircraft__in=flights_list2.values('aircraft')).values('aircraft').annotate(
        count1=Count('id')
    ).order_by('-count1')
    for plane in planes_both:
        plane['count2'] = top_planes2.get(aircraft=plane['aircraft'])['id__count']

    planes_only1 = flights_list1.exclude(aircraft__in=flights_list2.values('aircraft')).values('aircraft').annotate(
        count1=Count('id')
    ).order_by('-count1')

    planes_only2 = flights_list2.exclude(aircraft__in=flights_list1.values('aircraft')).values('aircraft').annotate(
        count2=Count('id')
    ).order_by('-count2')



    airlines_both = flights_list1.filter(airline__in=flights_list2.values('airline')).values('airline').annotate(
        count1=Count('id')
    ).order_by('-count1')
    for airline in airlines_both:
        airline['count2'] = top_airlines2.get(airline=airline['airline'])['id__count']

    airlines_only1 = flights_list1.exclude(airline__in=flights_list2.values('airline')).values('airline').annotate(
        count1=Count('id')
    ).order_by('-count1')

    airlines_only2 = flights_list2.exclude(airline__in=flights_list1.values('airline')).values('airline').annotate(
        count2=Count('id')
    ).order_by('-count2')



    #flights_list1.values('aircraft').intersection(flights_list2.values('aircraft'))#flights_list1.values('aircraft').intersection(flights_list2.values('aircraft'))


    context = {'username1': user1.username,
               'username2': user2.username,
               'n_flights1': len(flights_list1),
               'n_flights2': len(flights_list2),
               'distance_mi1': distance_mi1,
               'distance_km1': distance_km1,
               'distance_mi2': distance_mi2,
               'distance_km2': distance_km2,
               'top_airports1': top_airports1,
               'top_airports2': top_airports2,
               'airports_both': airports_both,
               'airports_only1': airports_only1,
               'airports_only2': airports_only2,
               'planes_both': planes_both,
               'planes_only1': planes_only1,
               'planes_only2': planes_only2,
               'airlines_both': airlines_both,
               'airlines_only1': airlines_only1,
               'airlines_only2': airlines_only2,
               'countries_both': countries_both,
               'countries_only1': countries_only1,
               'countries_only2': countries_only2,
               'top_countries1': top_countries1,
               'top_countries2': top_countries2,
               'top_routes1': top_routes1,
               'top_routes2': top_routes2,
              }

    return render(request, 'flights/compare.html', context)


def route_map(request, id1, id2):
    airport1 = Airport.objects.get(pk=id1)
    airport2 = Airport.objects.get(pk=id2)
    print(airport1.longitude)
    print(airport1.latitude)
    plt.figure()
    plt.scatter(airport1.longitude, airport1.latitude, color='black')
    plt.scatter(airport2.longitude, airport2.latitude, color='black')

    import io
    buf = io.BytesIO()


    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    response = HttpResponse(buf.getvalue(), content_type='image/png')
    return response
