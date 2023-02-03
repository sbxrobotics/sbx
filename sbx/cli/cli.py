#!/usr/bin/env python
import click
import requests
import pprint
import os
import toml

VERIFY = True
SBX_API_URL_BASE = "https://app.sbxrobotics.com"
if os.getenv('SBX_DEV'):
    print("Running SBX CLI in dev mode. No SSL verification will be used. `export SBX_DEV=` to test for prod")
    VERIFY = False
    SBX_API_URL_BASE = "https://dev.app.sbxrobotics.com"

CONFIG_DIR = os.path.expanduser('~/.config/sbx/')
CONFIG_PATH = os.path.join(CONFIG_DIR, 'config.toml')

def sbx_style(msg):
    """wrapper around styling informative sbx messages

    Parameters
    ----------
    msg : str
        message to style
    """
    return click.style("sbx", fg="cyan")  + ": " + msg

def validate_api_key(key):
    try:
        response = requests.post(SBX_API_URL_BASE + "/app-api/v0/user/validate-api-key", json = {'key': key}, verify=VERIFY)
        response.raise_for_status()
        return True
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            click.echo(sbx_style(f"API key is invalid. Please enter a key currently listed at {SBX_API_URL_BASE}/settings/account"))
        elif response.status_code == 500:
            click.echo(sbx_style(f"Server Error: There was an internal server error. Please retry in a bit."))
        else:
            print(e)
        return False

def get_api_key():
    api_key = None
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            config = toml.load(f)
            api_key = config['api']['key']
    if not api_key:
        click.echo(sbx_style('You are not logged in. Please use `sbx login`'))
    return api_key

@click.group()
def cli():
    pass

@cli.command()
def hello():
    click.echo('Hello Rick Deckard.')

@cli.command()
def login():
    click.echo(sbx_style(f'Welcome to SBX! Please find your API key(s) at {SBX_API_URL_BASE}/settings/account'))
    key = click.prompt(sbx_style('Paste the API key from your profile and hit enter, or press ctrl+c to quit'))
    if validate_api_key(key):
        config = {
            'api': {
                'key': key
            }
        }
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            toml.dump(config, f)

        click.echo(sbx_style("API key has been validated and stored at ~/.config/sbx/config.toml. You're good to go!"))
 
@cli.command()
def show_info():
    api_key = get_api_key()
    if not api_key:
        return
    try:
        response = requests.post(SBX_API_URL_BASE + "/app-api/v0/user/get-info-by-key", headers = {"Authorization": api_key, "AuthType": "API_KEY"}, verify=VERIFY)
        pprint.pprint(response.json())
    except requests.exceptions.HTTPError as e:
        print(e)

