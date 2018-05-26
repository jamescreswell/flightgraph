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


import matplotlib
matplotlib.use('Agg') # Server has no GUI
import matplotlib.pyplot as plt
#from mpl_toolkits.basemap import Basemap

def index(request):
    context = {'nav_id': 'index_nav',
               'name': 'index',
               'username': request.user.username,
              }
    return render(request, 'flights/index.html', context)

def airports(request):
    pass

def map(request, username=None):
    if username is not None:
        user = User.objects.get(username=username)
    else:
        user = request.user
    
    #flights_list = Flight.objects.filter(owner=user)
    airports_list = Airport.objects.filter(Q(origins__owner=user) | Q(destinations__owner=user)).distinct()
    
    routes_list = Flight.objects.filter(owner=user).values('origin__pk', 'origin__latitude', 'origin__longitude', 'destination__pk', 'destination__latitude', 'destination__longitude').annotate(Count('id'))
    
    context = {'airports': airports_list,
               'routes': routes_list,
               'username': user.username,
              }
    
    return render(request, 'flights/map.html', context)

def gcmap(request):
    context = {'method': 'GET',
               'nav_id': 'gcmap_nav',
               'username': request.user.username,
              }

    return render(request, 'flights/gcmap.html', context)

def export(request):
    if request.method != 'POST':
        raise PermissionDenied

    data = request.POST

    if data['filetype'] == 'pdf':
        response = HttpResponse(content_type='application/pdf')
    elif data['filetype'] == 'png':
        response = HttpResponse(content_type='image/png')
    else:
        raise UnreadablePostError

    # Checkboxes don't POST????
    #if data['borders']:
    #    m.drawcoastlines()
    #    m.drawcountries()

    ### Start interpret search string...should be abstracted ###
    try:
        input_routes = data['search_string'].split(",")
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
    ### End interpret search string...should be abstracted ###

    lat_0 = float(sum([airport.latitude for airport in airports])) / max(len(airports), 1)
    lon_0 = float(sum([airport.longitude for airport in airports])) / max(len(airports), 1)

    llcrnrlon = min([airport.longitude for airport in airports]) - 10.0
    llcrnrlat = min([airport.latitude for airport in airports]) - 10.0
    urcrnrlon = max([airport.longitude for airport in airports]) + 10.0
    urcrnrlat = max([airport.latitude for airport in airports]) + 10.0

    plt.figure()
    if data['projection'] in ['ortho', 'robin', 'moll']:
        m = Basemap(width=10000000,
                    height=10000000,
                    projection=data['projection'],
                    lat_0=lat_0,
                    lon_0=lon_0,
                    resolution='l',
                    area_thresh=1000.0
                   )
    elif data['projection'] in ['mill', 'stere']:
        return HttpResponse('Selected projection doesn\'t work yet')
        m = Basemap(width=10000000,
                    height=10000000,
                    projection=data['projection'],
                    llcrnrlon=llcrnrlon,
                    llcrnrlat=llcrnrlat,
                    urcrnrlon=urcrnrlon-360.0,
                    urcrnrlat=urcrnrlat,
                    resolution='l',
                    area_thresh=1000.0
                   )

    m.shadedrelief(scale=0.45)

    for airport in airports:
        m.scatter(airport.longitude, airport.latitude, s=3, latlon=True, color='red', zorder=100)

    for route in route_pairs:
        m.drawgreatcircle(route[0].longitude, route[0].latitude, route[1].longitude, route[1].latitude, del_s=100.0, color='red')

    plt.savefig(response, format=data['filetype'], dpi=300)
    return response

