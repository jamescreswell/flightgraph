from django.shortcuts import render
from django.http import HttpResponse
from .models import Airport

def index(request):
    context = {'title': 'Test',
              }
    return render(request, 'flights/index.html', context)

def gcmap(request):
    if request.method == 'POST':
        print(request.POST['origin'])
        origin = Airport.objects.filter(iata=request.POST['origin'])[0]
        context = {'origin': origin}
        return render(request, 'flights/gcmap.html', context)
    else:
        return HttpResponse('Missing POST')
        #return render(request, 'flights/gcmap.html', context)
    