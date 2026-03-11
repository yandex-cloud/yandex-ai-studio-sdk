from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import click
from yandex_ai_studio_sdk.cli.search_index.commands.base import BaseCommand
from yandex_ai_studio_sdk.cli.search_index.file_sources.local import LocalFileSource
from yandex_ai_studio_sdk.cli.search_index.utils.decorators import all_common_options
from yandex_ai_studio_sdk.cli.search_index.utils.helpers import run_command


@dataclass
class LocalCommand(BaseCommand):
    """Command for creating search index from local filesystem files."""

    paths: tuple[Path, ...]
    max_file_size: int | None

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
    run_command(LocalCommand, **kwargs)
