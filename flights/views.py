from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.core import serializers
from .models import Airport

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
        return HttpResponseForbidden('Permission denied: <tt>request.is_ajax() == False</tt>')
    
    input_string = request.GET.get('input_string')
    # input_string is of the format "abc-defg-hij-kil-...-xyz"

    # Extract codes
    try:
        hyphen_indices = [i for i, ltr in enumerate(input_string) if ltr == '-']
        codes = [input_string[0:hyphen_indices[0]],]
        i = -1
        for i in range(len(hyphen_indices)-1):
            codes.append(input_string[hyphen_indices[i]+1:hyphen_indices[i+1]])
        codes.append(input_string[hyphen_indices[i+1]+1:])
    except:
        raise ValueError('Invalid AJAX data')

    # Look up codes
    airports = []
    for code in codes:
        if len(code) == 3:
            match = Airport.objects.filter(iata=code.upper())
            if len(match) == 1:
                airports.append(match[0])
            elif len(match) == 0:
                pass
            else:
                # Problems...
                airports.append(match[0])
        elif len(code) == 4:
            match = Airport.objects.filter(icao=code.upper())
            if len(match) == 1:
                airports.append(match[0])
            elif len(match) == 0:
                pass
            else:
                # Problems...
                airports.append(match[0])
        else:
            # This should never happen
            raise ValueError('Invalid AJAX data')

    airports_as_json = serializers.serialize('json', airports)

    return JsonResponse(airports_as_json, safe=False)

def airports(request):
    pass

