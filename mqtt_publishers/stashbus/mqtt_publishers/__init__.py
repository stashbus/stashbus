import httpx
from abc import ABC, abstractmethod

from typing import TypeVar, Generic, Any
import paho.mqtt.client as mqtt
from paho.mqtt.reasoncodes import ReasonCode
from paho.mqtt.properties import Properties
from paho.mqtt.enums import CallbackAPIVersion
import logging
from dataclasses import field, dataclass
from time import sleep
import ssl
import threading
from stashbus.db_models import Payload


logging.basicConfig(level=logging.INFO)


def get_key(keyname: str) -> str:
    with open(f"/run/secrets/{keyname}", "r") as file:
        return file.read()


class StashbusError(Exception):
    pass


class NoAuth(httpx.Auth):
    pass


T = TypeVar("T", bound=Payload)


@dataclass
class RESTPublisher(ABC, Generic[T]):
    mqtt_host: str = field()
    mqtt_port: int = field()
    ca_certs: str | None = field()
    certfile: str | None = field()
    keyfile: str | None = field()
    topic: str = field()
    period: float = field()
    mqtt_cli: mqtt.Client = field(init=False)
    http_cli: httpx.Client = field(init=False)
    do_work: threading.Event = field(init=False)

    def __post_init__(self):
        self.init_mqtt_client()
        self.http_cli = httpx.Client()
        self.do_work = threading.Event()

    def init_mqtt_client(self):
        logging.info(f"Starting.")
        self.mqtt_cli = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
        self.mqtt_cli.on_message = self.on_message
        self.mqtt_cli.on_connect = self.on_connect
        self.mqtt_cli.on_connect_fail = self.on_connect_fail
        self.mqtt_cli.on_socket_close = self.on_socket_close
        self.mqtt_cli.on_publish = self.on_publish
        if self.ca_certs:
            self.mqtt_cli.tls_set(self.ca_certs, certfile=self.certfile, keyfile=self.keyfile, cert_reqs=ssl.CERT_REQUIRED)  # type: ignore
        self.mqtt_cli.connect_async(self.mqtt_host, self.mqtt_port)

    @property
    @abstractmethod
    def url(self) -> str:
        pass

    @property
    def auth(self) -> httpx.Auth | None:
        return None

    def get_data(self):
        response = self.http_cli.get(self.url, auth=self.auth)
        try:
            response.raise_for_status()
        except Exception as err:
            new_exc = StashbusError(f"{err} {response.text}")
            raise new_exc from err
        else:
            return response.text

    @abstractmethod
    def parse_data(self, data: str) -> T:
        pass

    def publish(self, payload: T):
        logging.info(f"Publishing {payload}.")
        self.mqtt_cli.publish(self.topic, payload.model_dump_json())

    def on_publish(
        self,
        client: mqtt.Client,
        userdata: Any,
        mid: int,
        reason_code: ReasonCode,
        properties: Properties,
    ):
        logging.info(f"mid: {mid}.")

    def on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage):
        logging.info(f"Received {msg}.")

    def on_subscribe(
        self,
        client: mqtt.Client,
        userdata: Any,
        mid: int,
        reason_code_list: list[ReasonCode],
        properties: Properties,
    ):
        logging.info(f"Subscribed topic.")

    def on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        connect_flags: mqtt.ConnectFlags,
        reason_code: ReasonCode,
        properties: Properties | None,
    ):
        logging.info(f"Connected {self}.")
        self.do_work.set()

    def on_connect_fail(self, client: mqtt.Client, userdata: Any):
        logging.info(f"Connect failed {self}.")

    def on_socket_close(
        self, client: mqtt.Client, userdata: Any, socket: "mqtt.SocketLike"
    ):
        logging.info(f"Socket {socket} will be closed.")
        self.do_work.clear()

    def cycle(self):
        data = self.get_data()
        payload = self.parse_data(data)
        self.publish(payload)

    def run(self):
        self.mqtt_cli.loop_start()

        while True:
            logging.debug("Waiting for do_work condition.")
            self.do_work.wait()
            self.cycle()
            sleep(self.period)
