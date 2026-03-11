from __future__ import annotations

import re
from typing import Literal
from urllib.parse import parse_qs, urlparse

import httpx
from yandex_ai_studio_sdk._logging import get_logger
from yandex_ai_studio_sdk.cli.search_index.file_sources.base import BaseFileSource, FileMetadata

ConfluenceExportFormat = Literal["pdf", "html", "markdown"]

_CONFLUENCE_PATH_MARKERS = ("/spaces/", "/pages/", "/display/")

logger = get_logger(__name__)


class ConfluenceFileSource(BaseFileSource):
    """Source for loading page content from Atlassian Confluence."""

    def __init__(
        self,
        page_urls: list[str],
        base_url: str | None = None,
        username: str | None = None,
        api_token: str | None = None,
        *,
        export_format: ConfluenceExportFormat,
        verify_ssl: bool = True,
    ):
        if not page_urls:
            raise ValueError("At least one page URL must be provided")

        self.page_urls = page_urls
        self.export_format = export_format

        # Determine base URL
        if base_url:
            self.url = base_url.rstrip('/')
        else:
            self.url = self._extract_base_url(page_urls[0])
            logger.info("Extracted base URL: %s", self.url)

        # Validate ALL URLs against the base (regardless of how base was set)
        for page_url in page_urls:
            if not page_url.startswith(self.url):
                raise ValueError(f"Page URL {page_url} does not start with base URL {self.url}")

        auth = (username, api_token) if username and api_token else None
        self._client = httpx.AsyncClient(auth=auth, verify=verify_ssl)
        self._api_base = f"{self.url}/rest/api"
        self._wiki_base = self.url

        logger.info("ConfluenceFileSource initialized for %s", self.url)

    async def _get_page(self, page_id: str, expand: str = "") -> dict:
        """Fetch page data from Confluence REST API."""
        params: dict[str, str] = {}
        if expand:
            params["expand"] = expand
        response = await self._client.get(f"{self._api_base}/content/{page_id}", params=params)
        response.raise_for_status()
        return response.json()

    async def _export_page(self, page_id: str) -> bytes:
        """Export page via Confluence exportword endpoint."""
        response = await self._client.get(f"{self._wiki_base}/exportword", params={"pageId": page_id})
        response.raise_for_status()
        return response.content

    def _extract_base_url(self, page_url: str) -> str:
        """Extract Confluence root URL including context path.

        Finds everything before the first known Confluence path marker
        (/spaces/, /pages/, /display/), so the result naturally includes
        any context path (e.g. /wiki for Cloud, /confluence for on-premise).
        """
        parsed = urlparse(page_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        for marker in _CONFLUENCE_PATH_MARKERS:
            idx = parsed.path.find(marker)
            if idx != -1:
                return base + parsed.path[:idx]
        return base

    def _parse_page_id(self, page_url: str) -> str:
        """Extract page ID from Confluence URL."""
        parsed = urlparse(page_url)

        # Try query param: ?pageId=123456
        if "pageId" in parsed.query:
            return parse_qs(parsed.query)["pageId"][0]

        # Try path: /pages/123456/... or /spaces/SPACE/pages/123456/...
        match = re.search(r"/pages/(\d+)", parsed.path)
        if match:
            return match.group(1)

        raise ValueError(
            f"Could not extract page ID from URL: {page_url}. "
            "Expected format: /pages/123456 or ?pageId=123456"
        )

    async def list_files(self) -> list[FileMetadata]:
        """List pages from Confluence by URL."""
        logger.info("Listing %d page(s) from Confluence", len(self.page_urls))

        result = []
        for page_url in self.page_urls:
            page_id = self._parse_page_id(page_url)
            page_info = await self._get_page(page_id)
            title = page_info.get("title", page_id)

            result.append(FileMetadata(
                path=page_id,
                name=title,
                mime_type=None,
                description=f"Confluence page: {title}",
            ))
        return result

    async def get_file_content(self, file_metadata: FileMetadata) -> bytes:
        """Export page content from Confluence."""
        page_id = str(file_metadata.path)
        logger.debug("Exporting Confluence page ID %s as %s", page_id, self.export_format)

        if self.export_format == "pdf":
            return await self._export_page(page_id)

        expand_map: dict[str, str] = {"html": "body.view", "markdown": "body.storage"}
        expand = expand_map[self.export_format]

        page = await self._get_page(page_id, expand=expand)
        body_type = "view" if self.export_format == "html" else "storage"
        content = page.get("body", {}).get(body_type, {}).get("value", "")

        return content.encode("utf-8")
