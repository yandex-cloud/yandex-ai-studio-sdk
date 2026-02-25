from __future__ import annotations

from pathlib import Path

import click

from yandex_ai_studio_sdk.cli.search_index.commands.base import BaseCommand
from yandex_ai_studio_sdk.cli.search_index.file_sources.local import LocalFileSource
from yandex_ai_studio_sdk.cli.search_index.openai_types import OpenAIFileCreateParams
from yandex_ai_studio_sdk.cli.search_index.utils.decorators import all_common_options
from yandex_ai_studio_sdk.cli.search_index.utils.helpers import create_command_executor


class LocalCommand(BaseCommand):
    """Command for creating search index from local filesystem files."""

    def __init__(
        self,
        # Local-specific options
        paths: tuple[Path, ...],
        max_file_size: int | None,
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
        """Initialize local command with local-specific and common parameters."""
        self.paths = paths
        self.max_file_size = max_file_size

        # Set default vector store name to the single directory name if applicable
        if not name and len(paths) == 1 and paths[0].is_dir():
            name = paths[0].name

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

    def create_file_source(self) -> LocalFileSource:
        """Create LocalFileSource with configured parameters."""
        return LocalFileSource(
            paths=list(self.paths),
            max_file_size=self.max_file_size,
        )


@click.command(name="local")
@click.argument(
    "paths",
    nargs=-1,
    required=True,
    type=click.Path(exists=True, path_type=Path),
)
@click.option(
    "--max-file-size",
    type=int,
    help="Maximum file size in bytes (larger files will be skipped)",
)
@all_common_options
def local_command(**kwargs):
    """
    Create a search index from local files or directories.

    PATHS can be individual files or directories (scanned recursively).
    Use shell glob expansion to filter by pattern:

        vector-stores local /docs/\n
        vector-stores local /docs/*.pdf /notes/*.md\n
        vector-stores local report.pdf summary.txt
    """
    create_command_executor(LocalCommand, **kwargs)
