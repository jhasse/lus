import subprocess
import sys
import os
from importlib.metadata import version as get_version

import click
from kdl.errors import ParseError
from termcolor import colored

from .LusFile import LusFile
from .completions import get_completion_script


@click.command(
    context_settings={
        "allow_extra_args": True,
        "allow_interspersed_args": False,
        "ignore_unknown_options": True,
    }
)
@click.option(
    "--version",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=lambda ctx, param, value: (
        click.echo(f"lus {get_version('lus')}") or ctx.exit()
    )
    if value
    else None,
    help="Show version",
)
@click.option(
    "--completions",
    is_eager=True,
    metavar="SHELL",
    help="Generate shell completions (bash, zsh, fish, powershell)",
)
@click.option(
    "-l",
    "--list",
    "list_subcommands",
    is_flag=True,
    is_eager=True,
    help="List available subcommands",
)
@click.argument("subcommand", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def main(ctx, completions, list_subcommands, subcommand):
    if completions is not None:
        try:
            click.echo(get_completion_script(completions))
        except ValueError as e:
            click.echo(f"error: {e}", err=True)
            ctx.exit(1)
        return

    args = (["-l"] if list_subcommands else []) + ctx.args + list(subcommand)

    try:
        invocation_directory = os.getcwd()
        MAX_DEPTH = 50
        current_filesystem = os.stat(".").st_dev
        for i in range(MAX_DEPTH):
            try:
                with open("lus.kdl", "r") as f:
                    content = f.read()
            except FileNotFoundError as e:
                if current_filesystem != os.stat("..").st_dev:
                    raise e
                cwd = os.getcwd()
                os.chdir("..")
                if cwd == os.getcwd():
                    raise e
            else:
                break

        LusFile(content, invocation_directory, args)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    except FileNotFoundError as e:
        click.echo(
            f"{colored('error:', 'red', attrs=['bold'])} {e.strerror}: {e.filename}",
            err=True,
        )
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
    except ParseError as e:
        click.echo(f"{colored('error:', 'red', attrs=['bold'])} lus.kdl:{e}", err=True)
        sys.exit(1)
