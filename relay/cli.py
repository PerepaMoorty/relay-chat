"""Operator commands, run as `flask --app run <command>`:

    create-admin <username>    create an administrator (prompts for a password)

B6 adds `seed-demo`.
"""

import click

from relay.errors import RelayError
from relay.services import auth


def register_cli(app):
    @app.cli.command("create-admin")
    @click.argument("username")
    @click.password_option()
    def create_admin(username, password):
        """Create an administrator account."""
        try:
            user = auth.register(username, password, role="admin")
        except RelayError as err:
            raise click.ClickException(err.message) from None
        click.echo(f"Created admin '{user.username}'")
