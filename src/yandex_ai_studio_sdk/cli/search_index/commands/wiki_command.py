from __future__ import annotations

from dataclasses import dataclass

import click
from yandex_ai_studio_sdk.cli.search_index.commands.base import BaseCommand
from yandex_ai_studio_sdk.cli.search_index.file_sources.wiki import WikiExportFormat, WikiFileSource
from yandex_ai_studio_sdk.cli.search_index.utils.decorators import all_common_options
from yandex_ai_studio_sdk.cli.search_index.utils.helpers import run_command


@dataclass
class WikiCommand(BaseCommand):
    """Command for creating search index from MediaWiki pages."""

    page_urls: tuple[str, ...]
    username: str | None
    password: str | None
    export_format: WikiExportFormat

    def create_file_source(self) -> WikiFileSource:
        """Create WikiFileSource with configured parameters."""
        return WikiFileSource(
            page_urls=list(self.page_urls),
            username=self.username,
            password=self.password,
            export_format=self.export_format,
        )


@click.command(name="wiki")
@click.argument("page_urls", nargs=-1, required=True)
@click.option(
    "--username",
    envvar="WIKI_USERNAME",
    help="Wiki username (or use WIKI_USERNAME env var)",
)
@click.option(
    "--password",
    envvar="WIKI_PASSWORD",
    help="Wiki password (or use WIKI_PASSWORD env var)",
)
@click.option(
    "--export-format",
    type=click.Choice(["text", "html", "markdown"]),
    default="text",
    show_default=True,
    help="Format for exporting page content",
)
@all_common_options
def wiki_command(**kwargs):
    """
    Create a search index from MediaWiki pages.

    This command parses page content from a MediaWiki instance (like Wikipedia),
    uploads it to Yandex Cloud, and creates a search index.

    Simply copy the page URL from your browser and use it with --page-url.
    You can specify multiple pages by using --page-url multiple times.

    Authentication is optional for public wikis like Wikipedia.
    """
    run_command(WikiCommand, **kwargs)