def flights(request, username=None):
    start = time.time()

    if request.method == 'POST':
        try:
            f = FlightForm(request.POST)
            f.instance.distance = -1
            try:
                f.instance.sortid = Flight.objects.filter(owner=request.user).order_by('-sortid')[0].sortid + 1
            except:
                f.instance.sortid = 0
            f.instance.owner = request.user
            new_flight = f.save()
            new_flight.distance = new_flight.origin.distance_to(new_flight.destination)
            new_flight.save()
            new_flight.set_distance()
        except:
            return HttpRequest("Form validation error")

    if username == None:
        if request.user.is_authenticated:
            user = request.user
            nav_id = 'flights_nav'
        else:
            return redirect('login')
    else:
        user = User.objects.get(username=username)
        nav_id = None

    flights_list = Flight.objects.filter(owner=user)

    airports_list = Airport.objects.filter(Q(origins__owner=user) | Q(destinations__owner=user)).distinct()

    top_airports = airports_list.annotate(
        id__count=Count('origins', filter=Q(origins__owner=user), distinct=True)+Count('destinations', filter=Q(destinations__owner=user), distinct=True)
    ).order_by('iata')

    planes = flights_list.values('aircraft').distinct().order_by('aircraft')
    airlines = flights_list.values('airline').distinct().order_by('airline')

    routes_list = flights_list.values('origin__latitude', 'origin__longitude', 'destination__latitude', 'destination__longitude').annotate(Count('id'))
    try:
        distance_mi = flights_list.aggregate(Sum('distance'))['distance__sum']
        distance_km = distance_mi * 6371.0/3959.0
    except:
        # flights_list is empty
        distance_mi = distance_km = 0

    context = {'nav_id': nav_id,
               'username': request.user.username,
               'query_username': username,
               'display_username': user.username,
               'flights': flights_list,
               'airports': top_airports,
               'routes': routes_list,
               'planes': planes,
               'airlines': airlines,
               'loading_time': time.time() - start,
               'method': request.method,
               'distance_mi': distance_mi,
               'distance_km': distance_km,
              }

    return render(request, 'flights/flights.html', context)

def flights_map(request):
    pass

