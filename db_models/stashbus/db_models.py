from pydantic import BaseModel, Field
from decimal import Decimal
from enum import StrEnum, auto
from datetime import datetime
from typing import Optional, Any


class Currency(StrEnum):
    BTC = auto()
    USD = auto()


class Price(BaseModel):
    USD: Decimal


class Payload(BaseModel):
    received_at: datetime


class Message(Payload):
    id: Optional[str] = Field(alias="_id", default=None)  # Mongo ObjectId as string
    price: Price


class CurrentWeather(BaseModel):
    temp: float
    pressure: float
    humidity: float
    wind_speed: float
    wind_deg: float
    wind_gust: Optional[float] = None


class OpenWeatherResponse(BaseModel):
    lat: float
    lon: float
    current: CurrentWeather


class OWMPayload(Payload, CurrentWeather):
    id: Optional[str] = Field(alias="_id", default=None)  # Mongo ObjectId as string
