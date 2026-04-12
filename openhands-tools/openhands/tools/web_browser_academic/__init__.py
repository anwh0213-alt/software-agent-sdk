"""Web browser tool for OpenHands SDK."""

from openhands.tools.web_browser_academic.definition import (
    WebBrowserAction,
    WebBrowserObservation,
    WebBrowserAcademicTool,
)
from openhands.tools.web_browser_academic.extractor import ContentExtractor
from openhands.tools.web_browser_academic.models import WebContent, WebPage
from openhands.tools.web_browser_academic.impl import WebBrowserExecutor

__all__ = [
    "WebBrowserAction",
    "WebBrowserObservation",
    "WebBrowserAcademicTool",
    "WebBrowserExecutor",
    "ContentExtractor",
    "WebContent",
    "WebPage",
]
