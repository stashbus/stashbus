import logging
import urllib.parse
from datetime import datetime
from stashbus.mqtt_publishers import RESTPublisher
from dataclasses import dataclass

from stashbus.db_models import OWMPayload, OpenWeatherResponse

logging.basicConfig(level=logging.INFO)

OWM_BASEURL = "https://api.openweathermap.org/data/3.0/onecall?"
BRNO_LAT_LON = 49.19522000, 16.60796000


@dataclass
class OWMPublisher(RESTPublisher[OWMPayload]):
    lat: float
    lon: float
    appid: str
    topic: str

    @property
    def url(self):
        params: dict[str, str] = {
            "lat": str(self.lat),
            "lon": str(self.lon),
            "appid": self.appid,
            "units": "metric",
        }
        return OWM_BASEURL + urllib.parse.urlencode(params)

    def parse_data(self, data: str) -> OWMPayload:
        return OWMPayload(
            received_at=datetime.now(),
            **OpenWeatherResponse.model_validate_json(data).current.model_dump(),
        )
