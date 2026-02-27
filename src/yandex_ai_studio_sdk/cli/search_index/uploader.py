from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Literal

from yandex_ai_studio_sdk import AsyncAIStudio
from yandex_ai_studio_sdk._files.file import AsyncFile
from yandex_ai_studio_sdk._logging import get_logger
from yandex_ai_studio_sdk._search_indexes.index_type import BaseSearchIndexType
from yandex_ai_studio_sdk._search_indexes.search_index import AsyncSearchIndex
from yandex_ai_studio_sdk._types.misc import UNDEFINED

from .constants import (
    BYTES_PER_MB, DEFAULT_MAX_WORKERS, DEFAULT_POLL_TIMEOUT, DEFAULT_SKIP_ON_ERROR, MAX_FILES_PER_INDEX_CREATE
)
from .file_sources.base import BaseFileSource, FileMetadata

logger = get_logger(__name__)


@dataclass
class UploadConfig:
    """
    Configuration for file upload and search index creation.

    This config is used by the legacy Yandex SDK uploader.
    TODO: Replace with OpenAI API client when migrating.
    """

    # File upload settings
    file_ttl_days: int | None = None
    """Time-to-live for uploaded files in days"""

    file_expiration_policy: Literal["static", "since_last_active"] | None = None
    """Expiration policy for files ('static' or 'since_last_active')"""

    file_labels: dict[str, str] | None = None
    """Labels to attach to all uploaded files (not in OpenAI API)"""

    # Search index settings
    index_name: str | None = None
    """Name for the search index"""

    index_description: str | None = None
    """Description for the search index (not in OpenAI API)"""

    index_labels: dict[str, str] | None = None
    """Labels to attach to the search index (metadata in OpenAI)"""

    index_ttl_days: int | None = None
    """Time-to-live for the search index in days"""

    index_expiration_policy: Literal["static", "since_last_active"] | None = None
    """Expiration policy for the index ('static' or 'since_last_active')"""

    index_type: BaseSearchIndexType | None = None
    """Type of search index to create (chunking_strategy in OpenAI)"""

    # Upload behavior settings
    skip_on_error: bool = DEFAULT_SKIP_ON_ERROR
    """Whether to skip files that fail to upload instead of stopping"""

    max_concurrent_uploads: int = DEFAULT_MAX_WORKERS
    """Maximum number of concurrent upload tasks"""

    poll_timeout: int = DEFAULT_POLL_TIMEOUT
    """Timeout in seconds for waiting on index creation operation"""



@dataclass
class UploadStats:
    """Statistics about the upload process."""

    total_files: int = 0
    """Total number of files processed"""

    uploaded_files: int = 0
    """Number of files successfully uploaded"""

    failed_files: int = 0
    """Number of files that failed to upload"""

    skipped_files: int = 0
    """Number of files skipped"""

    total_bytes: int = 0
    """Total bytes uploaded"""


