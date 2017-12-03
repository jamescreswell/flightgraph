from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.core import serializers
from django.core.exceptions import PermissionDenied
from .models import Airport
from django.template.loader import render_to_string
import numpy as np

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
               'airports': airports}
    html = render_to_string('flights/ajax/left-bar.html', context)
    
    return HttpResponse(html)

def airports(request):
    pass

def image(request):
    # This is going to be GET, right?
    response = HttpResponse(content_type='application/pdf')
    
    map = Basemap(projection='ortho', lat_0=50, lon_0=-100, resolution='l', area_thresh=1000.0)
 
    map.drawcoastlines()
    map.drawcountries()

    plt.savefig(response, format='pdf')
    return response