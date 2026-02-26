from __future__ import annotations

import click

from yandex_ai_studio_sdk.cli.search_index.commands.base import BaseCommand
from yandex_ai_studio_sdk.cli.search_index.file_sources.wiki import WikiExportFormat, WikiFileSource
from yandex_ai_studio_sdk.cli.search_index.openai_types import OpenAIFileCreateParams
from yandex_ai_studio_sdk.cli.search_index.utils.decorators import all_common_options
from yandex_ai_studio_sdk.cli.search_index.utils.helpers import run_command


class WikiCommand(BaseCommand):
    """Command for creating search index from MediaWiki pages."""

    def __init__(
        self,
        # Wiki-specific options
        page_urls: tuple[str, ...],
        username: str | None,
        password: str | None,
        export_format: WikiExportFormat,
        # Common options
        folder_id: str | None,
        auth: str | None,
        endpoint: str | None,
        verbose: int,
        name: str | None,
        metadata: tuple[str, ...],
        expires_after_days: int | None,
        expires_after_anchor: str | None,
        max_chunk_size_tokens: int,
        chunk_overlap_tokens: int,
        file_create_params: OpenAIFileCreateParams,
        max_concurrent_uploads: int,
        skip_on_error: bool,
        output_format: str,
    ):
        """Initialize Wiki command with Wiki-specific and common parameters."""
        self.page_urls = page_urls
        self.username = username
        self.password = password
        self.export_format = export_format

        super().__init__(
            folder_id=folder_id,
            auth=auth,
            endpoint=endpoint,
            verbose=verbose,
            name=name,
            metadata=metadata,
            expires_after_days=expires_after_days,
            expires_after_anchor=expires_after_anchor,
            max_chunk_size_tokens=max_chunk_size_tokens,
            chunk_overlap_tokens=chunk_overlap_tokens,
            file_create_params=file_create_params,
            max_concurrent_uploads=max_concurrent_uploads,
            skip_on_error=skip_on_error,
            output_format=output_format,
        )

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
