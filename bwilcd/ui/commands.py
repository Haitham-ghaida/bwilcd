import click
from prompt_toolkit import prompt, HTML
from typing import Optional, Dict
from ..client import SodaClient


class Commands:
    def __init__(self):
        self.shortcuts = {
            "q": "quit",
            "h": "help",
            "s": "search",
            "sl": "select",
            "n": "next",
            "p": "prev",
            "b": "back",
            "r": "refresh",
            "d": "dd",
            "c": "connect",
        }

    def connect_to_node(self, url: str) -> Optional[SodaClient]:
        """Connect to a ILCD node with optional authentication"""
        while True:
            use_auth = (
                prompt(click.style("Use authentication? (y/N): ", fg="green"))
                .lower()
                .strip()
            )
            if use_auth == "y":
                username = prompt(click.style("Username: ", fg="green"))
                password = prompt(
                    click.style("Password: ", fg="green"), is_password=True
                )
                client = SodaClient(url, username, password)
            else:
                client = SodaClient(url)

            click.echo("\n" + click.style("⟳ Connecting to server...", fg="cyan"))
            if client.test_connection():
                click.echo(
                    click.style("✓ Connected successfully!", fg="green", bold=True)
                )
                return client
            else:
                click.echo(
                    click.style("❌ Failed to connect to server", fg="red", bold=True)
                )
                retry = (
                    prompt(click.style("Retry? (Y/n): ", fg="green")).lower().strip()
                )
                if retry == "n":
                    return None
