"""Base search engine implementation for academic paper search."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

import httpx

from openhands.tools.search_academic.models import SearchResponse, SearchResult

logger = logging.getLogger(__name__)


class BaseSearchEngine(ABC):
    """Abstract base class for search engines."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        """Initialize search engine.

        Args:
            api_key: Optional API key for the search engine
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout

    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> SearchResponse:
        """Search for academic papers.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            SearchResponse with results
        """
        pass

    @staticmethod
    @abstractmethod
    def parse_results(raw_response: dict[str, Any]) -> list[SearchResult]:
        """Parse raw API response to SearchResult objects.

        Args:
            raw_response: Raw response from API

        Returns:
            List of SearchResult objects
        """
        pass

    async def _fetch_with_retry(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, Any]] = None,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """Fetch data from URL with retry logic.

        Args:
            url: URL to fetch
            headers: Optional HTTP headers
            params: Optional query parameters
            max_retries: Maximum number of retries

        Returns:
            Parsed JSON response

        Raises:
            Exception: If all retries fail
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, headers=headers, params=params)
                    response.raise_for_status()
                    return response.json()  # type: ignore

            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Fetch attempt {attempt + 1} failed: {e}. "
                    f"Retrying..." if attempt < max_retries - 1 else "Giving up."
                )

        if last_exception:
            raise last_exception
        raise RuntimeError("Failed to fetch data after retries")


class SerperSearchEngine(BaseSearchEngine):
    """Google Search via Serper API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        """Initialize Serper search engine.

        Note: API key should be set via SEARCH_ACADEMIC_SERPER_API_KEY environment variable
        """
        super().__init__(api_key=api_key, timeout=timeout)
        self.engine_name = "serper"
        self.api_endpoint = "https://google.serper.dev/search"

    async def search(self, query: str, max_results: int = 10) -> SearchResponse:
        """Search using Serper API.

        Args:
            query: Search query
            max_results: Maximum results to return

        Returns:
            SearchResponse with results
        """
        if not self.api_key:
            logger.warning(
                f"{self.engine_name} API key not configured. "
                "Set SEARCH_ACADEMIC_SERPER_API_KEY environment variable."
            )
            return SearchResponse(
                query=query,
                results=[],
                total_found=0,
                engine=self.engine_name,
                execution_time=0.0,
            )

        try:
            headers = {"X-API-KEY": self.api_key}
            params = {"q": query, "num": max_results}

            response_data: dict[str, Any] = await self._fetch_with_retry(
                self.api_endpoint,
                headers=headers,
                params=params,
            )

            results = self.parse_results(response_data)

            return SearchResponse(
                query=query,
                results=results[:max_results],
                total_found=len(results),
                engine=self.engine_name,
                execution_time=0.0,
            )
        except Exception as e:
            logger.error(f"Serper search failed: {e}")
            return SearchResponse(
                query=query,
                results=[],
                total_found=0,
                engine=self.engine_name,
                execution_time=0.0,
            )

    @staticmethod
    def parse_results(raw_response: dict[str, Any]) -> list[SearchResult]:
        """Parse Serper API response.

        Args:
            raw_response: Raw response from Serper API

        Returns:
            List of SearchResult objects
        """
        results = []
        for item in raw_response.get("organic", []):
            result = SearchResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                source="serper",
                snippet=item.get("snippet", ""),
                relevance_score=0.8,
            )
            results.append(result)
        return results


class ScholarSearchEngine(BaseSearchEngine):
    """Semantic Scholar search engine (free)."""

    def __init__(
        self,
        timeout: int = 30,
    ) -> None:
        """Initialize Semantic Scholar search engine."""
        super().__init__(api_key=None, timeout=timeout)
        self.engine_name = "scholar"
        self.api_endpoint = "https://api.semanticscholar.org/graph/v1/paper/search"

    async def search(self, query: str, max_results: int = 10) -> SearchResponse:
        """Search using Semantic Scholar API.

        Args:
            query: Search query
            max_results: Maximum results to return

        Returns:
            SearchResponse with results
        """
        try:
            params = {
                "query": query,
                "limit": max_results,
                "fields": "paperId,title,url,authors,publicationDate,abstract",
            }

            response_data: dict[str, Any] = await self._fetch_with_retry(
                self.api_endpoint,
                params=params,
            )

            results = self.parse_results(response_data)

            return SearchResponse(
                query=query,
                results=results[:max_results],
                total_found=len(results),
                engine=self.engine_name,
                execution_time=0.0,
            )
        except Exception as e:
            logger.error(f"Semantic Scholar search failed: {e}")
            return SearchResponse(
                query=query,
                results=[],
                total_found=0,
                engine=self.engine_name,
                execution_time=0.0,
            )

    @staticmethod
    def parse_results(raw_response: dict[str, Any]) -> list[SearchResult]:
        """Parse Semantic Scholar API response.

        Args:
            raw_response: Raw response from Semantic Scholar API

        Returns:
            List of SearchResult objects
        """
        results = []
        for item in raw_response.get("data", []):
            authors = [a.get("name", "") for a in item.get("authors", [])]
            result = SearchResult(
                title=item.get("title", ""),
                url=f"https://semanticscholar.org/paper/{item.get('paperId', '')}",
                source="scholar",
                authors=authors,
                relevance_score=0.85,
            )
            results.append(result)
        return results


class ArxivSearchEngine(BaseSearchEngine):
    """arXiv search engine (free)."""

    def __init__(
        self,
        timeout: int = 30,
    ) -> None:
        """Initialize arXiv search engine."""
        super().__init__(api_key=None, timeout=timeout)
        self.engine_name = "arxiv"
        self.api_endpoint = "http://export.arxiv.org/api/query"

    async def search(self, query: str, max_results: int = 10) -> SearchResponse:
        """Search using arXiv API.

        Args:
            query: Search query
            max_results: Maximum results to return

        Returns:
            SearchResponse with results
        """
        try:
            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": max_results,
                "sortBy": "relevance",
            }

            response_data: dict[str, Any] = await self._fetch_with_retry(
                self.api_endpoint,
                params=params,
            )

            results = self.parse_results(response_data)

            return SearchResponse(
                query=query,
                results=results[:max_results],
                total_found=len(results),
                engine=self.engine_name,
                execution_time=0.0,
            )
        except Exception as e:
            logger.error(f"arXiv search failed: {e}")
            return SearchResponse(
                query=query,
                results=[],
                total_found=0,
                engine=self.engine_name,
                execution_time=0.0,
            )

    @staticmethod
    def parse_results(raw_response: dict[str, Any]) -> list[SearchResult]:
        """Parse arXiv API response.

        Args:
            raw_response: Raw response from arXiv API (XML parsed as dict)

        Returns:
            List of SearchResult objects
        """
        # Note: arXiv returns XML, but for simplification we'll handle it later
        # For now, return empty results
        return []
