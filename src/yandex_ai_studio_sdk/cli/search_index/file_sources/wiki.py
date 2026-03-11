from __future__ import annotations

import asyncio
from typing import Literal
from urllib.parse import urlparse

from yandex_ai_studio_sdk._logging import get_logger
from yandex_ai_studio_sdk._utils.packages import requires_package
from yandex_ai_studio_sdk.cli.search_index.file_sources.base import BaseFileSource, FileMetadata

WikiExportFormat = Literal["text", "html", "markdown"]

logger = get_logger(__name__)


class WikiFileSource(BaseFileSource):
    """Source for loading page content from MediaWiki instances."""

    @requires_package('mwclient', '>=0.10.1', 'WikiFileSource')
    def __init__(
        self,
        page_urls: list[str],
        *,
        username: str | None = None,
        password: str | None = None,
        export_format: WikiExportFormat = "text",
    ):
        import mwclient  # type: ignore[import-untyped,import-not-found]

        if not page_urls:
            raise ValueError("At least one page URL must be provided")

        self.page_urls = page_urls
        self.export_format = export_format

        # Extract site domain from first page URL
        parsed = urlparse(page_urls[0])
        path_prefix = parsed.path.split("/wiki/")[0]
        self.site = mwclient.Site(parsed.netloc, path=(path_prefix or "/w") + "/")

        if username and password:
            self.site.login(username, password)
            logger.debug("Logged in to wiki as %s", username)

        logger.info("WikiFileSource initialized for %s", parsed.netloc)

    def _parse_page_url(self, page_url: str) -> str:
        """
        Parse MediaWiki page URL and extract page title.

        Examples:
        - https://en.wikipedia.org/wiki/Machine_learning -> Machine_learning
        - https://en.wikipedia.org/wiki/Python_(programming_language) -> Python_(programming_language)
        """
        parsed = urlparse(page_url)
        path = parsed.path

        if "/wiki/" in path:
            title = path.split("/wiki/", 1)[1]
            return title

        raise ValueError(f"Unable to parse MediaWiki page URL: {page_url}")

    async def list_files(self) -> list[FileMetadata]:
        """List pages from MediaWiki by URL."""
        logger.info("Listing %d page(s) from wiki", len(self.page_urls))

        result = []
        for page_url in self.page_urls:
            page_title = self._parse_page_url(page_url)
            result.append(FileMetadata(
                path=page_title,
                name=page_title.replace("_", " "),
                mime_type=None,
                description=f"Wiki page: {page_title.replace('_', ' ')}",
            ))
        return result

    async def get_file_content(self, file_metadata: FileMetadata) -> bytes:
        """Get page content using mwclient."""
        return await asyncio.to_thread(self._get_file_content_sync, file_metadata)

    def _get_file_content_sync(self, file_metadata: FileMetadata) -> bytes:
        page_title = str(file_metadata.path)
        logger.debug("Getting content for page: %s", page_title)

        page = self.site.pages[page_title]

        if not page.exists:
            raise ValueError(f"Page not found: {page_title}")

        if self.export_format == "html":
            html_content = page.html()
            return html_content.encode("utf-8")
        else:
            result = self.site.api(
                "query",
                titles=page_title,
                prop="extracts",
                explaintext=True,
            )
            pages = result.get("query", {}).get("pages", {})
            page_data = next(iter(pages.values()))

            if "extract" not in page_data:
                raise ValueError(f"No content available for page: {page_title}")

            return page_data["extract"].encode("utf-8")
