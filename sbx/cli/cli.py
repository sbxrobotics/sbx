#!/usr/bin/env python
import click
from click.exceptions import ClickException

@click.command()
def hello():
    click.echo('Hello Rick Deckard.')