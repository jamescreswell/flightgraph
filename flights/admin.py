from django.contrib import admin

from .models import Airport, Flight

class AirportAdmin(admin.ModelAdmin):
    list_display = ('iata', 'icao', 'name', 'city', 'region', 'country', 'id')
    list_display_links = ('name',)
    
    search_fields = ('name', 'iata', 'icao')
    
    list_filter = ['country']

class FlightAdmin(admin.ModelAdmin):
    pass

admin.site.register(Airport, AirportAdmin)
admin.site.register(Flight, FlightAdmin)