from django.conf.urls import url, include

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^gcmap/$', views.gcmap, name='gcmap'),
    url(r'^airports/$', views.airports, name='airports'),
    url(r'^ajax/draw_gcmap/$', views.draw_gcmap, name='draw_gcmap'),
    url(r'gcmap/export/$', views.export, name='export'),
    url(r'flights/$', views.flights, name='flights'),
    url(r'accounts/', include('django.contrib.auth.urls')),
]