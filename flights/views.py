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
        input_string = request.POST['input_string']
        # input_string is of the format "abc-defg-hij-kil-...-xyz"
        
        # Extract codes
        hyphen_indices = [i for i, ltr in enumerate(input_string) if ltr == '-']
        codes = [input_string[0:hyphen_indices[0]],]
        i = -1
        for i in range(len(hyphen_indices)-1):
            codes.append(input_string[hyphen_indices[i]+1:hyphen_indices[i+1]])
        codes.append(input_string[hyphen_indices[i+1]+1:])
        
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
                print('Error')
        print(airports)
        
        context = {'method': 'POST',
                   'nav_id': 'gcmap_nav',
                   'airports': airports,
                  }
        return render(request, 'flights/gcmap.html', context)
    else:
        origin = Airport.objects.filter(iata='DFW')[0]
        
        context = {'method': 'GET'}
        
        return render(request, 'flights/gcmap.html', context)
        


def airports(request):
    pass