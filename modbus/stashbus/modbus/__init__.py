import click
from stashbus.modbus.client import main as cli_main
from stashbus.modbus.server import main as srv_main


@click.group()
def cli():
    pass


@cli.command()
def client():
    cli_main()


@cli.command()
def server():
    srv_main()
