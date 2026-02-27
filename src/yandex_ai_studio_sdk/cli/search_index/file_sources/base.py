from __future__ import annotations

import abc
from dataclasses import dataclass

from yandex_ai_studio_sdk._types.misc import PathLike


@dataclass
class FileMetadata:
    """Metadata about a file to be uploaded."""

    path: PathLike
    """Path or identifier of the file"""

    name: str | None = None
    """Display name for the file"""

    mime_type: str | None = None
    """MIME type of the file"""

    labels: dict[str, str] | None = None
    """Labels to attach to the file"""

    description: str | None = None
    """Description of the file"""


class BaseFileSource(abc.ABC):
    """
    Base class for file sources that can provide files for indexing.
    """

    @abc.abstractmethod
    async def list_files(self) -> list[FileMetadata]:
        """List all files available from this source."""

    @abc.abstractmethod
    async def get_file_content(self, file_metadata: FileMetadata) -> bytes:
        """Retrieve the content of a specific file."""