def compare(request, username1, username2):
    user1 = User.objects.get(username=username1)
    user2 = User.objects.get(username=username2)

    flights_list1 = Flight.objects.filter(owner=user1)
    flights_list2 = Flight.objects.filter(owner=user2)

    top_airports1 = Airport.objects.annotate(
        id__count=Count('origins', filter=Q(origins__in=flights_list1), distinct=True)+Count('destinations', filter=Q(destinations__in=flights_list1), distinct=True)
    ).filter(Q(id__count__gt=0)).order_by('-id__count')
    top_planes1 = flights_list1.values('aircraft').annotate(Count('id')).order_by('-id__count')
    top_airlines1 = flights_list1.values('airline').annotate(Count('id')).order_by('-id__count')
    top_routes1 = flights_list1.values('origin__iata', 'origin__name', 'origin__city', 'origin__country', 'destination__iata', 'destination__name', 'destination__city', 'destination__country', 'origin__latitude', 'origin__longitude', 'destination__latitude', 'destination__longitude').annotate(Count('id')).order_by('-id__count')



    top_countries1 = Airport.objects.values('country', 'country_iso').annotate(
        id__count=Count('origins', filter=Q(origins__in=flights_list1), distinct=True)+Count('destinations', filter=Q(destinations__in=flights_list1), distinct=True)
    ).filter(Q(id__count__gt=0))

    top_countries2 = Airport.objects.values('country', 'country_iso').annotate(
        id__count=Count('origins', filter=Q(origins__in=flights_list2), distinct=True)+Count('destinations', filter=Q(destinations__in=flights_list2), distinct=True)
    ).filter(Q(id__count__gt=0))





    top_airports2 = Airport.objects.annotate(
        id__count=Count('origins', filter=Q(origins__in=flights_list2), distinct=True)+Count('destinations', filter=Q(destinations__in=flights_list2), distinct=True)
    ).filter(Q(id__count__gt=0)).order_by('-id__count')
    top_planes2 = flights_list2.values('aircraft').annotate(Count('id')).order_by('-id__count')
    top_airlines2 = flights_list2.values('airline').annotate(Count('id')).order_by('-id__count')
    top_routes2 = flights_list2.values('origin__iata', 'origin__name', 'origin__city', 'origin__country', 'destination__iata', 'destination__name', 'destination__city', 'destination__country', 'origin__latitude', 'origin__longitude', 'destination__latitude', 'destination__longitude').annotate(Count('id')).order_by('-id__count')

    try:
        distance_mi1 = flights_list1.aggregate(Sum('distance'))['distance__sum']
        distance_km1 = distance_mi1 * 6371.0/3959.0
    except:
        # flights_list is empty
        distance_mi1 = distance_km1 = 0

    try:
        distance_mi2 = flights_list2.aggregate(Sum('distance'))['distance__sum']
        distance_km2 = distance_mi2 * 6371.0/3959.0
    except:
        # flights_list is empty
        distance_mi2 = distance_km2 = 0

    #airports_both = Airport.objects.filter(Q(origins__in=flights_list1)|Q(destinations__in=flights_list1)).filter(Q(origins__in=flights_list2)|Q(destinations__in=flights_list2)).distinct().annotate(
    #    id__count=Count('origins', filter=Q(origins__in=flights_list1), distinct=True)+Count('destinations', filter=Q(destinations__in=flights_list1), distinct=True)
    #)

    #airports1 = Airport.objects.filter(Q(origins__in=flights_list1)|Q(destinations__in=flights_list1)).values('iata', distinct=True)
    #print(airports1)
    airports_both1 = Airport.objects.filter(Q(origins__in=flights_list1)|Q(destinations__in=flights_list1)).distinct()
    airports_both2 = Airport.objects.filter(Q(origins__in=flights_list2)|Q(destinations__in=flights_list2)).distinct()
    airports_both = airports_both1.filter(pk__in=airports_both2)
    print(airports_both.query)
    #print(airports_both.get(iata='PVG'))
    #print(airports_test)
    #print(list(airports_both))
    for airport in airports_both:
        airport.count1 = top_airports1.get(pk=airport.pk).id__count
        airport.count2 = top_airports2.get(pk=airport.pk).id__count


    airports_only1 = top_airports1.exclude(pk__in=airports_both)
    airports_only2 = top_airports2.exclude(pk__in=airports_both)

    airports_both = sorted(airports_both, key=lambda x: x.count1, reverse=True)



    #countries_both = Airport.objects.filter((Q(origins__in=flights_list1)|Q(destinations__in=flights_list1)) & (Q(origins__in=flights_list2)|Q(destinations__in=flights_list2))).values('country', 'country_iso').annotate(
    #    id__count=Count('origins', filter=Q(origins__in=flights_list1), distinct=True)+Count('destinations', filter=Q(destinations__in=flights_list1), distinct=True)
    #)

    countries_both1 = Airport.objects.filter(Q(origins__in=flights_list1)|Q(destinations__in=flights_list1)).distinct().values('country')#, 'country_iso')
    countries_both2 = Airport.objects.filter(Q(origins__in=flights_list2)|Q(destinations__in=flights_list2)).distinct().values('country')#, 'country_iso')
    countries_both = countries_both1.filter(country__in=countries_both2)
    for country in countries_both:
        country['count1'] = top_countries1.get(country=country['country'])['id__count']
        country['count2'] = top_countries2.get(country=country['country'])['id__count']
        country['country_iso'] = top_countries1.get(country=country['country'])['country_iso']

    countries_only1 = top_countries1.exclude(country__in=countries_both.values('country')).order_by('-id__count')
    countries_only2 = top_countries2.exclude(country__in=countries_both.values('country')).order_by('-id__count')

    countries_both = sorted(countries_both, key=lambda x: x['count1'], reverse=True)


    planes_both = flights_list1.filter(aircraft__in=flights_list2.values('aircraft')).values('aircraft').annotate(
        count1=Count('id')
    ).order_by('-count1')
    for plane in planes_both:
        plane['count2'] = top_planes2.get(aircraft=plane['aircraft'])['id__count']

    planes_only1 = flights_list1.exclude(aircraft__in=flights_list2.values('aircraft')).values('aircraft').annotate(
        count1=Count('id')
    ).order_by('-count1')

    planes_only2 = flights_list2.exclude(aircraft__in=flights_list1.values('aircraft')).values('aircraft').annotate(
        count2=Count('id')
    ).order_by('-count2')



    airlines_both = flights_list1.filter(airline__in=flights_list2.values('airline')).values('airline').annotate(
        count1=Count('id')
    ).order_by('-count1')
    for airline in airlines_both:
        airline['count2'] = top_airlines2.get(airline=airline['airline'])['id__count']

    airlines_only1 = flights_list1.exclude(airline__in=flights_list2.values('airline')).values('airline').annotate(
        count1=Count('id')
    ).order_by('-count1')

    airlines_only2 = flights_list2.exclude(airline__in=flights_list1.values('airline')).values('airline').annotate(
        count2=Count('id')
    ).order_by('-count2')



    #flights_list1.values('aircraft').intersection(flights_list2.values('aircraft'))#flights_list1.values('aircraft').intersection(flights_list2.values('aircraft'))


    context = {'username1': user1.username,
               'username2': user2.username,
               'n_flights1': len(flights_list1),
               'n_flights2': len(flights_list2),
               'distance_mi1': distance_mi1,
               'distance_km1': distance_km1,
               'distance_mi2': distance_mi2,
               'distance_km2': distance_km2,
               'top_airports1': top_airports1,
               'top_airports2': top_airports2,
               'airports_both': airports_both,
               'airports_only1': airports_only1,
               'airports_only2': airports_only2,
               'planes_both': planes_both,
               'planes_only1': planes_only1,
               'planes_only2': planes_only2,
               'airlines_both': airlines_both,
               'airlines_only1': airlines_only1,
               'airlines_only2': airlines_only2,
               'countries_both': countries_both,
               'countries_only1': countries_only1,
               'countries_only2': countries_only2,
               'top_countries1': top_countries1,
               'top_countries2': top_countries2,
               'top_routes1': top_routes1,
               'top_routes2': top_routes2,
              }

    return render(request, 'flights/compare.html', context)

