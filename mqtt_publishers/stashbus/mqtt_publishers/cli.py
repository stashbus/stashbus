import click
from stashbus.db_models import Currency
from stashbus.http_common import (
    CryptoCompareClient,
    OWMClient,
    StashRESTClient,
    Mempool,
)
from stashbus.mqtt_publishers import RESTPublisher

BRNO_LAT_LON = 49.19522000, 16.60796000


@click.group()
@click.option("--stashrest_url")
@click.option("--producer_id")
@click.option("--mqtt_host", default="mqtt-broker")
@click.option("--mqtt_port", default=1883)
@click.option("--mqtt_ca_certs", default=None)
@click.option("--mqtt_certfile", default=None)
@click.option("--mqtt_keyfile", default=None)
@click.pass_context
def stashbus(
    ctx: click.Context,
    stashrest_url: str | None,
    producer_id: int | None,
    mqtt_host: str,
    mqtt_port: int,
    mqtt_ca_certs: str | None,
    mqtt_certfile: str | None,
    mqtt_keyfile: str | None,
):
    ctx.ensure_object(dict)
    ctx.obj["mqtt_host"] = mqtt_host
    ctx.obj["mqtt_port"] = mqtt_port
    ctx.obj["mqtt_ca_certs"] = mqtt_ca_certs
    ctx.obj["mqtt_certfile"] = mqtt_certfile
    ctx.obj["mqtt_keyfile"] = mqtt_keyfile
    ctx.obj["producer_id"] = producer_id
    ctx.obj["stashrest_url"] = stashrest_url


@stashbus.command()
@click.pass_context
def cryptocurrency(ctx: click.Context):
    stashrest_cli = StashRESTClient(ctx.obj["producer_id"], ctx.obj["stashrest_url"])

    RESTPublisher(
        ctx.obj["mqtt_host"],
        ctx.obj["mqtt_port"],
        ctx.obj["mqtt_ca_certs"],
        ctx.obj["mqtt_certfile"],
        ctx.obj["mqtt_keyfile"],
        "stashbus/prices/btc_usd",
        15.0,
        # CryptoCompareClient(Currency.BTC, Currency.USD, stashrest_cli.secret("coindesk-api-key")),
        Mempool(),
        stashrest_cli,
    ).run()


@stashbus.command()
@click.pass_context
def weather(ctx: click.Context):
    stashrest_cli = StashRESTClient(ctx.obj["producer_id"], ctx.obj["stashrest_url"])

    RESTPublisher(
        ctx.obj["mqtt_host"],
        ctx.obj["mqtt_port"],
        ctx.obj["mqtt_ca_certs"],
        ctx.obj["mqtt_certfile"],
        ctx.obj["mqtt_keyfile"],
        "stashbus/weather/brno",
        60,
        OWMClient(*BRNO_LAT_LON, stashrest_cli.secret("openweathermap-api-key")),
        stashrest_cli,
    ).run()
