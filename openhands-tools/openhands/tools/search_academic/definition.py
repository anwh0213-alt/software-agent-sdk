"""Search academic tool definition for OpenHands SDK."""

from collections.abc import Sequence
from typing import TYPE_CHECKING

from pydantic import Field

if TYPE_CHECKING:
    from openhands.sdk.conversation.state import ConversationState

from openhands.sdk.llm import TextContent
from openhands.sdk.tool import (
    Action,
    Observation,
    ToolAnnotations,
    ToolDefinition,
    ToolExecutor,
    register_tool,
)

from openhands.tools.search_academic.models import SearchResponse


TOOL_DESCRIPTION = """Search academic papers from multiple sources.

This tool searches for academic papers using various search engines including:
- Semantic Scholar (free, academic papers)
- arXiv (free, preprints in computer science and related fields)
- Serper (requires API key for Google Search)

Returns structured search results with title, URL, authors, publication date, and relevance score.
"""


class SearchAction(Action):
    """Search for academic papers.

    Attributes:
        query: The search query string
        engines: List of search engines to use (e.g., ['scholar', 'arxiv', 'serper'])
        max_results: Maximum number of results to return (1-100)
    """

    query: str = Field(
        ...,
        description="The search query string. For example: 'machine learning', 'deep learning transformers'",
    )
    engines: list[str] = Field(
        default_factory=lambda: ["scholar", "arxiv"],
        description="List of search engines to use. Available: 'scholar' (Semantic Scholar), 'arxiv' (arXiv), 'serper' (requires API key)",
    )
    max_results: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results to return",
    )


class SearchObservation(Observation):
    """Result of a search operation.

    Attributes:
        search_results: The list of search results
        total_found: Total number of results found
        query: The original search query
        engines_used: Which search engines were used
    """

    search_results: list[dict[str, str | float | list[str] | None]] = Field(
        default_factory=list,
        description="List of search results with title, url, source, authors, etc.",
    )
    total_found: int = Field(
        default=0,
        description="Total number of results found",
    )
    query: str = Field(
        ...,
        description="The original search query",
    )
    engines_used: list[str] = Field(
        default_factory=list,
        description="Search engines that were used",
    )

    @property
    def to_llm_content(self) -> Sequence[TextContent]:
        """Convert observation to LLM-friendly format."""
        result_text = f"Search Results for '{self.query}':\n"
        result_text += f"Total found: {self.total_found}\n"
        result_text += f"Engines used: {', '.join(self.engines_used)}\n\n"

        for i, result in enumerate(self.search_results[:10], 1):  # Show first 10
            result_text += f"{i}. {result.get('title', 'N/A')}\n"
            result_text += f"   URL: {result.get('url', 'N/A')}\n"
            result_text += f"   Source: {result.get('source', 'N/A')}\n"
            if result.get("authors"):
                result_text += f"   Authors: {', '.join(result['authors'])}\n"
            result_text += f"   Relevance: {result.get('relevance_score', 0.5)}\n\n"

        return [TextContent(text=result_text)]


class SearchAcademicTool(ToolDefinition[SearchAction, SearchObservation]):
    """Tool definition for academic search."""

    name = "search_academic"

    @classmethod
    def create(
        cls,
        conv_state: "ConversationState",
        **params: dict,
    ) -> Sequence["SearchAcademicTool"]:
        """Create tool instance.

        Args:
            conv_state: Conversation state
            **params: Additional parameters (e.g., serper_api_key)

        Returns:
            Sequence of tool instances
        """
        from openhands.tools.search_academic.impl import SearchExecutor

        executor = SearchExecutor(**params)

        return [
            cls(
                description=TOOL_DESCRIPTION,
                action_type=SearchAction,
                observation_type=SearchObservation,
                annotations=ToolAnnotations(
                    title="search_academic",
                    readOnlyHint=True,
                    destructiveHint=False,
                    idempotentHint=True,
                    openWorldHint=True,
                ),
                executor=executor,
            )
        ]


# Register tool at module import
register_tool(SearchAcademicTool.name, SearchAcademicTool)
