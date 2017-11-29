from django.contrib import admin

from .models import Airport

class AirportAdmin(admin.ModelAdmin):
    list_display = ('iata', 'icao', 'name', 'city', 'region', 'country', 'id')
    list_display_links = ('name',)
    
    search_fields = ('name', 'iata', 'icao')
    
    list_filter = ['country']
    
admin.site.register(Airport, AirportAdmin)