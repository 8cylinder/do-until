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
    "ignore_unknown_options": True,
}


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("time", type=str)
@click.argument("command", nargs=-1, type=click.UNPROCESSED, required=True)
@click.version_option(__version__)
def main(time: str, command: tuple[str, ...]) -> None:
    """Run a command until a specified time.

    \b
    TIME is a time specification, e.g,
      "in 1h",
      "5s",
      "tomorrow 10:00",
      "2023-10-01 12:00"

    COMMAND is the command to run, e.g. "echo hello world".

    If the COMMAND uses an "-h", "--help" or "--version" option, that will trigger the
    help for this command.  To prevent that use a double dash between the TIME and
    the COMMAND,
    e.g,

    \b
    do-until "in 1h" -- echo hello world -h
    """  # noqa: D301
    now = datetime.datetime.now(TZ)

    dateparser_settings = {
        "PREFER_DATES_FROM": "future",
        "TIMEZONE": "UTC",
        "TO_TIMEZONE": "UTC",
        "RETURN_AS_TIMEZONE_AWARE": True,
    }
    stop_at = dateparser.parse(time, settings=dateparser_settings)  # type: ignore
    if not stop_at:
        click.secho(f'Time is an invalid time specification, "{time}"', fg="red")
        sys.exit(1)

    if stop_at < now:
        click.secho("Time is in the past, choose a future time.", fg="red")
        click.secho('Try using "in", for example "in 1h".', fg="red")
        sys.exit()

    try:
        run_cmd(command, stop_at)
    except KeyboardInterrupt:  # suppress the "Aborted!" message
        sys.exit(0)
