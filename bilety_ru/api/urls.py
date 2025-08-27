from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('cities/', views.get_cities, name='get_cities'),
    path('airports/', views.SearchAirports.as_view(), name='search_airports'),
    path('flight-offers/', views.get_structured_flight_offers, name='get_structured_flight_offers'),
    path('check-price/<int:offer_id>/', views.check_flight_price, name='check_flight_price'),
    path('flight-details/<int:offer_id>/', views.get_flight_details, name='get_flight_details'),
    path('create-order/<int:offer_id>/', views.create_flight_order, name='create_flight_order'),
    path('order/<str:order_id>/', views.get_order_info, name='get_order_info'),
]
