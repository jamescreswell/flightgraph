from django.conf.urls import url, include
from django.urls import path

from . import views, ajax

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
    path('profile/<str:username>/', views.flights, name='profile'),
]
