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

@login_required
def draw_list(request):
    if not request.is_ajax():
        raise PermissionDenied
    user = request.user
    flights_list = Flight.objects.filter(owner=user)
    
    context = {'flights': flights_list,
              }
    
    html = render_to_string('flights/ajax/list.html', context, request=request)
    
    return HttpResponse(html)

@login_required
def draw_stats(request):
    if not request.is_ajax():
        raise PermissionDenied
    user = request.user
    flights_list = Flight.objects.filter(owner=user)
    airports_list = Airport.objects.filter(Q(origins__owner=user) | Q(destinations__owner=user)).distinct()
    
    top_airports = airports_list.annotate(Count('origins', distinct=True), Count('destinations', distinct=True))
    # when to add origins and destinations??
    top_planes = flights_list.values('aircraft').annotate(Count('id')).order_by('-id__count')
    top_airlines = flights_list.values('airline').annotate(Count('id')).order_by('-id__count')
    
    
    
    context = {'top_airports': top_airports,
               'top_planes': top_planes,
               'top_airlines': top_airlines,
              }
    
    html = render_to_string('flights/ajax/statistics.html', context, request=request)
    
    return HttpResponse(html)
