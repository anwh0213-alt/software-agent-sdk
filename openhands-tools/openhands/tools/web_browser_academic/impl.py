"""Web browser executor implementation."""

import asyncio
import logging
from typing import Optional

import httpx
from openhands.sdk.tool import ToolExecutor

from openhands.tools.web_browser_academic.definition import (
    WebBrowserAction,
    WebBrowserObservation,
)
from openhands.tools.web_browser_academic.extractor import ContentExtractor

logger = logging.getLogger(__name__)


class WebBrowserExecutor(ToolExecutor[WebBrowserAction, WebBrowserObservation]):
    """Executor for web browser tool."""

    def __init__(
        self,
        timeout: int = 30,
        max_concurrent: int = 5,
        **kwargs,
    ):
        """Initialize web browser executor.

        Args:
            timeout: Request timeout in seconds
            max_concurrent: Maximum concurrent requests
            **kwargs: Additional parameters (ignored)
        """
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.extractor = ContentExtractor()

    async def __call__(
        self,
        action: WebBrowserAction,
        conversation=None,
    ) -> WebBrowserObservation:
        """Execute web browser action.

        Args:
            action: Web browser action with URLs to fetch
            conversation: Optional conversation context (unused)

        Returns:
            Web browser observation with results
        """
        try:
            # Limit concurrent requests with semaphore
            semaphore = asyncio.Semaphore(self.max_concurrent)

            async def fetch_with_semaphore(url: str):
                async with semaphore:
                    return await self._fetch_url(
                        url,
                        action.extract_metadata,
                        action.extract_links,
                        action.max_content_length,
                    )

            # Fetch all URLs concurrently
            results = await asyncio.gather(
                *[fetch_with_semaphore(url) for url in action.urls],
                return_exceptions=True,
            )

            # Process results
            fetched_pages = []
            failed_urls = []

            for url, result in zip(action.urls, results):
                if isinstance(result, Exception):
                    logger.warning(f"Failed to fetch {url}: {result}")
                    failed_urls.append(url)
                elif result:
                    fetched_pages.append(result)
                else:
                    failed_urls.append(url)

            return WebBrowserObservation(
                fetched_pages=fetched_pages,
                failed_urls=failed_urls,
                total_fetched=len(fetched_pages),
                total_requested=len(action.urls),
            )

        except Exception as e:
            logger.error(f"Web browser execution failed: {e}")
            return WebBrowserObservation(
                fetched_pages=[],
                failed_urls=action.urls,
                total_fetched=0,
                total_requested=len(action.urls),
                is_error=True,
                error=str(e),
            )

    async def _fetch_url(
        self,
        url: str,
        extract_metadata: bool,
        extract_links: bool,
        max_content_length: int,
    ) -> Optional[dict]:
        """Fetch a single URL and extract content.

        Args:
            url: URL to fetch
            extract_metadata: Whether to extract metadata
            extract_links: Whether to extract links
            max_content_length: Maximum content length

        Returns:
            Dictionary with page content or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()

                html = response.text

                # Extract content
                text = self.extractor.extract_text(html)

                # Truncate if necessary
                if len(text) > max_content_length:
                    text = text[:max_content_length] + "\n[Content truncated]"

                result = {
                    "url": url,
                    "text": text,
                    "html": html,
                }

                # Extract metadata if requested
                if extract_metadata:
                    metadata = self.extractor.extract_metadata(html)
                    result["title"] = metadata.get("title")
                    result["metadata"] = metadata
                else:
                    result["title"] = None
                    result["metadata"] = {}

                # Extract links if requested
                if extract_links:
                    links = self.extractor.extract_links(html)
                    result["links"] = links
                else:
                    result["links"] = []

                return result

        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
