"""Web browser tool definition for OpenHands SDK."""

from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

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


TOOL_DESCRIPTION = """Fetch and extract content from web pages.

This tool can:
- Fetch web pages from URLs
- Extract plain text content
- Extract metadata (title, description, authors, etc.)
- Extract links from pages
- Handle errors and timeouts gracefully

Returns structured web page content suitable for analysis and summarization.
"""


class WebBrowserAction(Action):
    """Fetch and process web pages.

    Attributes:
        urls: List of URLs to fetch
        extract_metadata: Whether to extract metadata
        extract_links: Whether to extract links
        max_content_length: Maximum content length to return
    """

    urls: list[str] = Field(
        ...,
        description="List of URLs to fetch. For example: ['https://example.com/paper', 'https://arxiv.org/pdf/2023.12345']",
    )
    extract_metadata: bool = Field(
        default=True,
        description="Whether to extract metadata (title, description, etc.)",
    )
    extract_links: bool = Field(
        default=False,
        description="Whether to extract all links from the page",
    )
    max_content_length: int = Field(
        default=10000,
        ge=100,
        description="Maximum content length to return (in characters)",
    )


class WebBrowserObservation(Observation):
    """Result of web browser operation.

    Attributes:
        fetched_pages: List of successfully fetched pages
        failed_urls: List of URLs that failed to fetch
        total_fetched: Number of successfully fetched pages
        total_requested: Number of URLs requested
    """

    fetched_pages: list[dict] = Field(
        default_factory=list,
        description="List of fetched pages with content",
    )
    failed_urls: list[str] = Field(
        default_factory=list,
        description="URLs that failed to fetch",
    )
    total_fetched: int = Field(
        default=0,
        description="Number of successfully fetched pages",
    )
    total_requested: int = Field(
        default=0,
        description="Number of URLs requested",
    )

    @property
    def to_llm_content(self) -> Sequence[TextContent]:
        """Convert observation to LLM-friendly format."""
        result_text = f"Web Content Extraction Results:\n"
        result_text += f"Successfully fetched: {self.total_fetched}/{self.total_requested}\n"

        if self.failed_urls:
            result_text += f"Failed URLs: {', '.join(self.failed_urls)}\n\n"

        for page in self.fetched_pages[:5]:  # Show first 5 pages
            result_text += f"URL: {page.get('url', 'N/A')}\n"
            result_text += f"Title: {page.get('title', 'N/A')}\n"

            # Truncate content for LLM
            content = page.get("text", "")
            if len(content) > 500:
                content = content[:500] + "...\n[Content truncated]"

            result_text += f"Content:\n{content}\n\n"

        return [TextContent(text=result_text)]


class WebBrowserAcademicTool(ToolDefinition[WebBrowserAction, WebBrowserObservation]):
    """Tool definition for web browsing and content extraction."""

    name = "web_browser_academic"

    @classmethod
    def create(
        cls,
        conv_state: "ConversationState",
        **params,
    ) -> Sequence["WebBrowserAcademicTool"]:
        """Create tool instance.

        Args:
            conv_state: Conversation state
            **params: Additional parameters (timeout, max_concurrent, etc.)

        Returns:
            Sequence of tool instances
        """
        from openhands.tools.web_browser_academic.impl import WebBrowserExecutor

        executor = WebBrowserExecutor(**params)

        return [
            cls(
                description=TOOL_DESCRIPTION,
                action_type=WebBrowserAction,
                observation_type=WebBrowserObservation,
                annotations=ToolAnnotations(
                    title="web_browser_academic",
                    readOnlyHint=True,
                    destructiveHint=False,
                    idempotentHint=True,
                    openWorldHint=True,
                ),
                executor=executor,
            )
        ]


# Register tool at module import
register_tool(WebBrowserAcademicTool.name, WebBrowserAcademicTool)
