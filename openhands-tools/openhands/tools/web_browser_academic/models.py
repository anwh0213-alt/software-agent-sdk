"""Data models for web browser tool."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class WebContent(BaseModel):
    """Web page content extracted from HTML."""

    url: str = Field(..., description="URL of the web page")
    title: Optional[str] = Field(
        default=None,
        description="Title of the web page",
    )
    text: str = Field(
        ...,
        min_length=1,
        description="Extracted plain text content",
    )
    html: Optional[str] = Field(
        default=None,
        description="Original HTML content",
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Extracted metadata (title, description, authors, etc.)",
    )
    extracted_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of extraction",
    )


class WebPage(BaseModel):
    """Web page with parsing status."""

    url: str = Field(..., description="URL of the web page")
    content: WebContent = Field(..., description="Extracted content")
    parse_success: bool = Field(
        default=True,
        description="Whether parsing was successful",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if parsing failed",
    )
