"""BWI ILCD Network Interactive Client"""

import click
import sys
from .ui.session import Session
import traceback


@click.command()
def main():
    """BWI ILCD Network Interactive Client"""
    try:
        # Set up error handling
        sys.excepthook = lambda type, value, tb: print(
            click.style(
                f"\n❌ Error: {str(value)}\n{traceback.format_tb(tb)[-1]}",
                fg="red",
                bold=True,
            )
        )

        session = Session()
        session.start()
    except KeyboardInterrupt:
        click.echo(
            click.style("\n👋 Interrupted by user. Goodbye!", fg="cyan", bold=True)
        )
        sys.exit(0)
    except Exception as e:
        click.echo(click.style(f"\n❌ Fatal error: {str(e)}", fg="red", bold=True))
        click.echo(click.style("Traceback:", fg="red"))
        traceback.print_exc()
        sys.exit(1)

    click.echo(click.style("\n👋 Goodbye!", fg="cyan", bold=True))


if __name__ == "__main__":
    main()
