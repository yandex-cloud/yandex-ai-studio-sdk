from __future__ import annotations

import os
from pathlib import Path
from typing import Union

import aiofiles
from yandex_ai_studio_sdk._logging import get_logger
from yandex_ai_studio_sdk._types.misc import PathLike, coerce_path
from yandex_ai_studio_sdk.cli.search_index.file_sources.base import BaseFileSource, FileMetadata

logger = get_logger(__name__)

PathsInput = Union[PathLike, list[PathLike]]


class LocalFileSource(BaseFileSource):
    """Source for loading files from local filesystem."""

    def __init__(
        self,
        paths: PathsInput,
        *,
        max_file_size: int | None = None,
    ):
        """
        Initialize local file source.

        :param paths: One path or a list of paths. Shell glob expansion is handled by the caller (bash).
        :param max_file_size: Maximum file size in bytes (larger files will be skipped).
        """
        if isinstance(paths, (str, os.PathLike)):
            self.paths = [coerce_path(paths)]
        else:
            self.paths = [coerce_path(p) for p in paths]

        self.max_file_size = max_file_size

    async def list_files(self) -> list[FileMetadata]:
        """List all files from provided paths."""
        seen: set[Path] = set()
        result: list[FileMetadata] = []

        for path in self.paths:
            if path.is_file():
                candidates: list[Path] = [path]
            elif path.is_dir():
                raise ValueError(
                    f"Directories are not supported: {path}. Please provide individual files."
                )
            else:
                raise FileNotFoundError(f"Path does not exist or is not accessible: {path}")

            for file_path in candidates:
                if file_path in seen:
                    continue
                seen.add(file_path)

                if self.max_file_size:
                    size = file_path.stat().st_size
                    if size > self.max_file_size:
                        logger.warning(
                            "Skipping file (too large): %s (%d bytes > %d max)",
                            file_path, size, self.max_file_size,
                        )
                        continue

                result.append(FileMetadata(path=file_path, name=file_path.name))

        logger.info("Finished scanning: %d unique files found", len(result))
        return result

    async def get_file_content(self, file_metadata: FileMetadata) -> bytes:
        """Read file content from the local filesystem."""
        file_path = Path(file_metadata.path)
        try:
            async with aiofiles.open(file_path, "rb") as f:
                return await f.read()
        except OSError as e:
            logger.error("Failed to read file: %s - %s", file_path, e)
            raise
