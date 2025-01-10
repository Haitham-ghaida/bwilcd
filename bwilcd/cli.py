"""BWI ILCD Network Interactive Client"""

import click
from .ui.session import Session


@click.command()
def main():
    """BWILCD command line interface"""
    session = Session()
    session.start()


if __name__ == "__main__":
    main()
