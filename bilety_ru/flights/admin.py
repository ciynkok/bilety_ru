from django.contrib import admin
from .models import FlightOffer, FlightRequest, FlightSegment, Booking

# Register your models here.

admin.site.register(FlightOffer)
admin.site.register(FlightRequest)
admin.site.register(FlightSegment)
admin.site.register(Booking)
