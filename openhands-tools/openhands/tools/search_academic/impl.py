"""Search executor implementation."""

import asyncio
import logging
import os
from typing import Optional

from openhands.sdk.tool import ToolExecutor

from openhands.tools.search_academic.definition import SearchAction, SearchObservation
from openhands.tools.search_academic.engines import (
    ArxivSearchEngine,
    ScholarSearchEngine,
    SerperSearchEngine,
)

logger = logging.getLogger(__name__)


class SearchExecutor(ToolExecutor[SearchAction, SearchObservation]):
    """Executor for academic search tool."""

    def __init__(
        self,
        serper_api_key: Optional[str] = None,
        scholar_api_key: Optional[str] = None,
        timeout: int = 30,
        **kwargs,
    ):
        """Initialize search executor.

        Args:
            serper_api_key: API key for Serper search engine
            scholar_api_key: API key for Semantic Scholar search engine
            timeout: Request timeout in seconds
            **kwargs: Additional parameters (ignored)
        """
        self.serper_api_key = serper_api_key or os.getenv("SERPER_API_KEY")
        self.scholar_api_key = scholar_api_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        self.timeout = timeout

        self.engines = {
            "serper": SerperSearchEngine(
                api_key=self.serper_api_key, timeout=timeout
            ),
            "scholar": ScholarSearchEngine(
                api_key=self.scholar_api_key, timeout=timeout
            ),
            "arxiv": ArxivSearchEngine(timeout=timeout),
        }

    async def __call__(
        self,
        action: SearchAction,
        conversation=None,
    ) -> SearchObservation:
        """Execute search action.

        Args:
            action: Search action with query and engines
            conversation: Optional conversation context (unused)

        Returns:
            Search observation with results
        """
        try:
            # Determine which engines to use (default to serper only for stability)
            engines_to_use = action.engines or ["serper"]

            # Run searches concurrently
            results_list = await asyncio.gather(
                *[
                    self.engines[engine_name].search(
                        action.query, action.max_results
                    )
                    for engine_name in engines_to_use
                    if engine_name in self.engines
                ],
                return_exceptions=True,
            )

            # Aggregate results and deduplicate by URL
            seen_urls = set()
            aggregated_results = []

            for result in results_list:
                if isinstance(result, Exception):
                    logger.warning(f"Search engine failed: {result}")
                    continue

                for item in result.results:
                    if item.url not in seen_urls:
                        seen_urls.add(item.url)
                        aggregated_results.append(
                            {
                                "title": item.title,
                                "url": item.url,
                                "source": item.source,
                                "snippet": item.snippet,
                                "authors": item.authors,
                                "published_date": (
                                    item.published_date.isoformat()
                                    if item.published_date
                                    else None
                                ),
                                "relevance_score": item.relevance_score,
                            }
                        )

            # Sort by relevance score
            aggregated_results.sort(
                key=lambda x: x.get("relevance_score", 0), reverse=True
            )

            # Limit to max_results
            aggregated_results = aggregated_results[: action.max_results]

            return SearchObservation(
                search_results=aggregated_results,
                total_found=len(aggregated_results),
                query=action.query,
                engines_used=engines_to_use,
            )

        except Exception as e:
            logger.error(f"Search execution failed: {e}")
            return SearchObservation(
                search_results=[],
                total_found=0,
                query=action.query,
                engines_used=action.engines or ["serper"],
                is_error=True,
                error=str(e),
            )
