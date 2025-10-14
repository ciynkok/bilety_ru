from django.db import models
from user_management.models import CustomUser as User
import datetime

# Create your models here.


class FlightRequest(models.Model):
    SORT_PARMS = (('price_asc', 'Цене'), ('duration_asc', 'Длительности'), ('departure_asc', 'Времени вылета'))
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True)  # Для хранения ключа сессии
    currencyCode = models.CharField(max_length=50)
    originLocationCode = models.CharField(max_length=50)
    destinationLocationCode = models.CharField(max_length=50)
    departureDate = models.DateField()
    returnDate = models.DateField(null=True, blank=True)
    adults = models.IntegerField(default=1)
    children = models.IntegerField(null=True, blank=True)
    infants = models.IntegerField(null=True, blank=True)
    cabin = models.CharField(max_length=20, null=True, blank=True)
    includedAirlines = models.CharField(max_length=200, null=True, blank=True)
    excludedAirlines = models.CharField(max_length=200, null=True, blank=True)
    travelClass = models.CharField(max_length=50, null=True, blank=True)
    nonStop = models.BooleanField(null=True, blank=True)
    maxPrice = models.IntegerField(null=True, blank=True)
    sortParam = models.CharField(max_length=50, choices=SORT_PARMS, default='price_asc')
    created_at = models.DateTimeField(auto_now_add=True)  # Новое поле для времени создания


class FlightOffer(models.Model):
    flightRequest = models.ForeignKey(FlightRequest, on_delete=models.CASCADE)
    adults_count = models.IntegerField()
    children_count = models.IntegerField(null=True, blank=True)
    infants_count = models.IntegerField(null=True, blank=True)
    dep_duration = models.DateTimeField()
    arr_duration = models.DateTimeField(default=None, null=True, blank=True)
    duration = models.TimeField()
    currencyCode = models.CharField(max_length=3)
    totalPrice = models.DecimalField(max_digits=10, decimal_places=2)
    oneWay = models.BooleanField(default=False)
    data = models.JSONField()


class FlightSegment(models.Model):
    offer = models.ForeignKey(FlightOffer, on_delete=models.CASCADE)
    there_seg = models.BooleanField(default=True)
    dep_iataCode = models.CharField(max_length=3)
    dep_airport = models.CharField(max_length=50)
    dep_terminal = models.CharField(max_length=2, null=True)
    dep_dateTime = models.DateTimeField()
    arr_iataCode = models.CharField(max_length=3)
    arr_airport = models.CharField(max_length=50)
    arr_terminal = models.CharField(max_length=2, null=True)
    arr_dateTime = models.DateTimeField()
    carrierCode = models.CharField(max_length=2)
    number = models.CharField(max_length=4, null=True)
    aircraftCode = models.CharField(max_length=4, null=True)
    operating = models.CharField(max_length=2, null=True)
    duration = models.TimeField()
    # id_seg = models.CharField(max_length=2)


class Booking(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Ожидает подтверждения'),
        ('CONFIRMED', 'Подтверждено'),
        ('CANCELLED', 'Отменено'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True)  # Для неавторизованных пользователей
    offer = models.ForeignKey(FlightOffer, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=50, blank=True)  # ID заказа в Amadeus
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency_code = models.CharField(max_length=3)
    
    # Информация о пассажирах
    passenger_data = models.JSONField(default=dict)  # Хранит информацию о пассажирах в формате JSON
    
    # Контактная информация
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Бронирование #{self.id} - {self.status}"

