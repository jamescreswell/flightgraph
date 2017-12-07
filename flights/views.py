from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden, UnreadablePostError
from django.core import serializers
from django.core.exceptions import PermissionDenied
from .models import Airport, Flight
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
import numpy as np
import time
from django.db.models import Q, Count

import matplotlib
matplotlib.use('Agg') # Server has no GUI
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

def index(request):
    context = {'nav_id': 'index_nav',
               'name': 'index',
              }
    return render(request, 'flights/index.html', context)

def gcmap(request):
    context = {'method': 'GET',
               'nav_id': 'gcmap_nav',
              }

    return render(request, 'flights/gcmap.html', context)
        
def draw_gcmap(request):
    if not request.is_ajax():
        raise PermissionDenied
        #return HttpResponseForbidden('Permission denied: <tt>request.is_ajax() == False</tt>')
    
    input_string = request.GET.get('input_string')
    # input_string is of the format "abc-defg-hij-kil-...-xyz"

    # Extract codes
    try:
        input_routes = input_string.split(",")
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
        
    context = {'routes': route_pairs,
               'airports': airports,
               'input_string': input_string
              }
    html = render_to_string('flights/ajax/left-bar.html', context, request=request)
    
    return HttpResponse(html)

def airports(request):
    pass

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

@login_required
def flights(request):
    start = time.time()
    # Get logged in user and his flights
    user = request.user
    flights_list = Flight.objects.filter(owner=user)
    airports_list = Airport.objects.filter(Q(origins__owner=user) | Q(destinations__owner=user)).distinct()
    #airports_list = set()
    #for flight in flights_list:
    #    airports_list.add(flight.origin)
    #    airports_list.add(flight.destination)
    
    top_airports = airports_list.annotate(Count('origins', distinct=True), Count('destinations', distinct=True))
    print(top_airports[0].destinations__count) # when to add origins and destinations??
    top_planes = flights_list.values('aircraft').annotate(Count('id')).order_by('-id__count')
    top_airlines = flights_list.values('airline').annotate(Count('id')).order_by('-id__count')
    
    
    
    context = {'nav_id': 'flights_nav',
               'username': user.username,
               'flights': flights_list,
               'top_airports': top_airports,
               'top_planes': top_planes,
               'top_airlines': top_airlines,
               'loading_time': time.time() - start,
              }
    
    return render(request, 'flights/flights.html', context)

        