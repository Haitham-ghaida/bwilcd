"""Interactive session management"""

import click
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import FormattedText
from typing import Optional, Dict, List
from ..client import SodaClient
from .display import Display
from .commands import Commands


class Session:
    def __init__(self):
        self.client: Optional[SodaClient] = None
        self.current_stock: Optional[Dict] = None
        self.stocks: List[Dict] = []
        self.page_size = 20
        self.current_page = 0
        self.current_query = ""
        self.display = Display()
        self.commands = Commands()

    def start(self):
        """Start the interactive session"""
        while True:
            if self.client is None:
                self.display.show_nodes()
                commands = ["connect", "url", "quit", "help"] + [
                    str(i + 1) for i in range(len(self.display.nodes))
                ]
                command_completer = WordCompleter(commands)
            elif self.current_stock is None:
                self.display.show_stocks(self.stocks)
                commands = list(self.commands.shortcuts.keys()) + [
                    str(i + 1) for i in range(len(self.stocks))
                ]
                command_completer = WordCompleter(commands)
            else:
                self.display.show_dataset_commands()
                commands = list(self.commands.shortcuts.keys())
                command_completer = WordCompleter(commands)

            try:
                # Create a formatted prompt using prompt_toolkit's FormattedText
                prompt_message = FormattedText(
                    [
                        ("class:prompt", "bwilcd> "),
                    ]
                )

                cmd = prompt(
                    prompt_message,
                    completer=command_completer,
                    style=self.display.get_prompt_style(),
                ).strip()
            except (KeyboardInterrupt, EOFError):
                break

            if not cmd:
                continue

            parts = cmd.split(maxsplit=1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            # Convert shortcut to full command if it exists
            command = self.commands.shortcuts.get(command, command)

            if command == "quit":
                break
            elif command == "help":
                self.display.show_help(self.client, self.current_stock)
            else:
                try:
                    self.handle_command(command, args)
                except Exception as e:
                    click.echo(click.style(f"❌ Error: {str(e)}", fg="red", bold=True))

    def handle_command(self, command: str, args: str):
        """Handle a command"""
        if self.client is None:
            # Handle commands when not connected
            if command == "connect":
                try:
                    index = int(args) - 1
                    if 0 <= index < len(self.display.nodes):
                        node = self.display.nodes[index]
                        if self.connect_to_node(node["url"]):
                            self.display.clear_screen()
                            self.display.show_header()
                            self.display.show_stocks(self.stocks)
                    else:
                        click.echo(
                            click.style(
                                "❌ Invalid node number",
                                fg="red",
                                bold=True,
                            )
                        )
                except ValueError:
                    click.echo(
                        click.style(
                            "❌ Please provide a valid node number",
                            fg="red",
                            bold=True,
                        )
                    )
            elif command == "url":
                if args:
                    if self.connect_to_node(args):
                        self.display.clear_screen()
                        self.display.show_header()
                        self.display.show_stocks(self.stocks)
                else:
                    click.echo(
                        click.style(
                            "❌ Please provide a URL",
                            fg="red",
                            bold=True,
                        )
                    )
        elif self.current_stock is None:
            # Handle commands when connected but no stock selected
            if command == "select":
                try:
                    index = int(args) - 1
                    if 0 <= index < len(self.stocks):
                        self.current_stock = self.stocks[index]
                        self.current_page = 0
                        self.current_query = ""
                        self.display.clear_screen()
                        self.display.show_header()
                        click.echo(
                            click.style(
                                f"\n📂 Selected Stock: {self.current_stock['name']}",
                                fg="cyan",
                                bold=True,
                            )
                        )
                        click.echo("\n⟳ Fetching datasets...")
                        self.display.show_datasets(
                            self.client,
                            self.current_stock,
                            self.current_page,
                            self.page_size,
                            self.current_query,
                        )
                    else:
                        click.echo(
                            click.style(
                                "❌ Invalid stock number",
                                fg="red",
                                bold=True,
                            )
                        )
                except ValueError:
                    click.echo(
                        click.style(
                            "❌ Please provide a valid stock number",
                            fg="red",
                            bold=True,
                        )
                    )
            elif command == "back":
                self.client = None
                self.stocks = []
                self.display.clear_screen()
                self.display.show_header()
                self.display.show_nodes()
            elif command == "refresh":
                try:
                    self.stocks = self.client.get_stocks()
                    self.display.clear_screen()
                    self.display.show_header()
                    self.display.show_stocks(self.stocks)
                except Exception as e:
                    click.echo(
                        click.style(
                            f"❌ Failed to refresh stocks: {str(e)}",
                            fg="red",
                            bold=True,
                        )
                    )
        else:
            # Handle dataset-related commands
            if command == "back":
                self.current_stock = None
                self.current_page = 0
                self.current_query = ""
                self.display.clear_screen()
                self.display.show_header()
                self.display.show_stocks(self.stocks)
            else:
                self.handle_dataset_command(command, args)

    def connect_to_node(self, url: str):
        """Connect to a SODA node"""
        try:
            # Ask for authentication
            use_auth = click.prompt(
                click.style("Use authentication?", fg="green"),
                type=bool,
                default=False,
                show_default=True,
            )

            username = None
            password = None
            if use_auth:
                username = click.prompt("Username", type=str)
                password = click.prompt("Password", type=str, hide_input=True)

            click.echo("\n⟳ Connecting to server...")

            # Create client and test connection
            self.client = SodaClient(url, username, password)
            if not self.client.test_connection():
                click.echo(
                    click.style("❌ Failed to connect to server", fg="red", bold=True)
                )
                self.client = None
                return False

            # Get available stocks
            self.stocks = self.client.get_stocks()
            if not self.stocks:
                click.echo(
                    click.style(
                        "❌ No data stocks found on server",
                        fg="red",
                        bold=True,
                    )
                )
                self.client = None
                return False

            return True

        except Exception as e:
            click.echo(
                click.style(
                    f"❌ Failed to connect: {str(e)}",
                    fg="red",
                    bold=True,
                )
            )
            self.client = None
            return False

    def get_url_from_command(self, command: str, args: str) -> Optional[str]:
        """Get URL from command arguments"""
        if command == "connect":
            try:
                node_num = int(args) - 1
                if not (0 <= node_num < len(self.display.nodes)):
                    raise ValueError()
                return self.display.nodes[node_num]["url"]
            except ValueError:
                click.echo(click.style("❌ Error: Invalid node number", fg="red"))
                return None
        else:
            url = args
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            return url

    def handle_back(self):
        """Handle the back command"""
        if self.current_stock is not None:
            self.current_stock = None
            self.current_query = ""
            self.display.clear_screen()
            self.display.show_header()
        elif self.client is not None:
            self.client = None
            self.stocks = []
            self.display.clear_screen()
            self.display.show_header()

    def refresh_stocks(self):
        """Refresh the list of stocks"""
        try:
            self.stocks = self.client.get_stocks()
            click.echo(click.style("✓ Stocks refreshed successfully", fg="green"))
        except Exception as e:
            click.echo(click.style(f"❌ Error refreshing stocks: {str(e)}", fg="red"))

    def select_stock(self, args: str):
        """Select a stock by number"""
        if not args:
            click.echo(click.style("❌ Error: Please provide a stock number", fg="red"))
            return

        try:
            stock_num = int(args) - 1
            if not (0 <= stock_num < len(self.stocks)):
                raise ValueError()
            self.current_stock = self.stocks[stock_num]
            self.current_page = 0
            self.current_query = ""
            self.display.clear_screen()
            self.display.show_header()
            click.echo(
                click.style(
                    f"\n📂 Selected Stock: {self.current_stock['name']}",
                    fg="cyan",
                    bold=True,
                )
            )
            self.display.show_datasets(
                self.client, self.current_stock, self.current_page, self.page_size
            )
        except ValueError:
            click.echo(click.style("❌ Error: Invalid stock number", fg="red"))

    def handle_dataset_command(self, command: str, args: str):
        """Handle dataset-related commands"""
        if command == "search":
            self.current_query = args
            self.current_page = 0
            self.display.clear_screen()
            self.display.show_header()
            click.echo(
                click.style(
                    f"\n📂 Current Stock: {self.current_stock['name']}",
                    fg="cyan",
                    bold=True,
                )
            )
            self.display.show_datasets(
                self.client,
                self.current_stock,
                self.current_page,
                self.page_size,
                self.current_query,
            )
        elif command == "ll":
            self.current_query = ""
            self.current_page = 0
            self.display.clear_screen()
            self.display.show_header()
            click.echo(
                click.style(
                    f"\n📂 Current Stock: {self.current_stock['name']}",
                    fg="cyan",
                    bold=True,
                )
            )
            self.display.show_datasets(
                self.client,
                self.current_stock,
                self.current_page,
                self.page_size,
                self.current_query,
            )
        elif command == "next":
            self.current_page += 1
            datasets = self.display.show_datasets(
                self.client,
                self.current_stock,
                self.current_page,
                self.page_size,
                self.current_query,
            )
            if not datasets:
                self.current_page -= 1
                click.echo(click.style("\n⚠️  No more datasets", fg="yellow", bold=True))
        elif command == "prev":
            if self.current_page > 0:
                self.current_page -= 1
                self.display.show_datasets(
                    self.client,
                    self.current_stock,
                    self.current_page,
                    self.page_size,
                    self.current_query,
                )
            else:
                click.echo(
                    click.style("\n⚠️  Already at first page", fg="yellow", bold=True)
                )