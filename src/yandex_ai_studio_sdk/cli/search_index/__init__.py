from __future__ import annotations

import click

from .commands.confluence_command import confluence_command
from .commands.local_command import local_command
from .commands.s3_command import s3_command
from .commands.wiki_command import wiki_command


@click.group(name="vector-stores")
def vector_stores():
    """
    Create Yandex Cloud search indexes from various file sources.

    This tool helps you upload files from different sources (local filesystem,
    S3, Confluence, Wiki) and create search indexes for use with Yandex Cloud
    Assistants API.
    """


vector_stores.add_command(local_command)
vector_stores.add_command(s3_command)
vector_stores.add_command(confluence_command)
vector_stores.add_command(wiki_command)


__all__: list = []
