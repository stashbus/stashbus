from pydantic import BaseModel, Field
from enum import StrEnum, auto
from datetime import datetime
from typing import Optional


class Currency(StrEnum):
    BTC = auto()
    USD = auto()


class Price(BaseModel):
    USD: float | None = Field(default=None)
    EUR: float | None = Field(default=None)
    GBP: float | None = Field(default=None)
    CAD: float | None = Field(default=None)
    CHF: float | None = Field(default=None)
    AUD: float | None = Field(default=None)
    JPY: float | None = Field(default=None)


class Payload(BaseModel):
    received_at: datetime


class Quote(Payload):
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
