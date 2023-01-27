#!/usr/bin/env python
import click
from click.exceptions import ClickException

@click.group()
def cli():
    pass

@cli.command()
def hello():
    click.echo('Hello Rick Deckard.')