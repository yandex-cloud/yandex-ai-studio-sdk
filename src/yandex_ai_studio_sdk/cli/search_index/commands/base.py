from __future__ import annotations

import abc
import asyncio
import json
from dataclasses import dataclass, field

import click
from yandex_ai_studio_sdk import AsyncAIStudio
from yandex_ai_studio_sdk._logging import TRACE, LogLevel, get_logger, setup_default_logging
from yandex_ai_studio_sdk._types.misc import UNDEFINED
from yandex_ai_studio_sdk.cli.search_index.file_sources.base import BaseFileSource
from yandex_ai_studio_sdk.cli.search_index.legacy_mapper import LegacyYandexMapper
from yandex_ai_studio_sdk.cli.search_index.openai_types import OpenAIFileCreateParams, OpenAIVectorStoreCreateParams
from yandex_ai_studio_sdk.cli.search_index.uploader import AsyncSearchIndexUploader, UploadConfig

logger = get_logger(__name__)


@dataclass
class BaseCommand(abc.ABC):
    """
    Base class for all CLI commands.
    """
    # SDK options
    folder_id: str | None
    auth: str | None
    endpoint: str | None
    verbose: int
    # Vector store & file options
    vector_store_params: OpenAIVectorStoreCreateParams
    file_create_params: OpenAIFileCreateParams
    # Upload options
    max_concurrent_uploads: int
    skip_on_error: bool
    poll_timeout: int
    # Output
    output_format: str

    sdk: AsyncAIStudio = field(init=False)

    def __post_init__(self) -> None:
        self.setup_logging()
        self.sdk = self.create_sdk()

    def setup_logging(self) -> None:
        """Configure logging based on verbosity level."""
        level: LogLevel
        if self.verbose == 0:
            level = "WARNING"
        elif self.verbose == 1:
            level = "INFO"
        elif self.verbose == 2:
            level = "DEBUG"
        else:
            level = TRACE

        setup_default_logging(log_level=level)

    def create_sdk(self) -> AsyncAIStudio:
        sdk = AsyncAIStudio(
            folder_id=self.folder_id if self.folder_id else UNDEFINED,
            auth=self.auth if self.auth else UNDEFINED,
            endpoint=self.endpoint if self.endpoint else UNDEFINED,
        )
        logger.debug("SDK initialized successfully")
        return sdk

    def create_upload_config(self) -> UploadConfig:
        """
        Create upload configuration from OpenAI-compatible CLI parameters.

        TODO: Remove this method when migrating to native OpenAI API.
        Uses LegacyYandexMapper to convert OpenAI params to Yandex SDK format.
        """
        return LegacyYandexMapper.create_legacy_upload_config(
            file_create_params=self.file_create_params,
            vector_store_create_params=self.vector_store_params,
            skip_on_error=self.skip_on_error,
            max_concurrent_uploads=self.max_concurrent_uploads,
            poll_timeout=self.poll_timeout,
        )

    @abc.abstractmethod
    def create_file_source(self) -> BaseFileSource:
        """Create file source specific to this command."""

    def execute(self) -> None:
        asyncio.run(self._execute_async())

    async def _execute_async(self) -> None:
        """Async implementation of execute."""
        file_source = self.create_file_source()
        config = self.create_upload_config()

        uploader = AsyncSearchIndexUploader(self.sdk, config)
        search_index = await uploader.upload_from_source(file_source)

        self._output_success(search_index)

    def _output_success(self, search_index) -> None:
        """Output success message with search index details."""
        if self.output_format == "json":
            result = {
                "status": "success",
                "folder_id": self.folder_id,
                "search_index": {
                    "id": search_index.id,
                    "name": search_index.name,
                },
            }
            print(json.dumps(result))
        else:
            click.echo("\nSearch index created successfully!")
            click.echo(f"Search Index ID: {search_index.id}")
            if search_index.name:
                click.echo(f"Name: {search_index.name}")
            if self.folder_id:
                click.echo(f"Folder ID: {self.folder_id}")
