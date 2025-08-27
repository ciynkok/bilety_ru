from django.db import models

# Create your models here.

class IATA(models.Model):
    iata = models.CharField(max_length=3)
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
