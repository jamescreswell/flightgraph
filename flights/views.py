from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden, UnreadablePostError
from django.core import serializers
from django.core.exceptions import PermissionDenied
from .models import Airport, Flight
from .forms import FlightForm
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
import numpy as np
import time
from django.db.models import Q, Count, Sum
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


#import matplotlib
#matplotlib.use('Agg') # Server has no GUI
#import matplotlib.pyplot as plt
#from mpl_toolkits.basemap import Basemap

def index(request):
    context = {'nav_id': 'index_nav',
               'name': 'index',
               'username': request.user.username,
              }
    return render(request, 'flights/index.html', context)

def airports(request):
    pass


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

def create_account(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('flights')
    else:
        form = UserCreationForm()
    return render(request, 'registration/create_account.html', {'form': form})
