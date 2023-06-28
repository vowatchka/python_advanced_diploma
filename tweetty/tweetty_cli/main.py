"""Tweetty CLI."""

from typing import Annotated

import typer

from . import users

__version__ = "0.1.1"
__author__ = "Владимир Салтыков"
__email__ = "vowatchka@mail.ru"
__license__ = "MIT"

app = typer.Typer(invoke_without_command=True, no_args_is_help=True)
app.add_typer(users.users_app, name="users")


@app.callback()
def main(version: Annotated[bool, typer.Option(help="Show version", is_eager=True)] = False):
    if version:
        print(__version__)
        raise typer.Exit()


if __name__ == "__main__":
    app()
