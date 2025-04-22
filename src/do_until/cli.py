import importlib.metadata
import shlex
import time

import click
import subprocess
import dateparser
import datetime
from rich.progress import Progress, TimeRemainingColumn  # Added import


__version__ = importlib.metadata.version("do-until")


def run_cmd(cmd: tuple[str, ...], stop_at: datetime.datetime) -> None:
    pretty_cmd = shlex.join(cmd)
    try:
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
    except FileNotFoundError:
        click.secho(f'Command not found: "{pretty_cmd}"', fg="red")
        exit(1)

    total_time = (stop_at - datetime.datetime.now()).total_seconds()
    with Progress(
        "[progress.description]{task.description}",
        "[progress.percentage]{task.percentage:>03.0f}%",  # Padded with zeros
        TimeRemainingColumn(),
        transient=True,  # hide the progress line after it's done.
    ) as progress:
        task = progress.add_task(
            f'[green]Running: [bold]"{pretty_cmd}"', total=total_time
        )

        while datetime.datetime.now() < stop_at:
            if process.poll() is not None:  # Check if the process has already exited
                progress.stop()
                # click.secho("Process finished.", fg="yellow")
                break
            elapsed = (
                datetime.datetime.now()
                - (stop_at - datetime.timedelta(seconds=total_time))
            ).total_seconds()
            progress.update(task, completed=elapsed)
            time.sleep(0.5)  # Sleep briefly to avoid busy-waiting

        if datetime.datetime.now() >= stop_at:
            process.terminate()  # Terminate the process if the time is up
            progress.stop()
            click.secho(
                "Process terminated as the specified time was reached.", fg="yellow"
            )

    stdout, stderr = process.communicate()
    if stdout:
        print(stdout)
    if stderr:
        print(stderr)


# xfmt: off
CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
    "token_normalize_func": lambda x: x.lower(),
    # "ignore_unknown_options": True,
}


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("time", type=str)
@click.argument("command", nargs=-1, type=click.UNPROCESSED)
@click.version_option(__version__)
# fmt: on

def main(time: str, command: tuple[str, ...]) -> None:
    now = datetime.datetime.now()

    stop_at = dateparser.parse(time)
    if not stop_at:
        click.secho(f'Time is an invalid time specification, "{time}"', fg="red")
        exit(1)

    if stop_at < now:
        click.secho("Time is in the past, choose a future time.", fg="red")
        click.secho('Try using "in", for example "in 1h".', fg="red")
        exit()

    pretty_cmd = shlex.join(command)
    # click.echo(
    #     click.style("Stop at:", fg="green")
    #     + click.style(f" {stop_at}", fg="green", bold=True)
    # )

    run_cmd(command, stop_at)