@login_required
def settings(request):
    if request.method == 'POST':
        pass
    user = request.user
    user_profile = UserProfile.objects.get(user=user)


    context = {'nav_id': None,
               'username': request.user.username}

    return render(request, 'flights/settings.html', context)

def create_account(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('flights')
    else:
        form = UserCreationForm()
    return render(request, 'registration/create_account.html', {'form': form})

def mileage_graph(request, user1, user2):
    if user2 != 'null':
        usernames = [user1, user2]
    else:
        usernames = [user1,]
    dates, dists = {}, {}
    for user in usernames:
        flights = Flight.objects.filter(owner__username=user).order_by('date')
        dates[user] = []
        dists[user] = [0]
        for flight in flights:
            dates[user].append(matplotlib.dates.date2num(flight.date))
            dists[user].append(dists[user][-1] + flight.distance)



    #response = HttpResponse(content_type='image/png')

    plt.figure()

    for user in usernames:
        plt.plot_date(dates[user], dists[user][1:], marker=None, linestyle='-', xdate=True, label=user)

    plt.legend()
    plt.xlabel('Date')
    plt.ylabel('Distance (mi)')
    import io
    buf = io.BytesIO()


    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    response = HttpResponse(buf.getvalue(), content_type='image/png')
    return response

def airport_graph(request, user1, user2):
    if user2 != 'null':
        usernames = [user1, user2]
    else:
        usernames = [user1,]
    dates, airport_count, airports_visited = {}, {}, {}
    for user in usernames:
        flights = Flight.objects.filter(owner__username=user).order_by('date')
        dates[user] = []
        airport_count[user] = [0]
        airports_visited[user] = set()
        for flight in flights:
            dates[user].append(matplotlib.dates.date2num(flight.date))
            airports_visited[user].add(flight.origin.pk)
            airports_visited[user].add(flight.destination.pk)
            airport_count[user].append(len(airports_visited[user]))



    #response = HttpResponse(content_type='image/png')

    plt.figure()

    for user in usernames:
        plt.plot_date(dates[user], airport_count[user][1:], marker=None, linestyle='-', xdate=True, label=user)
    
    plt.legend()
    plt.xlabel('Date')
    plt.ylabel('Airports visited')
    import io
    buf = io.BytesIO()


    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    response = HttpResponse(buf.getvalue(), content_type='image/png')
    return response

def country_graph(request, user1, user2):
    if user2 != 'null':
        usernames = [user1, user2]
    else:
        usernames = [user1,]
    dates, country_count, countries_visited = {}, {}, {}
    for user in usernames:
        flights = Flight.objects.filter(owner__username=user).order_by('date')
        dates[user] = []
        country_count[user] = [0]
        countries_visited[user] = set()
        for flight in flights:
            dates[user].append(matplotlib.dates.date2num(flight.date))
            countries_visited[user].add(flight.origin.country)
            countries_visited[user].add(flight.destination.country)
            country_count[user].append(len(countries_visited[user]))



    #response = HttpResponse(content_type='image/png')

    plt.figure()

    for user in usernames:
        plt.plot_date(dates[user], country_count[user][1:], marker=None, linestyle='-', xdate=True, label=user)

    plt.legend()
    plt.xlabel('Date')
    plt.ylabel('Countries visited')
    import io
    buf = io.BytesIO()


    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    response = HttpResponse(buf.getvalue(), content_type='image/png')
    return response