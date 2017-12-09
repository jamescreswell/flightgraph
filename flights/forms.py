from django.forms import ModelForm, DateInput
from .models import Airport, Flight

class FlightForm(ModelForm):
    class Meta:
        model = Flight
        fields = ['origin', 'destination', 'date', 'number', 'airline', 'aircraft', 'aircraft_registration', 'travel_class', 'seat', 'operator', 'comments', 'picture']
        widgets = {
            'date': DateInput(attrs={'type': 'date'})
        }