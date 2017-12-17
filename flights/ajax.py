from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden, UnreadablePostError
from django.core import serializers
from django.core.exceptions import PermissionDenied, FieldError
from .models import Airport, Flight
from .forms import FlightForm
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
import numpy as np
import time
from django.db.models import Q, Count, Sum, Case, When, IntegerField
        
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
    flights_list = Flight.objects.filter(owner=user).order_by('-sortid')
    
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
    
    
    ##top_airports = Airport.objects.all().annotate(origins__count=Sum(
    #    Case(When(origins__owner=user, then=1),
    #          default=0,
    #          output_field=IntegerField()
    #    )),

     #                                             destinations__count=Sum(
    #    Case(When(destinations__owner=user, then=1),
    #        default=0,
    #   output_field=IntegerField()))
    #                                             )
    #top_airports = Airport.objects.annotate(
    #    origins__count = Count('origins', filter=Q(pk=2)),
        
    #)
                                                
    #print(top_airports.query)
    
    # Q: How many times has user been on airport XXX?
    
    #top_airports = (Airport.objects.filter(origins__owner=user) | Airport.objects.filter(destinations__owner=user)).annotate(origins__count=Count('origins'), destinations__count=Count('destinations'))
    #print(result)
    
    top_airports = Airport.objects.filter(origins__owner=user).annotate(num_origins=Count('origins')+Count('destinations'))
    print(Airport.objects.filter(iata='CPH')[0].origins.filter(owner=user))


    #top_origins = Airport.objects.annotate(id__count=Count('origins', filter=Q(origins__owner=user)))
    
    #top_airports = result.annotate(id__count=Count('origins'))
    
    #top_airports = list(top_origins) + list(top_destinations)
    
    
    
    #top_airports = Airport.objects.annotate(
    #    id__count=Count(
    #        'origins', distinct=True, filter=Q(owner=user) | #Q(owner=user)
            #Case(
            #    When(owners=user, then=1),
            #    default=0,
            #    output_field=IntegerField()
            #)
    #    )
    #)
    
    #top_airports = airports_list.annotate(id__count=Count('origins', filter=))
    print(top_airports)

    
    #top_origins = Airport.objects.filter(origins__owner=user).annotate(id__count=Count('origins', distinct=True)).order_by('-id__count')
    #top_destinations = Airport.objects.filter(destinations__owner=user).annotate(id__count=Count('destinations', distinct=True)).order_by('-id__count')

    top_planes = flights_list.values('aircraft').annotate(Count('id')).order_by('-id__count')
    top_airlines = flights_list.values('airline').annotate(Count('id')).order_by('-id__count')
    
    top_routes = flights_list.values('origin__iata', 'origin__name', 'origin__city', 'origin__country', 'destination__iata', 'destination__name', 'destination__city', 'destination__country', 'origin__latitude', 'origin__longitude', 'destination__latitude', 'destination__longitude').annotate(Count('id')).order_by('-id__count')
    
    
    
    context = {'top_airports': top_airports,
               'top_planes': top_planes,
               'top_airlines': top_airlines,
               'top_routes': top_routes,
              }
    
    html = render_to_string('flights/ajax/statistics.html', context, request=request)
    
    return HttpResponse(html)

@login_required
def draw_add(request):
    if not request.is_ajax():
        raise PermissionDenied
    user = request.user
    form = FlightForm()
    
    context = {'form': form}
    
    html = render_to_string('flights/ajax/add.html', context, request=request)
    
    return HttpResponse(html)

@login_required
def edit_flight(request):
    if not request.is_ajax():
        raise PermissionDenied
    
    pk = request.GET.get('pk')
    new_date = request.GET.get('date')
    new_number = request.GET.get('number').strip()
    new_airline = request.GET.get('airline').strip()
    new_aircraft = request.GET.get('aircraft').strip()
    new_aircraft_registration = request.GET.get('aircraft_registration').strip()
    
    flight = Flight.objects.get(pk=pk)
    if flight.owner != request.user:
        raise PermissionDenied
    
    try:
        flight.date = new_date
        flight.number = new_number
        flight.airline = new_airline
        flight.aircraft = new_aircraft
        flight.aircraft_registration = new_aircraft_registration
        flight.save()
    except:
        raise FieldError
        
    return HttpResponse('AJAX request fulfilled successfully')

@login_required
def move_flights(request):
    if not request.is_ajax():
        raise PermissionDenied
    
    pk1 = request.GET.get('pk1')
    sortid1 = request.GET.get('sortid1')
    pk2 = request.GET.get('pk2')
    sortid2 = request.GET.get('sortid2')
    
    flight1 = Flight.objects.get(pk=pk1)
    flight2 = Flight.objects.get(pk=pk2)
    
    if flight1.owner != request.user:
        raise PermissionDenied
    if flight2.owner != request.user:
        raise PermissionDenied
    
    try:
        flight1.sortid = sortid1
        flight2.sortid = sortid2
        flight1.save()
        flight2.save()
    except:
        raise FieldError
    
    return HttpResponse('AJAX request fulfilled successfully')

@login_required
def delete_flight(request):
    if not request.is_ajax():
        raise PermissionDenied
    
    pk = request.GET.get('pk')
    
    flight = Flight.objects.get(pk=pk)
    if flight.owner != request.user:
        raise PermissionDenied
        
    try:
        flight.delete()
    except:
        raise FieldError
    
    return HttpResponse('AJAX request fulfilled successfully')