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