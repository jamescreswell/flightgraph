from django.shortcuts import render
from django.http import HttpResponse
from .models import Airport

def index(request):
    string = ''
    for airport in Airport.objects.all():
        string += airport.name + ' (' + airport.iata + ')\n'
    return HttpResponse(string)
