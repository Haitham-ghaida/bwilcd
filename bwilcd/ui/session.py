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
        # Show initial help
        self.display.show_nodes(show_commands=True)

        while True:
            if self.client is None:
                commands = ["quit", "help", "url"] + [
                    str(i + 1) for i in range(len(self.display.nodes))
                ]
                command_completer = WordCompleter(commands)
            elif self.current_stock is None:
                commands = ["quit", "help", "back", "refresh", "download"] + [
                    str(i + 1) for i in range(len(self.stocks))
                ]
                command_completer = WordCompleter(commands)
            else:
                commands = [
                    "quit",
                    "help",
                    "back",
                    "next",
                    "prev",
                    "search",
                    "list",
                ] + [str(i + 1) for i in range(20)]
                command_completer = WordCompleter(commands)

            try:
                prompt_message = FormattedText(
                    [
                        ("class:prompt", "bwilcd> "),
                    ]
                )

                cmd = (
                    prompt(
                        prompt_message,
                        completer=command_completer,
                        style=self.display.get_prompt_style(),
                    )
                    .strip()
                    .lower()
                )
            except (KeyboardInterrupt, EOFError):
                break

            if not cmd:
                continue

            if cmd.isdigit():
                number = int(cmd)
                try:
                    if self.client is None:
                        if 0 < number <= len(self.display.nodes):
                            node = self.display.nodes[number - 1]
                            if self.connect_to_node(node["url"]):
                                self.display.clear_screen()
                                self.display.show_header()
                                self.display.show_stocks(
                                    self.stocks, show_commands=True
                                )
                        else:
                            click.echo(
                                click.style(
                                    "❌ Invalid node number", fg="red", bold=True
                                )
                            )
                    elif self.current_stock is None:
                        if 0 < number <= len(self.stocks):
                            self.current_stock = self.stocks[number - 1]
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
                                self.client,
                                self.current_stock,
                                self.current_page,
                                self.page_size,
                                self.current_query,
                                show_commands=True,
                            )
                        else:
                            click.echo(
                                click.style(
                                    "❌ Invalid stock number", fg="red", bold=True
                                )
                            )
                    else:
                        datasets = self.client.search_datasets(
                            self.current_stock["uuid"],
                            query=self.current_query,
                            page=self.current_page,
                            size=self.page_size,
                        )
                        # Calculate the actual index based on the page number
                        actual_number = number - (self.current_page * self.page_size)
                        if 0 < actual_number <= len(datasets):
                            dataset_uuid = datasets[actual_number - 1]["uuid"]
                            click.echo(
                                click.style(
                                    "\n⟳ Fetching dataset details...", fg="cyan"
                                )
                            )
                            dataset_info = self.client.get_dataset(dataset_uuid)
                            self.display.show_dataset_info(dataset_info)

                            # Wait for user input before returning to dataset list
                            click.prompt(
                                "\nPress Enter to return to dataset list",
                                default="",
                                show_default=False,
                            )

                            # Refresh dataset list display
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
                                show_commands=True,
                            )
                        else:
                            click.echo(
                                click.style(
                                    "❌ Invalid dataset number", fg="red", bold=True
                                )
                            )
                except Exception as e:
                    click.echo(click.style(f"❌ Error: {str(e)}", fg="red", bold=True))
                continue

            parts = cmd.split(maxsplit=1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            if command == "quit":
                break
            elif command == "help":
                if self.client is None:
                    self.display.clear_screen()
                    self.display.show_header()
                    self.display.show_nodes(show_commands=True)
                elif self.current_stock is None:
                    self.display.clear_screen()
                    self.display.show_header()
                    self.display.show_stocks(self.stocks, show_commands=True)
                else:
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
                        show_commands=True,
                    )
            elif command == "back":
                if self.current_stock is not None:
                    self.current_stock = None
                    self.current_page = 0
                    self.current_query = ""
                    self.display.clear_screen()
                    self.display.show_header()
                    self.display.show_stocks(self.stocks, show_commands=True)
                elif self.client is not None:
                    self.client = None
                    self.stocks = []
                    self.display.clear_screen()
                    self.display.show_header()
                    self.display.show_nodes(show_commands=True)
            elif command == "download" and self.current_stock is None and args:
                try:
                    stock_number = int(args)
                    if 0 < stock_number <= len(self.stocks):
                        stock = self.stocks[stock_number - 1]
                        click.echo(
                            click.style(
                                f"\n⬇️  Downloading stock: {stock['name']}...", fg="cyan"
                            )
                        )

                        def progress_callback(current: int, total: int):
                            if total > 0:
                                percentage = (current / total) * 100
                                click.echo(f"\rProgress: {percentage:.1f}%", nl=False)

                        download_path = self.client.download_stock(
                            stock["uuid"], progress_callback
                        )
                        click.echo("\n✅ Download complete!")
                        click.echo(
                            click.style(f"📁 Saved to: {download_path}", fg="green")
                        )
                    else:
                        click.echo(
                            click.style("❌ Invalid stock number", fg="red", bold=True)
                        )
                except ValueError:
                    click.echo(
                        click.style(
                            "❌ Please provide a valid stock number",
                            fg="red",
                            bold=True,
                        )
                    )
                except Exception as e:
                    click.echo(
                        click.style(
                            f"❌ Download failed: {str(e)}", fg="red", bold=True
                        )
                    )
            elif command == "url" and self.client is None:
                if args:
                    if not args.startswith(("http://", "https://")):
                        args = "https://" + args
                    if self.connect_to_node(args):
                        self.display.clear_screen()
                        self.display.show_header()
                        self.display.show_stocks(self.stocks, show_commands=True)
                else:
                    click.echo(
                        click.style("❌ Please provide a URL", fg="red", bold=True)
                    )
            elif command == "refresh" and self.current_stock is None:
                try:
                    self.stocks = self.client.get_stocks()
                    self.display.clear_screen()
                    self.display.show_header()
                    self.display.show_stocks(self.stocks, show_commands=True)
                except Exception as e:
                    click.echo(
                        click.style(
                            f"❌ Failed to refresh stocks: {str(e)}",
                            fg="red",
                            bold=True,
                        )
                    )
            elif command == "search" and self.current_stock is not None:
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
                    show_commands=True,
                )
            elif command == "list" and self.current_stock is not None:
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
                    show_commands=True,
                )
            elif command == "next" and self.current_stock is not None:
                self.current_page += 1
                datasets = self.display.show_datasets(
                    self.client,
                    self.current_stock,
                    self.current_page,
                    self.page_size,
                    self.current_query,
                    show_commands=True,
                )
                if not datasets:
                    self.current_page -= 1
                    click.echo(
                        click.style("\n⚠️  No more datasets", fg="yellow", bold=True)
                    )
            elif command == "prev" and self.current_stock is not None:
                if self.current_page > 0:
                    self.current_page -= 1
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
                        show_commands=True,
                    )
                else:
                    click.echo(
                        click.style(
                            "\n⚠️  Already at first page", fg="yellow", bold=True
                        )
                    )
            else:
                click.echo(click.style("❌ Invalid command", fg="red", bold=True))

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
                            click.style("❌ Invalid node number", fg="red", bold=True)
                        )
                except ValueError:
                    click.echo(
                        click.style(
                            "❌ Please provide a valid node number", fg="red", bold=True
                        )
                    )
            elif command == "url":
                if args:
                    if not args.startswith(("http://", "https://")):
                        args = "https://" + args
                    if self.connect_to_node(args):
                        self.display.clear_screen()
                        self.display.show_header()
                        self.display.show_stocks(self.stocks)
                else:
                    click.echo(
                        click.style("❌ Please provide a URL", fg="red", bold=True)
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
                        self.display.show_datasets(
                            self.client,
                            self.current_stock,
                            self.current_page,
                            self.page_size,
                            self.current_query,
                        )
                    else:
                        click.echo(
                            click.style("❌ Invalid stock number", fg="red", bold=True)
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
                    click.echo(
                        click.style("✓ Stocks refreshed successfully", fg="green")
                    )
                except Exception as e:
                    click.echo(
                        click.style(f"❌ Error refreshing stocks: {str(e)}", fg="red")
                    )
        else:
            # Handle dataset-related commands
            self.handle_dataset_command(command, args)

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
        elif command == "list":
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
        elif command == "view":
            try:
                index = int(args) - 1
                datasets = self.client.search_datasets(
                    self.current_stock["uuid"],
                    query=self.current_query,
                    page=self.current_page,
                    size=self.page_size,
                )

                if 0 <= index < len(datasets):
                    dataset_uuid = datasets[index]["uuid"]
                    click.echo(
                        click.style("\n⟳ Fetching dataset details...", fg="cyan")
                    )
                    dataset_info = self.client.get_dataset(dataset_uuid)
                    self.display.show_dataset_info(dataset_info)

                    # Wait for user input before returning to dataset list
                    click.prompt(
                        "\nPress Enter to return to dataset list",
                        default="",
                        show_default=False,
                    )

                    # Refresh dataset list display
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
                else:
                    click.echo(
                        click.style("❌ Invalid dataset number", fg="red", bold=True)
                    )
            except ValueError:
                click.echo(
                    click.style(
                        "❌ Please provide a valid dataset number", fg="red", bold=True
                    )
                )
        elif command == "back":
            self.current_stock = None
            self.current_page = 0
            self.current_query = ""
            self.display.clear_screen()
            self.display.show_header()
            self.display.show_stocks(self.stocks)

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
