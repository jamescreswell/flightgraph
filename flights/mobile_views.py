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

def index(request):
    context = {
        'name': 'index',
        'username': request.user.username,
    }
    return render(request, 'mobile/index.html', context)

def flights(request):
    context = {
        'name': 'flights',
    }
    
    return render(request, 'mobile/flights.html', context)

@login_required
def list(request):
    user = request.user

    flights_list = Flight.objects.filter(owner=user)

    context = {'flights': flights_list.order_by('-sortid'),
               'username': request.user.username,
              }
    
    return render(request, 'mobile/list.html', context)

@login_required
def flight_details(request, flight_pk):
    user = request.user
    flight = Flight.objects.get(pk=flight_pk)
    context = {
        'flight': flight,
    }
    return render(request, 'mobile/flight.html', context)

@login_required
def add(request):
    if request.method == 'POST':
        try:
            origin_airport = Airport.objects.get(pk=request.POST['origin-pk'])
            destination_airport = Airport.objects.get(pk=request.POST['destination-pk'])
            try:
                next_sortid = Flight.objects.filter(owner=request.user).order_by('-sortid')[0].sortid + 1
            except:
                next_sortid = 0
            f = Flight(date = request.POST['date'],
                       number = request.POST['number'],
                       origin = origin_airport,
                       destination = destination_airport,
                       airline = request.POST['airline'],
                       aircraft = request.POST['aircraft'],
                       aircraft_registration = request.POST['registration'],
                       owner=request.user,
                       distance=-1.0,
                       sortid=next_sortid)
            f.save()
            #new_flight.distance = new_flight.origin.distance_to(new_flight.destination)
            #new_flight.save()
            f.set_distance()
            #return redirect(index)
            added = True
        except:
            return HttpResponse("Form validation error")
    else:
        added = False
    context = {'form': 0, 
               'added': added
              }
    return render(request, 'mobile/add.html', context)
        
@login_required        
def statistics(request):
    user = request.user

    flights_list = Flight.objects.filter(owner=user)

    top_airports = Airport.objects.annotate(
        id__count=Count('origins', filter=Q(origins__in=flights_list), distinct=True)+Count('destinations', filter=Q(destinations__in=flights_list), distinct=True)
    ).filter(Q(id__count__gt=0)).order_by('-id__count')

    top_planes = flights_list.values('aircraft').annotate(Count('id')).order_by('-id__count')
    top_airlines = flights_list.values('airline').annotate(Count('id')).order_by('-id__count')

    top_routes = flights_list.values('origin__iata', 'origin__name', 'origin__city', 'origin__country', 'destination__iata', 'destination__name', 'destination__city', 'destination__country', 'origin__latitude', 'origin__longitude', 'destination__latitude', 'destination__longitude').annotate(Count('id')).order_by('-id__count')

    context = {'top_airports': top_airports,
               'top_planes': top_planes,
               'top_airlines': top_airlines,
               'top_routes': top_routes,
              }
    
    return render(request, 'mobile/statistics.html', context)