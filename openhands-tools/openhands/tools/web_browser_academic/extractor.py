"""Content extraction utilities."""

import logging
import re

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ContentExtractor:
    """Extract and clean web content from HTML."""

    @staticmethod
    def extract_text(html: str) -> str:
        """Extract clean text from HTML.

        Args:
            html: Raw HTML content

        Returns:
            Extracted and cleaned text
        """
        try:
            soup = BeautifulSoup(html, "lxml")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Remove common non-content elements
            for element in soup(["nav", "footer", "header", "aside", "noscript"]):
                element.decompose()

            # Get text
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)

            return text
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return ""

    @staticmethod
    def extract_metadata(html: str) -> dict[str, str]:
        """Extract metadata from HTML.

        Args:
            html: Raw HTML content

        Returns:
            Dictionary of metadata
        """
        metadata: dict[str, str] = {}
        try:
            soup = BeautifulSoup(html, "lxml")

            # Extract title
            title_tag = soup.find("title")
            if title_tag:
                metadata["title"] = title_tag.get_text(strip=True)

            # Extract meta tags
            for meta_tag in soup.find_all("meta"):
                name_attr = meta_tag.get("name")
                name = str(name_attr).lower() if name_attr else ""
                content_attr = meta_tag.get("content")
                content = str(content_attr) if content_attr else ""
                if name and content:
                    metadata[name] = content

            # Extract Open Graph tags
            for og_tag in soup.find_all("meta", property=re.compile("og:")):
                property_attr = og_tag.get("property")
                property_name = str(property_attr).lower() if property_attr else ""
                content_attr = og_tag.get("content")
                content = str(content_attr) if content_attr else ""
                if property_name and content:
                    metadata[property_name] = content

        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")

        return metadata

    @staticmethod
    def extract_links(html: str) -> list[str]:
        """Extract all links from HTML.

        Args:
            html: Raw HTML content

        Returns:
            List of URLs found in the HTML
        """
        links: list[str] = []
        try:
            soup = BeautifulSoup(html, "lxml")
            for link in soup.find_all("a", href=True):
                href_attr = link.get("href")
                href = str(href_attr).strip() if href_attr else ""
                if href:
                    links.append(href)
        except Exception as e:
            logger.error(f"Link extraction failed: {e}")

        return links
