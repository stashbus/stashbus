import logging
import click
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
from paho.mqtt.reasoncodes import ReasonCode
from paho.mqtt.properties import Properties
from dataclasses import dataclass, field
from typing import Any, Dict
import json
import ssl
from pymongo import MongoClient
from pymongo.collection import Collection


logging.basicConfig(level=logging.INFO)


@dataclass
class StashbusSub:
    mqtt_host: str
    mqtt_port: int
    mqtt_ca_certs: str | None
    mqtt_certfile: str | None
    mqtt_keyfile: str | None
    mongodb_url: str
    mongodb_database: str
    logged_topic = "stashbus/#"
    control_topic = "stashbus/control"

    mongodb_cli: MongoClient[Dict[str, Any]] = field(init=False)
    messages: Collection[Dict[str, Any]] = field(init=False)

    def __post_init__(self):
        self.mongodb_cli = MongoClient(self.mongodb_url)
        self.db = self.mongodb_cli[self.mongodb_database]

    def parse_data(self, data: str):
        obj = json.loads(data)
        logging.info(f"Parsed payload: {obj}.")
        return obj

    def on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage):
        logging.info(
            f"Received message in topic: {msg.topic} with state: {msg.state} info: {msg.info}."
        )
        obj = self.parse_data(msg.payload.decode("utf-8"))
        self.db[msg.topic].insert_one(obj)

    def on_subscribe(
        self,
        client: mqtt.Client,
        userdata: Any,
        mid: int,
        reason_code_list: list[ReasonCode],
        properties: Properties,
    ):
        # Since we subscribed only for a single channel, reason_code_list contains
        # a single entry
        if reason_code_list[0].is_failure:
            logging.error(f"Broker rejected you subscription: {reason_code_list[0]}")
        else:
            logging.info(
                f"Broker granted the following QoS: {reason_code_list[0].value}"
            )

    def on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        connect_flags: mqtt.ConnectFlags,
        reason_code: ReasonCode,
        properties: Properties | None,
    ):
        if reason_code.is_failure:
            logging.error(
                f"Failed to connect: {reason_code}. loop_forever() will retry connection."
            )
        else:
            # we should always subscribe from on_connect callback to be sure
            # our subscribed is persisted across reconnections.
            logging.info("Connected.")
            client.subscribe(self.control_topic)
            client.subscribe(self.logged_topic)

    def run(self):
        mqttc = mqtt.Client(CallbackAPIVersion.VERSION2)
        mqttc.on_message = self.on_message
        mqttc.on_subscribe = self.on_subscribe
        mqttc.on_connect = self.on_connect
        if self.mqtt_ca_certs:
            mqttc.tls_set(ca_certs=self.mqtt_ca_certs, certfile=self.mqtt_certfile, keyfile=self.mqtt_keyfile, cert_reqs=ssl.CERT_REQUIRED)  # type: ignore
        mqttc.connect_async(self.mqtt_host, self.mqtt_port)
        mqttc.loop_forever()


@click.command()
@click.option("--mqtt_host", default="mqtt-broker")
@click.option("--mqtt_port", default=1883)
@click.option("--mqtt_ca_certs", default=None)
@click.option("--mqtt_certfile", default=None)
@click.option("--mqtt_keyfile", default=None)
@click.option("--mongodb_url", default="mongodb://root:example@mongo:27017/")
@click.option("--mongodb_database", default="stashbus")
def main_cli(
    mqtt_host: str,
    mqtt_port: int,
    mqtt_ca_certs: str | None,
    mqtt_certfile: str | None,
    mqtt_keyfile: str | None,
    mongodb_url: str,
    mongodb_database: str,
):
    subscriber = StashbusSub(
        mqtt_host,
        mqtt_port,
        mqtt_ca_certs,
        mqtt_certfile,
        mqtt_keyfile,
        mongodb_url,
        mongodb_database,
    )
    subscriber.run()
