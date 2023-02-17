#!/usr/bin/env python
import click
import requests
import pprint
import os
import toml
from functools import wraps

# TODO (T2600): Potentially support active context (i.e. checkout a project) to avoid having to specify ids each time.

VERIFY = True
SBX_API_URL_BASE = "https://app.sbxrobotics.com"
if os.getenv('SBX_DEV'):
    print("Running SBX CLI in dev mode. No SSL verification will be used. `export SBX_DEV=` to test for prod")
    VERIFY = False
    SBX_API_URL_BASE = "https://dev.app.sbxrobotics.com"

CONFIG_DIR = os.path.expanduser('~/.config/sbx/')
CONFIG_PATH = os.path.join(CONFIG_DIR, 'config.toml')

#
# Utility functions
#


def sbx_style(msg):
    """wrapper around styling informative sbx messages

    Parameters
    ----------
    msg : str
        message to style
    """
    return click.style("sbx", fg="cyan") + ": " + msg


def validate_key_format(hex):
    """validate that an api key is well formatted.
    It must be a 40 character long hexadecimal string.
    """
    if len(hex) != 40:
        return False
    try:
        int(hex, 16)
        return True
    except:
        return False


def login_required(f):
    """enforces that we have a ~/.config/sbx/config.toml and loads it, then passes it
    to the decorated function as the first parameter. This serves as an easy way to load
    stored cli state.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        config = None
        if 'key' in kwargs.keys():
            # we supply a kwarg "key" when we are setting up our api key during sbx login.
            return f({}, *args, **kwargs)
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r') as file:
                config = toml.load(file)
        else:
            click.echo(
                sbx_style(f"It looks like you're not logged in. Please `sbx login` first."))
            return
        f(config, *args, **kwargs)
    return wrapper


@login_required
def sbx_post(cfg, route, key=None):
    """post to a route and return a parsed json response

    Parameters
    ----------
    route : str
        Something like `/user/validate-api-key`
    cfg : dict
        loaded from login_required decorator, config dict
    key : str
        api key that overrides the one in the cfg (useful for validating api key for the first time before storing it)

    Returns
    -------
    dict
        parsed json object returned from post request
    """
    if not key:
        key = cfg['api']['key']
    try:
        response = requests.post(SBX_API_URL_BASE + "/app-api/v0" + route, headers={
                                 "Authorization": key, "AuthType": "API_KEY"}, verify=VERIFY)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            click.echo(sbx_style(
                f"API key is invalid. Please enter a key currently listed at {SBX_API_URL_BASE}/settings/account"))
        elif response.status_code == 500:
            click.echo(sbx_style(
                f"Server Error: There was an internal server error. Please retry in a bit."))
        else:
            print(e)
        return None


@click.group()
def cli():
    """Entrypoint"""
    pass


@cli.group()
def project():
    """list generator related commands"""
    pass


@cli.group()
def generator():
    """list generator related commands"""
    pass


@cli.group()
def dataset():
    """list dataset related commands"""
    pass


@cli.group()
def job():
    """list aws job related commands"""
    pass

#
# Top level Commands
#


@cli.command()
def login():
    """log into SBX, getting user and company info"""
    click.echo(sbx_style(
        f'Welcome to SBX! Please find your API key(s) at {SBX_API_URL_BASE}/settings/account'))
    key = click.prompt(sbx_style(
        'Paste the API key from your profile and hit enter, or press ctrl+c to quit'))
    if not validate_key_format(key):
        click.echo(sbx_style("Please enter a well-formed API key"))
        return
    res = sbx_post("/user/validate-api-key", key=key)
    if res:
        config = {
            'api': {
                'key': key
            },
            'user': res['user'],
            'company': res['company']
        }
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            toml.dump(config, f)

        click.echo(sbx_style(
            "API key has been validated and stored at ~/.config/sbx/config.toml. You're good to go!"))


@cli.command()
@login_required
def account(cfg):
    """show information about current login"""
    click.echo(sbx_style(
        "You're currently logged in with the following account information:\n"))
    click.echo(click.style("Email", fg="cyan") + ": " + cfg['user']['email'])
    click.echo(click.style("Name", fg="cyan") + ": " + cfg['user']['name'])
    click.echo(click.style("Organization", fg="cyan") +
               ": " + cfg['company']['name'])
    click.echo("")

#
# Project commands
#


@project.command()
def list():
    """list user projects"""

    raise NotImplementedError


@project.command()
def info():
    """show detailed info about a project"""
    raise NotImplementedError


#
# Generator commands
#


@generator.command()
def info():
    """show detailed info about a particular generator"""
    raise NotImplementedError


@generator.command()
def list():
    """list all generators attached to a project"""
    raise NotImplementedError

#
# Dataset commands
#


@dataset.command()
def list():
    """list all datasets belonging to a project"""
    raise NotImplementedError


@dataset.command()
def download():
    """download a dataset locally to a specified location"""
    raise NotImplementedError

#
# Job commands
#


@job.command()
def list():
    """list current running and completed aws jobs"""
    raise NotImplementedError
