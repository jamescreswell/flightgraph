from django.shortcuts import render
from django.http import HttpResponse
from .models import Airport

def index(request):
    context = {'nav_id': 'index_nav',
               'name': 'index',
              }
    return render(request, 'flights/index.html', context)

def gcmap(request):
    if request.method == 'POST':
        print(request.POST['origin'])
        origin = Airport.objects.filter(iata=request.POST['origin'])[0]
    else:
        origin = Airport.objects.filter(iata='DFW')[0]
        #return HttpResponse('Missing POST')
        #return render(request, 'flights/gcmap.html', context)
        
    context = {'nav_id': 'gcmap_nav',
               'origin': origin,
               'distance': origin.distance_to(origin),
              }
    return render(request, 'flights/gcmap.html', context)

def airports(request):
    pass