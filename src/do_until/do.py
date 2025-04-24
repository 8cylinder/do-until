"""do-until, a CLI tool to run a command until a specified time."""

import datetime
import selectors
import shlex
import subprocess
import sys
import time
from typing import Any

import click
from rich.console import Console
from rich.progress import Progress

TZ: datetime.tzinfo = datetime.UTC
console = Console(highlight=False)


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
    with Progress(transient=True, console=console) as progress:
        update_progress(process, progress, stop_at, total_time, pretty_cmd)


def update_progress(
    process: subprocess.Popen[str],
    progress: Progress,
    stop_at: datetime.datetime,
    total_time: float,
    pretty_cmd: str,
) -> None:
    """Update the progress bar until the specified time."""
    task = progress.add_task(
        f"[green]▶ {pretty_cmd}",
        total=total_time,
    )
    pp: Any = progress.console.print

    selector = selectors.DefaultSelector()
    # Register process.stdout and process.stderr with the selector
    if process.stdout:
        selector.register(process.stdout, selectors.EVENT_READ)
    if process.stderr:
        selector.register(process.stderr, selectors.EVENT_READ)

    now = datetime.datetime.now(TZ)
    while now < stop_at:
        if process.poll() is not None:  # Check if the process has already exited
            progress.stop()
            break

        # Check command output
        for key, _ in selector.select(timeout=0.1):
            line = key.fileobj.readline()
            if line:
                if key.fileobj is process.stdout:
                    pp(line.strip())  # Print stdout in green
                elif key.fileobj is process.stderr:
                    pp(f"[red]{line.strip()}")  # Print stderr in red

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
