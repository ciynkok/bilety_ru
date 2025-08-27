from .models import FlightRequest
import datetime


def delete_req():
    print("Hello world")
    delete_time = (datetime.datetime.now() - datetime.timedelta(minutes=1))
    FlightRequest.objects.filter(create_in__lte=delete_time).delete()

