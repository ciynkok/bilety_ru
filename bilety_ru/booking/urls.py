from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('<int:offer_id>/', views.BookingView.as_view(), name='booking_index'),
]
