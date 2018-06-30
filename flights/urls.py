from django.conf.urls import url, include
from django.urls import path

from django.contrib.auth import views as auth_views

from . import views, ajax, mobile_views, api

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^gcmap/$', views.gcmap, name='gcmap'),
    url(r'^airports/$', views.airports, name='airports'),
    url(r'^ajax/draw_gcmap/$', ajax.draw_gcmap, name='draw_gcmap'),
    path('ajax/draw_map/<str:username>/', ajax.draw_map, name='draw_map'),
    path('ajax/draw_list/<str:username>/', ajax.draw_list, name='draw_list'),
    path('ajax/draw_stats/<str:username>/', ajax.draw_stats, name='draw_stats'),
    path('ajax/draw_add/', ajax.draw_add, name='draw_add'),
    url(r'^ajax/edit_flight/$', ajax.edit_flight, name='edit_flight'),
    url(r'^ajax/move_flights/$', ajax.move_flights, name='move_flights'),
    url(r'^ajax/delete_flight/$', ajax.delete_flight, name='delete_flight'),
    url(r'gcmap/export/$', views.export, name='export'),
    url(r'^flights/$', views.flights, name='flights'),
    url(r'^settings/$', views.settings, name='settings'),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^accounts/create_account/$', views.create_account, name='create_account'),
    path('profile/<str:username>/', views.map, name='profile'),
    path('compare/<str:username1>/<str:username2>/', views.compare, name='compare'),

    path('mobile/', mobile_views.index, name='mobile_index'),
    path('mobile/flights/', mobile_views.flights, name='mobile_flights'),
    path('mobile/list/', mobile_views.list, name='mobile_list'),
    path('mobile/statistics/', mobile_views.statistics, name='mobile_statistics'),
    path('mobile/flight/<int:flight_pk>/', mobile_views.flight_details, name='mobile_details'),
    path('mobile/accounts/login/', auth_views.LoginView.as_view(template_name='mobile/registration/login.html'), name='mobile_login'),
    path('mobile/add/', mobile_views.add, name='mobile_add'),

    path('api/search_airports/', api.search_airports, name='search_airports'),
    path('api/mileage_graph/usr1=<str:user1>&usr2=<str:user2>', views.mileage_graph, name='mileage_graph'),
    path('api/airport_graph/usr1=<str:user1>&usr2=<str:user2>', views.airport_graph, name='airport_graph'),
    path('api/country_graph/usr1=<str:user1>&usr2=<str:user2>', views.country_graph, name='country_graph'),
    path('api/top_airports_graph/<str:username>', views.top_airports_graph, name='top_airports_graph'),
    
    
    path('api/get_airport/<int:airport_id>', api.get_airport, name='get_airport'),
    path('api/get_airport_flights/<str:username>/<int:airport_id>', api.get_airport_flights, name='get_airport_flights'),
    path('api/get_route/<int:id1>/<int:id2>', api.get_route, name='get_route'),
    path('api/get_route_flights/<str:username>/<int:id1>/<int:id2>', api.get_route_flights, name='get_route_flights'),
    path('api/get_flights/<str:username>', api.get_flights, name='get_flights'),
    path('api/get_flight_details/<int:id>', api.get_flight_details),
    
    path('api/route_map/<int:id1>/<int:id2>', views.route_map),
    
    
    path('map', views.map, name='map'),
    path('list', views.list, name='list'),
]
