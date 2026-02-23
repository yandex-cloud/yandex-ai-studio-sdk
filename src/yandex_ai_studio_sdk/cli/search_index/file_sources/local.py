from __future__ import annotations

import asyncio
import os
from collections.abc import Iterator
from pathlib import Path

from yandex_ai_studio_sdk._logging import get_logger
from yandex_ai_studio_sdk._types.misc import PathLike, coerce_path
from yandex_ai_studio_sdk.cli.search_index.file_sources.base import BaseFileSource, FileMetadata

logger = get_logger(__name__)

# Accepts a single path or a list of paths
PathsInput = PathLike | list[PathLike]


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

        Args:
            paths: One path or a list of paths (files or directories).
                   Directories are scanned recursively.
                   Shell glob expansion is handled by the caller (bash).
            max_file_size: Maximum file size in bytes (larger files will be skipped)
        """
        if isinstance(paths, (str, os.PathLike)):
            self.paths = [coerce_path(paths)]
        else:
            self.paths = [coerce_path(p) for p in paths]

        self.max_file_size = max_file_size

    def list_files(self) -> Iterator[FileMetadata]:
        """List all files from provided paths."""
        seen: set[Path] = set()

        for path in self.paths:
            if path.is_file():
                candidates: Iterator[Path] = iter([path])
            elif path.is_dir():
                candidates = path.rglob("*")
            else:
                logger.warning("Path does not exist or is not accessible: %s", path)
                continue

            for file_path in candidates:
                if not file_path.is_file():
                    continue
                if file_path in seen:
                    continue
                seen.add(file_path)

                if self.max_file_size:
                    try:
                        size = file_path.stat().st_size
                        if size > self.max_file_size:
                            logger.warning(
                                "Skipping file (too large): %s (%d bytes > %d max)",
                                file_path, size, self.max_file_size,
                            )
                            continue
                    except OSError as e:
                        logger.error("Cannot access file: %s - %s", file_path, e)
                        continue

                yield FileMetadata(path=file_path, name=file_path.name)

        logger.info("Finished scanning: %d unique files found", len(seen))

    async def get_file_content(self, file_metadata: FileMetadata) -> bytes:
        """Read file content from the local filesystem."""
        file_path = Path(file_metadata.path)
        try:
            return await asyncio.to_thread(file_path.read_bytes)
        except OSError as e:
            logger.error("Failed to read file: %s - %s", file_path, e)
            raise

    def get_file_count_estimate(self) -> int | None:
        """Count files across all provided paths."""
        try:
            seen: set[Path] = set()
            for path in self.paths:
                candidates = iter([path]) if path.is_file() else path.rglob("*")
                for f in candidates:
                    if f.is_file() and f not in seen:
                        seen.add(f)
            return len(seen)
        except Exception as e:
            logger.warning("Failed to count files: %s", e)
            return None
