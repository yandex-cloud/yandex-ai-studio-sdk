from __future__ import annotations

from dataclasses import dataclass

import click
from yandex_ai_studio_sdk.cli.search_index.commands.base import BaseCommand
from yandex_ai_studio_sdk.cli.search_index.file_sources.s3 import S3FileSource
from yandex_ai_studio_sdk.cli.search_index.utils.decorators import all_common_options
from yandex_ai_studio_sdk.cli.search_index.utils.helpers import run_command


@dataclass
class S3Command(BaseCommand):
    """Command for creating search index from S3-compatible storage."""

    bucket: str
    prefix: str
    endpoint_url: str | None
    aws_access_key_id: str | None
    aws_secret_access_key: str | None
    region_name: str | None
    include_patterns: tuple[str, ...]
    exclude_patterns: tuple[str, ...]
    max_file_size: int | None

    def create_file_source(self) -> S3FileSource:
        """Create S3FileSource with configured parameters."""
        return S3FileSource(
            bucket=self.bucket,
            prefix=self.prefix,
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name,
            include_patterns=list(self.include_patterns) if self.include_patterns else None,
            exclude_patterns=list(self.exclude_patterns) if self.exclude_patterns else None,
            max_file_size=self.max_file_size,
        )


@click.command(name="s3")
@click.argument("bucket")
@click.option(
    "--prefix",
    default="",
    show_default=True,
    help="Prefix (folder path) within the bucket",
)
@click.option(
    "--endpoint-url",
    help="Custom S3 endpoint URL (for S3-compatible services)",
)
@click.option(
    "--aws-access-key-id",
    envvar="AWS_ACCESS_KEY_ID",
    help="AWS access key ID (or use AWS_ACCESS_KEY_ID env var)",
)
@click.option(
    "--aws-secret-access-key",
    envvar="AWS_SECRET_ACCESS_KEY",
    help="AWS secret access key (or use AWS_SECRET_ACCESS_KEY env var)",
)
@click.option(
    "--region-name",
    envvar="AWS_DEFAULT_REGION",
    help="AWS region name (or use AWS_DEFAULT_REGION env var)",
)
@click.option(
    "--include-pattern",
    "include_patterns",
    multiple=True,
    help="Glob patterns to include (can be specified multiple times)",
)
@click.option(
    "--exclude-pattern",
    "exclude_patterns",
    multiple=True,
    help="Glob patterns to exclude (can be specified multiple times)",
)
@click.option(
    "--max-file-size",
    type=int,
    help="Maximum file size in bytes (larger files will be skipped)",
)
@all_common_options
def s3_command(**kwargs):
    """
    Create a search index from S3-compatible storage.

    This command downloads files from an S3 bucket, uploads them to
    Yandex Cloud, and creates a search index.
    """
    run_command(S3Command, **kwargs)
