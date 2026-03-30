from __future__ import annotations

from dataclasses import dataclass

import click
from yandex_ai_studio_sdk.cli.search_index.commands.base import BaseCommand
from yandex_ai_studio_sdk.cli.search_index.file_sources.confluence import ConfluenceExportFormat, ConfluenceFileSource
from yandex_ai_studio_sdk.cli.search_index.utils.decorators import all_common_options
from yandex_ai_studio_sdk.cli.search_index.utils.helpers import run_command, validate_authentication


@dataclass
class ConfluenceCommand(BaseCommand):
    """Command for creating search index from Atlassian Confluence pages."""

    page_urls: tuple[str, ...]
    base_url: str | None
    username: str | None
    api_token: str | None
    export_format: ConfluenceExportFormat
    no_verify: bool

    def __post_init__(self) -> None:
        if self.username or self.api_token:
            self.username, self.api_token = validate_authentication(
                self.username,
                self.api_token,
                auth_type="Confluence authentication",
            )
        super().__post_init__()

    def create_file_source(self) -> ConfluenceFileSource:
        """Create ConfluenceFileSource with configured parameters."""
        return ConfluenceFileSource(
            page_urls=list(self.page_urls),
            base_url=self.base_url,
            username=self.username,
            api_token=self.api_token,
            export_format=self.export_format,
            verify_ssl=not self.no_verify,
        )


@click.command(name="confluence")
@click.option(
    "--page-url",
    "page_urls",
    multiple=True,
    required=True,
    help="Page URL(s) to export (e.g., https://your-domain/display/SPACE/Page+Title). Can be specified multiple times.",
)
@click.option(
    "--base-url",
    help="Confluence base URL (e.g., https://cwiki.apache.org/confluence). If not specified, extracted from first page URL.",
)
@click.option(
    "--username",
    envvar="CONFLUENCE_USERNAME",
    help="Confluence username (email) - optional for public instances (or use CONFLUENCE_USERNAME env var)",
)
@click.option(
    "--api-token",
    envvar="CONFLUENCE_API_TOKEN",
    help="Confluence API token - optional for public instances (or use CONFLUENCE_API_TOKEN env var)",
)
@click.option(
    "--export-format",
    type=click.Choice(["pdf", "html", "markdown"]),
    default="pdf",
    show_default=True,
    help="Format for exporting pages",
)
@click.option(
    "--no-verify",
    is_flag=True,
    default=False,
    help="Disable SSL certificate verification (for self-signed certs)",
)
@all_common_options
def confluence_command(**kwargs):
    """
    Create a search index from Atlassian Confluence pages.

    This command exports page content from Confluence by URL,
    uploads it to Yandex Cloud, and creates a search index.

    Simply copy the page URL from your browser and use it with --page-url.
    You can specify multiple pages by using --page-url multiple times.

    Authentication is optional. For public Confluence instances, you can omit
    --username and --api-token. For private instances, provide credentials via
    command line options or CONFLUENCE_USERNAME and CONFLUENCE_API_TOKEN environment variables.
    """
    run_command(ConfluenceCommand, **kwargs)
