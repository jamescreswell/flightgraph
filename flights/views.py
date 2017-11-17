from django.shortcuts import render
from django.http import HttpResponse
from .models import Airport

def index(request):
    context = {'title': 'Test',
              }
    return render(request, 'flights/index.html', context)
