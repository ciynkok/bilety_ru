from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('<int:offer_id>/', views.BookingView.as_view(), name='booking_index'),
    path('booking_success/<int:booking_id>', views.BookingSuccessView.as_view(), name='booking_success'),
    path('booking_data/<int:booking_id>/', views.BookingDataView.as_view(), name='booking_data'),
]
