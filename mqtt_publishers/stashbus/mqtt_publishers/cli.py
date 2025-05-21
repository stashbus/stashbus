import click
from stashbus.db_models import Currency
from stashbus.mqtt_publishers.cryptocompare_mqtt_publisher import CryptoComparePublisher
from stashbus.mqtt_publishers.openweathermap_mqtt_publisher import (
    OWMPublisher,
    BRNO_LAT_LON,
)
from stashbus.mqtt_publishers import get_key


@click.group()
@click.option("--mqtt_host", default="mqtt-broker")
@click.option("--mqtt_port", default=1883)
@click.option("--mqtt_ca_certs", default=None)
@click.option("--mqtt_certfile", default=None)
@click.option("--mqtt_keyfile", default=None)
@click.option("--stashrest_url", default=None)
@click.pass_context
def stashbus(
    ctx: click.Context,
    mqtt_host: str,
    mqtt_port: int,
    mqtt_ca_certs: str | None,
    mqtt_certfile: str | None,
    mqtt_keyfile: str | None,
    stashrest_url: str | None,
):
    ctx.ensure_object(dict)
    ctx.obj["mqtt_host"] = mqtt_host
    ctx.obj["mqtt_port"] = mqtt_port
    ctx.obj["mqtt_ca_certs"] = mqtt_ca_certs
    ctx.obj["mqtt_certfile"] = mqtt_certfile
    ctx.obj["mqtt_keyfile"] = mqtt_keyfile
    ctx.obj["stashrest_url"] = stashrest_url


@stashbus.command()
@click.pass_context
def cryptocurrency(ctx: click.Context):
    CryptoComparePublisher(
        ctx.obj["mqtt_host"],
        ctx.obj["mqtt_port"],
        ctx.obj["mqtt_ca_certs"],
        ctx.obj["mqtt_certfile"],
        ctx.obj["mqtt_keyfile"],
        "stashbus/prices/btc_usd",
        5.0,
        ctx.obj["stashrest_url"],
        Currency.BTC,
        Currency.USD,
        get_key("coindesk-api-key"),
    ).run()


@stashbus.command()
@click.pass_context
def weather(ctx: click.Context):
    OWMPublisher(
        ctx.obj["mqtt_host"],
        ctx.obj["mqtt_port"],
        ctx.obj["mqtt_ca_certs"],
        ctx.obj["mqtt_certfile"],
        ctx.obj["mqtt_keyfile"],
        "stashbus/weather/brno",
        60,
        ctx.obj["stashrest_url"],
        *BRNO_LAT_LON,
        get_key("openweathermap-api-key"),
    ).run()
