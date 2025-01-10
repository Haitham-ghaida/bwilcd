import click
from tabulate import tabulate
from typing import List, Dict, Optional
from ..client import SodaClient
import json
import os
import pkg_resources
from prompt_toolkit.styles import Style


class Display:
    def __init__(self):
        self.nodes = self.load_nodes()

    def load_nodes(self) -> List[Dict]:
        """Load predefined nodes from JSON file"""
        try:
            # First try to get the file from the package resources
            try:
                json_path = pkg_resources.resource_filename("bwilcd", "nodes.json")
            except Exception:
                # If that fails, try to find it relative to this file
                current_dir = os.path.dirname(os.path.abspath(__file__))
                json_path = os.path.join(os.path.dirname(current_dir), "nodes.json")

            if not os.path.exists(json_path):
                click.echo(
                    click.style(
                        f"❌ Warning: nodes.json not found at {json_path}",
                        fg="yellow",
                        bold=True,
                    )
                )
                # Return default nodes if file not found
                return [
                    {"name": "ProBas", "url": "https://data.probas.umweltbundesamt.de"}
                ]

            with open(json_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    if not isinstance(data, dict) or "nodes" not in data:
                        click.echo(
                            click.style(
                                "❌ Warning: Invalid nodes.json format - using default nodes",
                                fg="yellow",
                                bold=True,
                            )
                        )
                        return [
                            {
                                "name": "ProBas",
                                "url": "https://data.probas.umweltbundesamt.de",
                            }
                        ]
                    return data["nodes"]
                except json.JSONDecodeError as e:
                    click.echo(
                        click.style(
                            f"❌ Warning: Error parsing nodes.json: {str(e)} - using default nodes",
                            fg="yellow",
                            bold=True,
                        )
                    )
                    return [
                        {
                            "name": "ProBas",
                            "url": "https://data.probas.umweltbundesamt.de",
                        }
                    ]
        except Exception as e:
            click.echo(
                click.style(
                    f"❌ Warning: Error loading nodes: {str(e)} - using default nodes",
                    fg="yellow",
                    bold=True,
                )
            )
            return [{"name": "ProBas", "url": "https://data.probas.umweltbundesamt.de"}]

    def clear_screen(self):
        """Clear the terminal screen"""
        click.clear()

    def show_header(self):
        """Show the application header"""
        header = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                       Brightway ILCD Network Interactive Client           ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""
        click.echo(click.style(header, fg="cyan", bold=True))

    def show_nodes(self):
        """Show available ILCD nodes"""
        self.clear_screen()
        self.show_header()
        headers = [
            click.style("#", fg="cyan", bold=True),
            click.style("Name", fg="cyan", bold=True),
            click.style("URL", fg="cyan", bold=True),
        ]
        table_data = [
            [
                click.style(str(i + 1), fg="green"),
                click.style(node["name"], fg="yellow", bold=True),
                click.style(node["url"], fg="blue"),
            ]
            for i, node in enumerate(self.nodes)
        ]
        click.echo(
            "\n" + tabulate(table_data, headers=headers, tablefmt="rounded_grid")
        )
        click.echo("\n" + click.style("Commands:", fg="cyan", bold=True))
        click.echo(
            "  "
            + click.style("c|connect <number>", fg="green")
            + " - Connect to a node"
        )
        click.echo(
            "  "
            + click.style("url <custom_url>", fg="green")
            + " - Connect to custom URL"
        )
        click.echo(
            "  " + click.style("q|quit", fg="red") + "           - Exit the program"
        )
        click.echo(
            "  " + click.style("h|help", fg="yellow") + "           - Show this help"
        )

    def show_stocks(self, stocks: List[Dict]):
        """Show available stocks"""
        headers = [
            click.style("#", fg="cyan", bold=True),
            click.style("Name", fg="cyan", bold=True),
            click.style("UUID", fg="cyan", bold=True),
            click.style("Description", fg="cyan", bold=True),
        ]
        table_data = [
            [
                click.style(str(i + 1), fg="green"),
                click.style(s["name"], fg="yellow", bold=True),
                click.style(s["uuid"], fg="bright_black"),
                click.style(s.get("description", ""), fg="white"),
            ]
            for i, s in enumerate(stocks)
        ]
        click.echo(
            "\n" + click.style("📦 Available Data Stocks:", fg="cyan", bold=True)
        )
        click.echo(tabulate(table_data, headers=headers, tablefmt="rounded_grid"))
        self.show_stock_commands()

    def show_stock_commands(self):
        """Show commands for stock view"""
        click.echo("\n" + click.style("Commands:", fg="cyan", bold=True))
        click.echo(
            "  "
            + click.style("sl|select <number>", fg="green")
            + " - Select a stock to browse"
        )
        click.echo(
            "  " + click.style("d|dd <number>", fg="green") + "      - Download a stock"
        )
        click.echo(
            "  " + click.style("b|back", fg="yellow") + "            - Go back to nodes"
        )
        click.echo(
            "  " + click.style("r|refresh", fg="yellow") + "         - Refresh stocks"
        )
        click.echo("  " + click.style("q|quit", fg="red") + "             - Exit")
        click.echo(
            "  " + click.style("h|help", fg="yellow") + "             - Show help"
        )

    def show_dataset_commands(self):
        """Show commands for dataset view"""
        click.echo("\n" + click.style("Commands:", fg="cyan", bold=True))
        click.echo(
            "  " + click.style("s|search <query>", fg="green") + " - Search datasets"
        )
        click.echo(
            "  " + click.style("ll", fg="green") + "              - List all datasets"
        )
        click.echo("  " + click.style("n|next", fg="yellow") + "           - Next page")
        click.echo(
            "  " + click.style("p|prev", fg="yellow") + "           - Previous page"
        )
        click.echo(
            "  "
            + click.style("b|back", fg="yellow")
            + "            - Go back to stocks"
        )
        click.echo(
            "  "
            + click.style("d|dd", fg="green")
            + "              - Download current stock"
        )
        click.echo("  " + click.style("q|quit", fg="red") + "             - Exit")
        click.echo(
            "  " + click.style("h|help", fg="yellow") + "             - Show help"
        )

    def show_datasets(
        self,
        client: SodaClient,
        stock: Dict,
        page: int,
        page_size: int,
        query: str = "",
    ) -> List[Dict]:
        """Show datasets for a stock with pagination"""
        try:
            click.echo(
                "\n"
                + click.style("⟳ Fetching datasets...", fg="cyan", bold=True)
                + (click.style(f" (search: '{query}')", fg="yellow") if query else "")
            )
            datasets = client.search_datasets(
                stock["uuid"], query=query, page=page, size=page_size
            )
            if datasets:
                # Calculate absolute numbering
                start_num = (page * page_size) + 1

                # Create a rich table with colors and formatting
                headers = [
                    click.style("#", fg="cyan", bold=True),
                    click.style("Name", fg="cyan", bold=True),
                    click.style("Type", fg="cyan", bold=True),
                    click.style("Location", fg="cyan", bold=True),
                    click.style("UUID", fg="cyan", bold=True),
                ]
                table_data = []

                for i, d in enumerate(datasets):
                    # Get dataset number (continuous across pages)
                    num = start_num + i

                    # Format the row data
                    name = click.style(d["name"], fg="green", bold=True)
                    dtype = click.style(d.get("dataset_type", "Process"), fg="yellow")
                    location = click.style(d.get("location", ""), fg="blue", bold=True)
                    uuid = click.style(d["uuid"], fg="bright_black")

                    table_data.append([str(num), name, dtype, location, uuid])

                # Show page info with colors
                total_size = (
                    client.total_size
                    if hasattr(client, "total_size")
                    else len(datasets)
                )
                page_info = click.style(
                    f"\n📊 Datasets (Page {page + 1}, showing {len(datasets)} of {total_size} results, starting at #{start_num})",
                    fg="cyan",
                    bold=True,
                )
                click.echo(page_info)

                # Show the table with grid format
                click.echo(
                    tabulate(
                        table_data,
                        headers=headers,
                        tablefmt="rounded_grid",
                        colalign=("right", "left", "left", "center", "left"),
                    )
                )
            else:
                if query:
                    click.echo(
                        click.style(
                            "\n❌ No datasets found matching your search", fg="red"
                        )
                    )
                else:
                    click.echo(
                        click.style("\n❌ No datasets found in this stock", fg="red")
                    )
            return datasets
        except Exception as e:
            click.echo(
                click.style(
                    f"❌ Error listing datasets: {str(e)}", fg="red", bold=True
                ),
                err=True,
            )
            return []

    def show_help(self, client: Optional[SodaClient], current_stock: Optional[Dict]):
        """Show context-sensitive help"""
        self.clear_screen()
        self.show_header()
        if client is None:
            self.show_nodes()
        elif current_stock is None:
            self.show_stock_commands()
        else:
            self.show_dataset_commands()

    def get_prompt_style(self):
        """Get the style for the prompt"""
        return Style.from_dict(
            {
                # User input (default text)
                "": "#ffffff",
                # Prompt
                "prompt": "#00ffff bold",
            }
        )
