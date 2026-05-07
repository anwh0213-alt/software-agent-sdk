"""Search executor implementation."""

import asyncio
import logging
import os
from typing import ClassVar

from openhands.sdk.tool import ToolExecutor
from openhands.tools.search_academic.definition import SearchAction, SearchObservation
from openhands.tools.search_academic.engines.base import (
    ArxivSearchEngine,
    BaseSearchEngine,
    ScholarSearchEngine,
    SerperSearchEngine,
)


logger = logging.getLogger(__name__)


class SearchExecutor(ToolExecutor[SearchAction, SearchObservation]):
    """Executor for academic search tool."""

    _ENGINE_REGISTRY: ClassVar[dict[str, type[BaseSearchEngine]]] = {
        "arxiv": ArxivSearchEngine,
        "scholar": ScholarSearchEngine,
        "serper": SerperSearchEngine,
    }

    def __init__(
        self,
        engines: list[str] | None = None,
        timeout: int = 30,
        engine_params: dict[str, dict] | None = None,
    ):
        """Initialize search executor.

        Args:
            engines: List of engine names to enable. Defaults to all registered engines.
            timeout: Request timeout in seconds
            engine_params: Per-engine config overrides, e.g.
                {"arxiv": {"timeout": 60}, "serper": {"api_key": "sk-..."}}
            **kwargs: Additional parameters (ignored)
        """
        self.timeout = timeout

        engine_names = (
            list(self._ENGINE_REGISTRY.keys()) if engines is None else engines
        )

        env_defaults = {
            "scholar": {"api_key": os.getenv("SEMANTIC_SCHOLAR_API_KEY")},
            "serper": {"api_key": os.getenv("SERPER_API_KEY")},
        }
        custom_params = engine_params or {}

        self.engines: dict[str, BaseSearchEngine] = {}
        for name in engine_names:
            engine_cls = self._ENGINE_REGISTRY.get(name)
            if engine_cls is None:
                logger.warning(f"Unknown engine: {name}, skipping")
                continue
            params = {
                "timeout": timeout,
                **env_defaults.get(name, {}),
                **custom_params.get(name, {}),
            }
            self.engines[name] = engine_cls(**params)

    async def __call__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        action: SearchAction,
        _conversation: object = None,
    ) -> SearchObservation:
        try:
            engines_to_use = action.engines or list(self.engines.keys())

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

            seen_urls: set[str] = set()
            aggregated_results: list[dict] = []

            for result in results_list:
                if isinstance(result, BaseException):
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

            aggregated_results.sort(
                key=lambda x: x.get("relevance_score", 0), reverse=True
            )

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
                engines_used=action.engines or list(self.engines.keys()),
            )
