"""do-until, a CLI tool to run a command until a specified time."""

import datetime
import shlex
import subprocess
import sys
import time

import click
from rich.progress import Progress  # Added import

TZ: datetime.tzinfo = datetime.UTC


def run_cmd(
    cmd: tuple[str, ...],
    stop_at: datetime.datetime,
) -> None:
    """Run a command until a specified time."""
    pretty_cmd = shlex.join(cmd)
    split_cmd = shlex.split(pretty_cmd)
    try:
        process = get_process(split_cmd)
    except FileNotFoundError:
        click.secho(f'Command not found: "{pretty_cmd}"', fg="red")
        sys.exit(1)

    total_time = (stop_at.astimezone(TZ) - datetime.datetime.now(TZ)).total_seconds()
    with Progress(
        transient=True,  # hide the progress line after it's done.
    ) as progress:
        update_progress(process, progress, stop_at, total_time, pretty_cmd)

    stdout, stderr = process.communicate()
    if stdout:
        click.echo(stdout)
    if stderr:
        click.echo(stderr)


def update_progress(
    process: subprocess.Popen[str],
    progress: Progress,
    stop_at: datetime.datetime,
    total_time: float,
    pretty_cmd: str,
) -> None:
    """Update the progress bar until the specified time."""
    task = progress.add_task(
        f'[green]Running: [bold]"{pretty_cmd}"',
        total=total_time,
    )
    now = datetime.datetime.now(TZ)
    while now < stop_at:
        if process.poll() is not None:  # Check if the process has already exited
            progress.stop()
            break
        elapsed = (
            now - (stop_at - datetime.timedelta(seconds=total_time))
        ).total_seconds()
        progress.update(task, completed=elapsed)
        time.sleep(0.5)  # Sleep briefly to avoid busy-waiting
        now = datetime.datetime.now(TZ)

    process.terminate()  # Terminate the process if the time is up
    progress.stop()
    click.secho(
        "Process terminated as the specified time was reached.",
        fg="yellow",
    )


def get_process(split_cmd: list[str]) -> subprocess.Popen[str]:
    """Get the process for the given command."""
    return subprocess.Popen(
        split_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        text=True,
    )
