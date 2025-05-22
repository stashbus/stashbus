from django.db import models
import mongoengine as me
from stashbus.models.mqtt_models import OWMPayload, Quote


class DataProducer(models.Model):
    name = models.CharField(max_length=30)

    class Command(models.TextChoices):
        PRODUCE = "PRODUCE"
        STOP = "STOP"

    command = models.CharField(
        max_length=7,
        choices=Command,
        default=Command.PRODUCE,
    )


class Secret(models.Model):
    name = models.CharField(max_length=30, primary_key=True)
    value = models.TextField(max_length=2048)


class WeatherData(me.Document):
    recieved_at = me.DateTimeField(required=True)
    price = me.FloatField()
    in_stock = me.BooleanField(default=True)
