import asyncio
from abc import abstractmethod
import httpx
from stashbus.db_models import Payload, Quote, OWMPayload, OpenWeatherResponse, Price
from typing import TypeVar, Generic, Type
from enum import StrEnum
from dataclasses import field, dataclass
import urllib.parse
from datetime import datetime
from stashbus.rest_models import DataProducer, Command, Secret, MempoolResponse
import logging
from pydantic import ValidationError
from decimal import Decimal


logging.basicConfig(level=logging.INFO)


class StashbusError(Exception):
    pass


class NoAuth(httpx.Auth):
    pass


T = TypeVar("T", bound=Payload)


class DataClient(Generic[T]):
    http_cli = httpx.Client()

    @property
    @abstractmethod
    def get_model_class(self) -> Type[T]:
        pass

    @property
    @abstractmethod
    def url(self) -> str:
        pass

    @property
    def auth(self) -> httpx.Auth:
        return NoAuth()

    async def aget_data(self) -> T:
        async with httpx.AsyncClient() as http_cli:
            response = await http_cli.get(self.url, auth=self.auth)
            try:
                response.raise_for_status()
            except Exception as err:
                new_exc = StashbusError(f"{err} {response.text}")
                raise new_exc from err
            else:
                try:
                    return self.parse_data(response.text)
                except ValidationError:
                    logging.error(
                        f"The {response} couldn't parsed. Request was {response.request}"
                    )
                    raise

    def get_data(self) -> T:
        return asyncio.run(self.aget_data())

    @abstractmethod
    def parse_data(self, data: str) -> T:
        pass


class Mempool(DataClient[Quote]):
    BASEURL = "https://mempool.space/api/v1/prices"

    @property
    def model_class(self):
        return Quote

    @property
    def url(self):
        return self.BASEURL

    def parse_data(self, data: str) -> Quote:
        try:
            mempool_response = MempoolResponse.model_validate_json(data)
            message = self.model_class(
                received_at=datetime.now(),
                price=Price.model_validate(mempool_response.model_dump()),
            )
            return message
        except ValidationError as err:
            logging.error(f"Data: {data} couldn't be understood. {err}")
            raise


@dataclass
class CryptoCompareClient(DataClient[Quote]):
    fsym: StrEnum
    tsym: StrEnum
    api_key: str = field(repr=False)

    BASEURL = "https://min-api.cryptocompare.com/data/price?"

    @property
    def model_class(self):
        return Quote

    @property
    def url(self):
        return self.BASEURL + urllib.parse.urlencode(
            dict(fsym=self.fsym, tsyms=self.tsym)
        )

    def parse_data(self, data: str) -> Quote:
        try:
            price = Price.model_validate_json(data)
            message = self.model_class(received_at=datetime.now(), price=price)
            return message
        except ValidationError:
            logging.error(f"Got invalid data: {data}.")
            raise

    @property
    def auth(self):
        return CryptoCompareAuth(self.api_key)


class CryptoCompareAuth(httpx.Auth):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def auth_flow(self, request: httpx.Request):
        # Send the request, with a custom `X-Authentication` header.
        request.headers["Apikey"] = self.api_key
        yield request


@dataclass
class OWMClient(DataClient[OWMPayload]):
    lat: float
    lon: float
    appid: str

    BASEURL = "https://api.openweathermap.org/data/3.0/onecall?"

    @property
    def model_class(self):
        return OWMPayload

    @property
    def url(self):
        params: dict[str, str] = {
            "lat": str(self.lat),
            "lon": str(self.lon),
            "appid": self.appid,
            "units": "metric",
        }
        return self.BASEURL + urllib.parse.urlencode(params)

    def parse_data(self, data: str) -> OWMPayload:
        return self.model_class(
            received_at=datetime.now(),
            **OpenWeatherResponse.model_validate_json(data).current.model_dump(),
        )


@dataclass
class StashRESTClient:
    producer_id: int = field()
    stashrest_url: str = field()
    http_cli = httpx.Client()

    def current_command(self) -> Command:
        return DataProducer.model_validate_json(
            self.http_cli.get(
                f"{self.stashrest_url}/data_producers/{self.producer_id}/"
            ).text
        ).command

    def secret(self, name: str) -> str:
        try:
            return Secret.model_validate_json(
                self.http_cli.get(f"{self.stashrest_url}/secrets/{name}/").text
            ).value
        except httpx.HTTPError as error:
            logging.error(
                f"Error while retrieving secret {name}: {error}. Will attempt getting the file-based secret."
            )
            return get_key(name)


def get_key(keyname: str) -> str:
    with open(f"/run/secrets/{keyname}", "r") as file:
        return file.read()
