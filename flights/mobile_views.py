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

def add(request):
    if request.method == 'POST':
        try:
            pass
        except:
            return HttpRequest("Form validation error")
    else:
        context = {'form': 0}
        return render(request, 'mobile/add.html', context)

@csrf_exempt # This disables all CSRF security, please fix as soon as possible (JS fetch POSTs without credentials...)
def search_airports(request):
    if request.method == 'POST':
        try: 
            airport = Airport.objects.get(iata=request.body.decode('utf-8').strip().upper())
            # if multiple hits, take the most recent
            # if no iata, not possible from this function
            return JsonResponse({'status': 1, 'name': airport.name, 'iata': airport.iata})
        except:
            return JsonResponse({'status': 0});