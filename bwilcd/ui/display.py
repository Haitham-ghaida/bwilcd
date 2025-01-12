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

    def show_nodes(self, show_commands: bool = True):
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
        if show_commands:
            click.echo("\n" + click.style("Commands:", fg="cyan", bold=True))
            click.echo(
                "  "
                + click.style("number", fg="green")
                + "         - Connect to a node"
            )
            click.echo(
                "  "
                + click.style("url <custom_url>", fg="green")
                + " - Connect to custom URL"
            )
            click.echo("  " + click.style("quit", fg="red") + "          - Exit")
            click.echo(
                "  " + click.style("help", fg="yellow") + "          - Show help"
            )

    def show_stocks(self, stocks: List[Dict], show_commands: bool = True):
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
        if show_commands:
            self.show_stock_commands()

    def show_stock_commands(self):
        """Show commands for stock view"""
        click.echo("\n" + click.style("Commands:", fg="cyan", bold=True))
        click.echo(
            "  "
            + click.style("number", fg="green")
            + "         - Select a stock to browse"
        )
        click.echo(
            "  " + click.style("back", fg="yellow") + "          - Go back to nodes"
        )
        click.echo(
            "  " + click.style("refresh", fg="yellow") + "       - Refresh stocks"
        )
        click.echo("  " + click.style("quit", fg="red") + "          - Exit")
        click.echo("  " + click.style("help", fg="yellow") + "          - Show help")

    def show_dataset_commands(self):
        """Show commands for dataset view"""
        click.echo("\n" + click.style("Commands:", fg="cyan", bold=True))
        click.echo(
            "  " + click.style("number", fg="green") + "         - View dataset details"
        )
        click.echo(
            "  " + click.style("search <query>", fg="green") + " - Search datasets"
        )
        click.echo(
            "  " + click.style("list", fg="green") + "           - List all datasets"
        )
        click.echo("  " + click.style("next", fg="yellow") + "          - Next page")
        click.echo(
            "  " + click.style("prev", fg="yellow") + "          - Previous page"
        )
        click.echo(
            "  " + click.style("back", fg="yellow") + "          - Go back to stocks"
        )
        click.echo("  " + click.style("quit", fg="red") + "          - Exit")
        click.echo("  " + click.style("help", fg="yellow") + "          - Show help")

    def show_datasets(
        self,
        client: SodaClient,
        stock: Dict,
        page: int,
        page_size: int,
        query: str = "",
        show_commands: bool = True,
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

            if show_commands:
                self.show_dataset_commands()

            return datasets
        except Exception as e:
            click.echo(
                click.style(
                    f"❌ Error listing datasets: {str(e)}", fg="red", bold=True
                ),
                err=True,
            )
            return []

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

    def show_dataset_info(self, dataset_info: Dict):
        """Display detailed information about a dataset"""
        click.echo("\n" + click.style("Dataset Information:", fg="cyan", bold=True))
        click.echo("=" * 80)

        # Basic information
        click.echo(
            click.style("Name: ", fg="green", bold=True)
            + click.style(dataset_info.get("name", "N/A"), fg="white")
        )
        click.echo(
            click.style("UUID: ", fg="green", bold=True)
            + click.style(dataset_info.get("uuid", "N/A"), fg="bright_black")
        )
        click.echo(
            click.style("Reference Year: ", fg="green", bold=True)
            + click.style(str(dataset_info.get("reference_year", "N/A")), fg="white")
        )
        click.echo(
            click.style("Geography: ", fg="green", bold=True)
            + click.style(dataset_info.get("geography", "N/A"), fg="blue")
        )

        # Description
        if dataset_info.get("description"):
            click.echo("\n" + click.style("Description:", fg="yellow", bold=True))
            click.echo("-" * 80)
            click.echo(
                click.style(
                    dataset_info["description"][:500]
                    + ("..." if len(dataset_info["description"]) > 500 else ""),
                    fg="white",
                )
            )

        # Technology description
        if dataset_info.get("technology"):
            click.echo(
                "\n" + click.style("Technology Description:", fg="yellow", bold=True)
            )
            click.echo("-" * 80)
            click.echo(
                click.style(
                    dataset_info["technology"][:500]
                    + ("..." if len(dataset_info["technology"]) > 500 else ""),
                    fg="white",
                )
            )

        # Exchanges
        if dataset_info.get("exchanges"):
            # Group exchanges by direction
            inputs = [e for e in dataset_info["exchanges"] if e.direction == "Input"]
            outputs = [e for e in dataset_info["exchanges"] if e.direction == "Output"]

            # Find reference flow
            ref_flow = next(
                (e for e in dataset_info["exchanges"] if e.is_reference_flow), None
            )

            # Format inputs
            if inputs:
                click.echo("\n" + click.style("Inputs:", fg="blue", bold=True))
                click.echo("-" * 80)
                headers = ["Flow", "Amount"]
                table_data = []
                for e in sorted(inputs, key=lambda x: abs(x.amount), reverse=True):
                    flow_name = e.flow_name
                    if e == ref_flow:
                        flow_name = click.style(
                            f"⭐ {flow_name} (Reference Flow)", fg="yellow", bold=True
                        )
                    table_data.append([flow_name, f"{e.amount:g}"])
                click.echo(
                    tabulate(table_data, headers=headers, tablefmt="rounded_grid")
                )

            # Format outputs
            if outputs:
                click.echo("\n" + click.style("Outputs:", fg="magenta", bold=True))
                click.echo("-" * 80)
                headers = ["Flow", "Amount"]
                table_data = []
                for e in sorted(outputs, key=lambda x: abs(x.amount), reverse=True):
                    flow_name = e.flow_name
                    if e == ref_flow:
                        flow_name = click.style(
                            f"⭐ {flow_name} (Reference Flow)", fg="yellow", bold=True
                        )
                    table_data.append([flow_name, f"{e.amount:g}"])
                click.echo(
                    tabulate(table_data, headers=headers, tablefmt="rounded_grid")
                )
