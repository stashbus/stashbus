import click
from . import client as client_mod
from . import server as server_mod


@click.group()
def cli():
    pass


@cli.command()
def client():
    client_mod.main()


@cli.command()
def server():
    server_mod.main()
