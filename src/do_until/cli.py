"""do-until - CLI for running commands until a specified time."""

import datetime
import importlib.metadata
import sys

import click
import dateparser

from .do import TZ, run_cmd

__version__ = importlib.metadata.version("do-until")

CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
    "token_normalize_func": lambda x: x.lower(),
    # "ignore_unknown_options": True,
}


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("time", type=str)
@click.argument("command", nargs=-1, type=click.UNPROCESSED)
@click.version_option(__version__)
def main(time: str, command: tuple[str, ...]) -> None:
    """Run a command until a specified time."""
    now = datetime.datetime.now(TZ)

    if "UTC" not in time:
        time = time + " UTC"
    stop_at = dateparser.parse(time)
    if not stop_at:
        click.secho(f'Time is an invalid time specification, "{time}"', fg="red")
        sys.exit(1)

    if stop_at < now:
        click.secho("Time is in the past, choose a future time.", fg="red")
        click.secho('Try using "in", for example "in 1h".', fg="red")
        sys.exit()

    run_cmd(command, stop_at)
