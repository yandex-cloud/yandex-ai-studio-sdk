from __future__ import annotations

import click

from .search_index import vector_stores


@click.group()
@click.version_option()
def cli():
    """Yandex AI Studio CLI utilities."""


cli.add_command(vector_stores)


def main():
    cli()
