from django.urls import path, include
from .views import OffersSearch, BookingView, BookingSuccessView, ClearSearchHistoryView
from api.views import get_cities

app_name = 'flights'

urlpatterns = [
    path('', OffersSearch.as_view(), name='home'),
    path('api_airport_search/', get_cities, name='api_airport_search'),
    path('clear-search-history/', ClearSearchHistoryView.as_view(), name='clear_search_history'),
    #path('booking/<int:offer_id>/', BookingView.as_view(), name='booking'),
    #path('booking/success/<int:booking_id>/', BookingSuccessView.as_view(), name='booking_success'),
]