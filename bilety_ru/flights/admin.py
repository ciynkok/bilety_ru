from django.contrib import admin
from .models import FlightOffer, FlightRequest, FlightSegment, Booking, AirLineRaiting

# Register your models here.

admin.site.register(FlightOffer)
admin.site.register(FlightRequest)
admin.site.register(FlightSegment)
admin.site.register(Booking)
admin.site.register(AirLineRaiting)
