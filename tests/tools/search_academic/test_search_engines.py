"""Integration tests for academic search engines.

These tests verify that each search engine can successfully
connect to and retrieve results from its respective API.

Run with: pytest tests/tools/search_academic/test_search_engines.py -v
"""

import os
import sys

# Add the openhands-tools package to path
_repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.join(_repo_root, "openhands-tools"))

import pytest

from openhands.tools.search_academic.engines import (
    ScholarSearchEngine,
    ArxivSearchEngine,
    SerperSearchEngine,
)


from tests.tools.search_academic.conftest import require_env


class TestScholarSearchEngine:
    """Integration tests for Semantic Scholar search engine."""

    @pytest.mark.asyncio
    async def test_search_with_api_key(self):
        """Test that Scholar search returns non-empty results with API key."""
        api_key = require_env("SEMANTIC_SCHOLAR_API_KEY")

        engine = ScholarSearchEngine(api_key=api_key, timeout=30)
        response = await engine.search("machine learning", max_results=5)

        assert response.engine == "scholar"
        assert response.total_found > 0, "Semantic Scholar API should return results"
        assert len(response.results) > 0
        print(f"\n✓ Scholar returned {len(response.results)} results")

    @pytest.mark.asyncio
    async def test_search_result_structure(self):
        """Test that search results have required fields."""
        api_key = require_env("SEMANTIC_SCHOLAR_API_KEY")

        engine = ScholarSearchEngine(api_key=api_key, timeout=30)
        response = await engine.search("transformer attention", max_results=3)

        assert response.total_found > 0, "Semantic Scholar API should return results"
        assert len(response.results) > 0
        result = response.results[0]

        assert result.title
        assert result.url
        assert result.source == "scholar"
        print(f"\n✓ Result structure valid: {result.title[:50]}...")


class TestArxivSearchEngine:
    """Integration tests for arXiv search engine."""

    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        """Test that arXiv search returns non-empty results."""
        engine = ArxivSearchEngine(timeout=30)
        response = await engine.search("machine learning", max_results=5)

        assert response.engine == "arxiv"
        assert response.total_found > 0, "arXiv API should return results"
        assert len(response.results) > 0
        print(f"\n✓ ArXiv search completed, total found: {response.total_found}")
        print(f"  Results count: {len(response.results)}")

    @pytest.mark.asyncio
    async def test_search_result_structure(self):
        """Test that search results have required fields."""
        engine = ArxivSearchEngine(timeout=30)
        response = await engine.search("neural networks", max_results=3)

        assert response.total_found > 0, "arXiv API should return results"
        assert len(response.results) > 0
        result = response.results[0]
        assert result.title
        assert result.url
        assert result.source == "arxiv"
        print(f"\n✓ ArXiv returned {len(response.results)} parsed results")
        print(f"  First result: {result.title[:50]}...")


class TestSerperSearchEngine:
    """Integration tests for Serper (Google) search engine."""

    @pytest.mark.asyncio
    async def test_search_with_api_key(self):
        """Test Serper search with valid API key."""
        api_key = require_env("SERPER_API_KEY")

        engine = SerperSearchEngine(api_key=api_key, timeout=30)
        response = await engine.search("machine learning", max_results=5)

        assert response.engine == "serper"
        assert response.total_found > 0, "Serper API should return results with valid API key"
        assert len(response.results) > 0
        print(f"\n✓ Serper returned {len(response.results)} results")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
