from django.contrib import admin

from .models import Airport, Flight, UserProfile

class AirportAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'iata', 'icao', 'name', 'city', 'region', 'country', 'id')
    list_display_links = ('name',)
    
    search_fields = ('name', 'iata', 'icao')
    
    list_filter = ['country']

class FlightAdmin(admin.ModelAdmin):
    list_display = ('number', 'date', 'origin', 'destination', 'owner')
    list_display_links = ('number',)
    list_filter = ['owner', 'airline']
    
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'public', 'public_delay',)
    list_display_links = ('user',)

admin.site.register(Airport, AirportAdmin)
admin.site.register(Flight, FlightAdmin)
admin.site.register(UserProfile, UserProfileAdmin)