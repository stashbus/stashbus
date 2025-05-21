import urllib.parse
import httpx
from stashbus.mqtt_publishers import RESTPublisher
import logging
from enum import StrEnum
from dataclasses import field, dataclass
from datetime import datetime
from stashbus.db_models import Message, Price

logging.basicConfig(level=logging.INFO)


CRYPTOCOMPARE_BASEURL = "https://min-api.cryptocompare.com/data/price?"


class CoindeskAuth(httpx.Auth):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def auth_flow(self, request: httpx.Request):
        # Send the request, with a custom `X-Authentication` header.
        request.headers["Apikey"] = self.api_key
        yield request


@dataclass
class CryptoComparePublisher(RESTPublisher[Message]):
    fsym: StrEnum
    tsym: StrEnum
    api_key: str = field(repr=False)

    @property
    def url(self):
        return CRYPTOCOMPARE_BASEURL + urllib.parse.urlencode(
            dict(fsym=self.fsym, tsyms=self.tsym)
        )

    def parse_data(self, data: str) -> Message:
        return Message.model_validate(
            dict(received_at=datetime.now(), price=Price.model_validate_json(data))
        )

    @property
    def auth(self):
        return CoindeskAuth(self.api_key)
