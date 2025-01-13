import click
from tabulate import tabulate
from typing import List, Dict, Optional, Any
from ..client import SodaClient
import json
import os
import pkg_resources
from prompt_toolkit.styles import Style

DEFAULT_NODE = {"name": "ProBas", "url": "https://data.probas.umweltbundesamt.de"}


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
                return [DEFAULT_NODE]

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
                        return [DEFAULT_NODE]
                    return data["nodes"]
                except json.JSONDecodeError as e:
                    click.echo(
                        click.style(
                            f"❌ Warning: Error parsing nodes.json: {str(e)} - using default nodes",
                            fg="yellow",
                            bold=True,
                        )
                    )
                    return [DEFAULT_NODE]
        except Exception as e:
            click.echo(
                click.style(
                    f"❌ Warning: Error loading nodes: {str(e)} - using default nodes",
                    fg="yellow",
                    bold=True,
                )
            )
            return [DEFAULT_NODE]

    def clear_screen(self):
        """Clear the terminal screen"""
        click.clear()

    def show_header_intro(self):
        """Show the application header"""
        header = """
                                               .                                                               
                                      .::                     :.                                       
                                      :.:.:                 :.:.                                       
                                    .: .:..::             .:.:.:                                       
                                    : . . .  :          ::  .: .:                                      
                                   ..   .:.   ..       : .  .:.  :                                     
                                   ..    ::    .:     :    . :   .:                                    
                                   .      :   ....   .:. ....:  .  :                  .::.:            
                                   ::.....:.  . ..   .....  :      :     .::.  .     .   :             
                                   ...    :      :   ..     :.    .:   .: ..     .  . ..:              
                                    :     ::.    .   ..     :     .: :.   .   .   ..   ..              
           :-::... ...::            ..    ..    ..   ..    ::.    : ::        . .  .  ..               
             :. ::.    . :           ::. .:.   ::    ....  :    ..: . .      .:.    ..:                
              :. ..:. .   :.           .:... :.       .:  .:.   .: ..  . ..    .   . :.                
               :.   .:.    :              ::            :. : . ..  ..  .  ..    .   :.                 
                .     :.    :       .:::::-::.            ::.::    .:.   .     .   :                   
                 :......:.  :   :---:     ::::::-:.        :..:.       :..       ::                    
                   :  .  : : .:--:      .. .::...:. .:::.. :::::::::     :::::::                       
                    .:...::.:=-:        :.. ..  ..:       ...:.  .. ..                                 
                          :-=-.   ..   .:.   :     :      . . ..      .:                               
                         :-=-::: . ...:..   .:.   ..:     .. . .:.  .. .:.                             
                        .--=  ..:  ..  :. .. .:..   :     :: ... :     . :                             
                        --=: ... .:.  .::.     :    :     ..     ..:  .   :                            
                        ...  ...   ::. .  .:.  .:. .:      ..      .::.    :                           
                              .:.  ..:.:    .:. .:.:        .:.      .:.   .:                          
                                 ::..:.:       .:.::          :.        :.  :                          
                                    .:::.         :.            .::.  .  :..:                          
                                                                    ...:..:::                          
           =%####%*.         -%=            :#*         ::                                             
           =%:   :%#                        :#*        :%*                                             
           =%:   :%%. .%#*%= :%-  .+%%%**%. :##*%%%* .*%%%%- %*   *#:  -%-  -#%%%*:  %*.  -%=          
           =%*++*%*.  :%#:   -%-  +%:  .*%. :#%.  =%=  :%*   +#: :%%=  **: -%=  .**. =%-  *#:          
           =%=:::*%+  :%*    -%- .#*.   *%  :#*   =%+  :%*   .%= *#=%: %=    .-==#*. :** :%=           
           =%:    *%- :%*    -%- .#*.   *%. :#*   =%+  :%*    +*=%-:*==#:  :##=::**.  =%:**:           
           =%:    #%: :%*    -%-  *#:   *%. :#*   =%+  :%*    :%%#  =%%*   +%-  .**.  :*#%=            
           =%####%%-  :%*    -%-  :#%**#%%  :#*   =%+   %%*:  .*%:  :#%:   :%%**%%#.   =%%.            
                                     .  *%.               .                   .        -%=             
                                  .=-::=%*                                           .:**              
                                   :=++=:                                            =*=     
            ╔═══════════════════════════════════════════════════════════════════════════╗
            ║                       ILCD Network Interactive Client                     ║
            ╚═══════════════════════════════════════════════════════════════════════════╝
"""
        click.echo(click.style(header, fg="cyan", bold=True))

    def show_header(self):
        """Show the application header"""
        header = """
            ╔═══════════════════════════════════════════════════════════════════════════╗
            ║                       ILCD Network Interactive Client                     ║
            ╚═══════════════════════════════════════════════════════════════════════════╝
"""

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

    def show_separator(self):
        """Show a styled separator line"""
        click.secho("─" * 100, fg="blue")

    def show_dataset_info(self, dataset_info: Dict[str, Any]):
        """Display detailed dataset information"""
        click.secho("\n📊 Dataset Details", fg="cyan", bold=True)

        # Basic Info
        headers = [
            click.style("Property", fg="magenta", bold=True),
            click.style("Value", fg="magenta", bold=True),
        ]

        basic_info = [
            ["Name", dataset_info.get("name", "N/A")],
            ["UUID", dataset_info.get("uuid", "N/A")],
            ["Reference Year", dataset_info.get("reference_year", "N/A")],
            ["Geography", dataset_info.get("geography", "N/A")],
            ["Functional Unit", dataset_info.get("functional_unit", "N/A")],
        ]

        basic_info = [
            [click.style(row[0], fg="blue"), click.style(row[1], fg="yellow")]
            for row in basic_info
        ]

        print(tabulate(basic_info, headers=headers, tablefmt="grid"))

        if "exchanges" in dataset_info and dataset_info["exchanges"]:
            click.secho("\n📊 Exchanges:", fg="cyan", bold=True)

            exchange_headers = [
                click.style(h, fg="magenta", bold=True)
                for h in [
                    "Flow Name",
                    "Direction",
                    "Amount",
                    "Type",
                    "Category",
                    "Unit",
                ]
            ]

            exchange_rows = []
            for ex in dataset_info["exchanges"]:
                # Add star and highlight reference flows
                flow_name = (
                    f"⭐ {ex.flow_name}" if ex.is_reference_flow else ex.flow_name
                )
                style_color = "bright_yellow" if ex.is_reference_flow else "cyan"

                row = [
                    click.style(flow_name, fg=style_color, bold=ex.is_reference_flow),
                    click.style(
                        str(ex.direction), fg=style_color, bold=ex.is_reference_flow
                    ),
                    click.style(str(ex.amount), fg="yellow"),
                    click.style(str(ex.unit), fg="magenta"),
                    click.style(str(ex.type), fg="blue"),
                    click.style(str(ex.category), fg="green"),
                ]
                exchange_rows.append(row)

            print(tabulate(exchange_rows, headers=exchange_headers, tablefmt="grid"))
