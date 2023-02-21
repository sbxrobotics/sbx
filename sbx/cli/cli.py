
#!/usr/bin/env python
import os
from enum import Enum
from functools import wraps

import click
import requests
import toml
from bson import ObjectId
from bson.errors import InvalidId
from tabulate import tabulate

# TODO (T2600): Potentially support active context (i.e. checkout a project) to avoid having to specify ids each time.

VERIFY = True
SBX_API_URL_BASE = "https://app.sbxrobotics.com"
if os.getenv('SBX_DEV'):
    print("Running SBX CLI in dev mode. No SSL verification will be used. `export SBX_DEV=` to test for prod")
    VERIFY = False
    SBX_API_URL_BASE = "https://dev.app.sbxrobotics.com"

CONFIG_DIR = os.path.expanduser('~/.config/sbx/')
CONFIG_PATH = os.path.join(CONFIG_DIR, 'config.toml')


class JobState(Enum):
    # maintain correspondence between these codes and DatasetJobState in the api.
    INIT = 1
    GEN = 10
    MERGE = 20
    COCO = 30
    SHIP = 40
    ERROR = 1000

    @classmethod
    def get_name(cls, val):
        return cls(val).name


class SortOrder(Enum):
    ASC = 10
    DESC = 20

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

def check_object_id(value):
    try:
        _ = ObjectId(value)
    except InvalidId:
        click.echo(sbx_style("Ooops, malformed id"))
        exit()


def check_dataset_job_id(value):
    try:
        split = value.split('-')
        assert len(split) > 2
        _ = ObjectId(value.split('-')[-1])
    except (InvalidId, AssertionError):
        click.echo(sbx_style("Ooops, malformed dataset job id. make sure to enter an id from `sbx job list`"))
        exit()


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
        return f(config, *args, **kwargs)
    return wrapper


@login_required
def sbx_post(cfg, route, key=None, json=None):
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
                                 "Authorization": key, "AuthType": "API_KEY"}, json=json, verify=VERIFY)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            click.echo(sbx_style(response.text))
            click.echo(sbx_style(
                f"Are you using an valid API key for the resource you are trying to access? Please enter a key currently listed at {SBX_API_URL_BASE}/settings/account"))
        elif response.status_code == 400:
            click.echo(sbx_style(response.json()['message']))
        elif response.status_code == 500:
            click.echo(sbx_style("Internal Server Error: Please retry in a bit."))
        else:
            click.echo(sbx_style(str(e)))
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
    res = sbx_post("/projects/get", json={"sort": SortOrder.DESC.value})
    if not res:
        return
    headers = ['Id', 'Date Created', 'Name']
    rows = [(
        proj['project_id'],
        proj['created_str_utc'],
        proj['name']
    ) for proj in res['projects']]
    print(tabulate(rows, headers=headers, tablefmt="grid"))


@project.command()
@click.argument("project_id")
def info(project_id):
    """show detailed info about a project"""
    check_object_id(project_id)
    res = sbx_post("/project/get", json={"id": project_id})
    if not res:
        return
    print(tabulate([(k, v) for k, v in res.items()], tablefmt="grid"))


#
# Generator commands
#

@generator.command()
@click.argument("project_id")
def list(project_id):
    """list all generators attached to a project
    """
    check_object_id(project_id)
    res = sbx_post("/generators/get",
                   json={"project_id": project_id, "sort": SortOrder.DESC.value})
    if not res:
        return
    headers = ['Id', 'Name', 'Build Name']
    rows = [(
        gen['id'],
        gen['name'],
        gen['cur_build_name']
    ) for gen in res['generators']]
    print(tabulate(rows, headers=headers, tablefmt="grid"))


@generator.command()
@click.argument("generator_id")
def info(generator_id):
    """show detailed info about a particular generator
    """
    check_object_id(generator_id)
    res = sbx_post("/generator/get", json={"id": generator_id})
    if not res:
        return
    print(tabulate([(k, v) for k, v in res.items()], tablefmt="grid"))

#
# Dataset commands
#


@dataset.command()
@click.argument("project_id")
def list(project_id):
    """list all datasets belonging to a project
    """
    check_object_id(project_id)
    res = sbx_post("/datasets/get",
                   json={"project_id": project_id, "sort": SortOrder.DESC.value})
    if not res:
        return
    headers = ['Id', 'Date Shipped', 'Name']
    rows = [(
        ds['id'],
        ds['created_str_utc'],
        ds['name']
    ) for ds in res['datasets']]
    print(tabulate(rows, headers=headers, tablefmt="grid"))


@dataset.command()
@click.argument("dataset_id")
def info(dataset_id):
    """show detailed info about a project
    Note: dataset_id refers to the id shown in the dataset list command,
    not the sbx internal id.
    """
    check_object_id(dataset_id)
    res = sbx_post("/dataset/get", json={"id": dataset_id})
    if not res:
        return
    print(tabulate([(k, v)
          for k, v in res['dataset'].items()], tablefmt="grid"))


@dataset.command()
def download():
    """download a dataset locally to a specified location"""
    raise NotImplementedError

#
# Job commands
#


@job.command()
@click.argument("project_id", default=None, required=False)
def list(project_id):
    """list current running and completed aws jobs
    """
    check_object_id(project_id)
    query = {"sort": SortOrder.DESC.value}
    if project_id:
        query['project_id'] = project_id
    res = sbx_post("/dataset-jobs/get",
                   json=query)
    if not res:
        return
    headers = ['Id', 'Created', 'Finished', 'Name', 'State']
    rows = [(
        ds['id'],
        ds['created_utc'],
        ds['finished_utc'],
        ds['name'],
        JobState.get_name(int(ds['state']))
    ) for ds in res['dataset_jobs']]
    print(tabulate(rows, headers=headers, tablefmt="grid"))


@job.command()
@click.argument("job_id")
def info(job_id):
    """list current running and completed aws jobs
    """
    check_dataset_job_id(job_id)
    res = sbx_post("/dataset-job/get", json={"id": job_id})
    if not res:
        return
    print(tabulate([(k, v)
          for k, v in res['dataset_job'].items()], tablefmt="grid"))