class AsyncSearchIndexUploader:
    """Asynchronous uploader for creating search indexes from various file sources."""

    def __init__(
        self,
        sdk: AsyncAIStudio,
        config: UploadConfig,
    ):
        self.sdk = sdk
        self.config = config
        self.stats = UploadStats()

    async def upload_from_source(
        self,
        source: BaseFileSource,
    ) -> AsyncSearchIndex:
        """
        Upload files from a source and create a search index.

        :param source: File source to upload from.
        """
        logger.info("Starting upload from source: %s", source.__class__.__name__)

        # Upload files
        uploaded_files = await self._upload_files(source)
        if not uploaded_files:
            raise ValueError("No files were uploaded successfully")
        logger.info("Uploaded %d files, creating search index...", len(uploaded_files))

        # Create search index
        search_index = await self._create_search_index(uploaded_files)

        logger.info("Search index created successfully: %s", search_index.id)
        self._log_stats()
        return search_index

    async def _upload_files(self, source: BaseFileSource) -> list[AsyncFile]:
        """
        Upload all files from the source with concurrent execution.

        :param source: File source to upload from.
        """
        # Collect file metadata only (not content)
        files_metadata = await source.list_files()
        self.stats.total_files = len(files_metadata)

        if len(files_metadata) > MAX_FILES_PER_INDEX_CREATE:
            raise ValueError(
                f"Too many files ({len(files_metadata)}), "
                f"maximum {MAX_FILES_PER_INDEX_CREATE} files per index creation request."
            )

        if not files_metadata:
            logger.warning("No files to upload")
            return []

        semaphore = asyncio.Semaphore(self.config.max_concurrent_uploads)

        # Create upload tasks that will read file content on-demand
        tasks = [
            self._upload_single_file_on_demand(file_metadata, source, semaphore)
            for file_metadata in files_metadata
        ]

        results_to_process: list[AsyncFile | BaseException | None]
        results_to_process = list(await asyncio.gather(*tasks, return_exceptions=True))

        uploaded_files: list[AsyncFile] = []
        for i, result in enumerate(results_to_process):
            file_metadata = files_metadata[i]

            if isinstance(result, BaseException):
                logger.error("Upload failed for %s: %s", file_metadata.path, result)
                self.stats.failed_files += 1
                if not self.config.skip_on_error:
                    raise result from result
            elif result is not None:
                assert isinstance(result, AsyncFile), (
                    f"Expected AsyncFile, got {type(result)}: {result}"
                )
                uploaded_files.append(result)
                self.stats.uploaded_files += 1
                logger.debug(
                    "Uploaded file %s (%d/%d)",
                    file_metadata.name,
                    self.stats.uploaded_files,
                    len(files_metadata),
                )
            else:
                # result is None: file was skipped due to skip_on_error=True
                self.stats.skipped_files += 1

        logger.info(
            "Upload completed: %d succeeded, %d failed, %d skipped",
            self.stats.uploaded_files,
            self.stats.failed_files,
            self.stats.skipped_files,
        )
        return uploaded_files

    async def _upload_single_file_on_demand(
        self,
        file_metadata: FileMetadata,
        source: BaseFileSource,
        semaphore: asyncio.Semaphore,
    ) -> AsyncFile | None:
        """
        Upload a single file by reading its content on-demand.

        :param file_metadata: Metadata about the file.
        :param source: File source to read content from.
        :param semaphore: Semaphore to limit concurrent uploads.
        """
        async with semaphore:
            try:
                content = await source.get_file_content(file_metadata)
                self.stats.total_bytes += len(content)
            except Exception as e:
                logger.error("Failed to read file %s: %s", file_metadata.path, e)
                if not self.config.skip_on_error:
                    raise
                return None

            return await self._upload_single_file(file_metadata, content)

    async def _upload_single_file(self, file_metadata: FileMetadata, content: bytes) -> AsyncFile | None:
        """
        Upload a single file to Yandex Cloud.

        :param file_metadata: Metadata about the file.
        :param content: File content as bytes.
        """
        try:
            labels = {}
            if self.config.file_labels:
                labels.update(self.config.file_labels)
            if file_metadata.labels:
                labels.update(file_metadata.labels)

            uploaded_file = await self.sdk.files.upload_bytes(
                content,
                name=file_metadata.name if file_metadata.name else UNDEFINED,
                mime_type=file_metadata.mime_type if file_metadata.mime_type else UNDEFINED,
                ttl_days=self.config.file_ttl_days if self.config.file_ttl_days is not None else UNDEFINED,
                expiration_policy=(
                    self.config.file_expiration_policy if self.config.file_expiration_policy else UNDEFINED
                ),
                labels=labels if labels else UNDEFINED,
            )

            logger.debug("Successfully uploaded file: %s (id: %s)", file_metadata.name, uploaded_file.id)
            return uploaded_file

        except Exception as e:
            logger.error("Failed to upload file %s: %s", file_metadata.name, e)
            if not self.config.skip_on_error:
                raise
            return None

    async def _create_search_index(self, files: list[AsyncFile]) -> AsyncSearchIndex:
        """
        Create a search index from uploaded files.

        :param files: List of uploaded File objects.
        """
        logger.info("Creating search index with %d files...", len(files))

        # Create search index using deferred operation
        operation = await self.sdk.search_indexes.create_deferred(
            files=files,
            index_type=self.config.index_type if self.config.index_type else UNDEFINED,
            name=self.config.index_name if self.config.index_name else UNDEFINED,
            description=self.config.index_description if self.config.index_description else UNDEFINED,
            labels=self.config.index_labels if self.config.index_labels else UNDEFINED,
            ttl_days=self.config.index_ttl_days if self.config.index_ttl_days is not None else UNDEFINED,
            expiration_policy=self.config.index_expiration_policy if self.config.index_expiration_policy else UNDEFINED,
        )

        logger.info("Search index creation started, waiting for completion...")

        search_index = await operation.wait(poll_timeout=self.config.poll_timeout)

        logger.info("Search index created successfully: %s", search_index.id)
        return search_index

    def _log_stats(self) -> None:
        """Log upload statistics."""
        logger.info("Upload statistics:")
        logger.info("  Total files: %d", self.stats.total_files)
        logger.info("  Uploaded: %d", self.stats.uploaded_files)
        logger.info("  Failed: %d", self.stats.failed_files)
        logger.info("  Skipped: %d", self.stats.skipped_files)
        logger.info(
            "  Total bytes: %d (%.2f MB)",
            self.stats.total_bytes,
            self.stats.total_bytes / BYTES_PER_MB,
        )
