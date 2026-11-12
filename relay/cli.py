"""Operator commands, run as `flask --app run <command>`:

    create-admin <username>    create an administrator (prompts for a password)
    seed-demo                  demo users, rooms and messages (empty database only)
"""

import click

from relay.errors import RelayError
from relay.models import User
from relay.services import auth, messages, rooms

DEMO_PASSWORD = "password123"
DEMO_USERS = ["alice", "bob", "carol", "dave"]


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

    @app.cli.command("seed-demo")
    def seed_demo():
        """Create the demo accounts, rooms and a short conversation history."""
        if User.query.count():
            click.echo("The database already has users; nothing was seeded.")
            return
        admin = auth.register("admin", "admin12345", role="admin")
        users = {name: auth.register(name, DEMO_PASSWORD) for name in DEMO_USERS}

        def say(user, room, text):
            messages.send(user.id, room.id, text)

        general = rooms.general_room()
        say(admin, general, "Welcome to Relay! This is the public chat, and everyone is here.")
        say(users["alice"], general, "Hi all!")
        say(users["bob"], general, "Hey Alice! The sprint review is at 4 pm.")

        team = rooms.create_group(users["alice"].id, "project-team", "public")
        for name in ("bob", "carol"):
            rooms.join_public(users[name].id, team.id)
        say(users["alice"], team, "Let's track the demo checklist here.")
        say(users["carol"], team, "I'll run the test plan after lunch.")

        lab = rooms.create_group(users["dave"].id, "secret-lab", "private")
        say(users["dave"], lab, "Private room: others join with the invite code.")

        dm, _ = rooms.open_direct(users["alice"].id, users["bob"].id)
        say(users["alice"], dm, "Can you review my PR before the meeting?")

        click.echo("Seeded demo data:")
        click.echo("  admin / admin12345 (administrator)")
        click.echo(f"  {', '.join(DEMO_USERS)} / {DEMO_PASSWORD}")
        click.echo("  rooms: #general, #project-team (public), "
                   f"#secret-lab (private, invite code {lab.invite_code}), DM alice <-> bob")
