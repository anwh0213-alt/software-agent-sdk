"""Tests for SearchExecutor engine configuration and E2E behavior."""

import pytest

from openhands.tools.search_academic.definition import SearchAction
from openhands.tools.search_academic.impl import SearchExecutor
from tests.tools.search_academic.conftest import require_env


class TestSearchExecutorEngineSelection:
    def test_default_creates_all_engines(self):
        executor = SearchExecutor()
        assert set(executor.engines.keys()) == {"serper", "scholar", "arxiv"}

    @pytest.mark.parametrize(
        "engines,expected",
        [
            (["arxiv"], {"arxiv"}),
            (["arxiv", "scholar"], {"arxiv", "scholar"}),
            (["arxiv", "nonexistent"], {"arxiv"}),
            ([], set()),
        ],
    )
    def test_engine_selection(self, engines, expected):
        executor = SearchExecutor(engines=engines)
        assert set(executor.engines.keys()) == expected


class TestSearchExecutorEngineParams:
    @pytest.mark.parametrize(
        "engine_name,param_key,override_value",
        [
            ("arxiv", "timeout", 99),
            ("serper", "api_key", "override_key"),
        ],
    )
    def test_engine_params_overrides_defaults(self, engine_name, param_key, override_value):
        executor = SearchExecutor(
            engines=[engine_name],
            timeout=10,
            engine_params={engine_name: {param_key: override_value}},
        )
        assert getattr(executor.engines[engine_name], param_key) == override_value

    def test_engine_params_does_not_affect_other_engines(self):
        executor = SearchExecutor(
            engines=["arxiv", "scholar"],
            timeout=10,
            engine_params={"arxiv": {"timeout": 99}},
        )
        assert executor.engines["arxiv"].timeout == 99
        assert executor.engines["scholar"].timeout == 10


class TestSearchExecutorE2E:
    @pytest.mark.asyncio
    async def test_arxiv_returns_results(self):
        executor = SearchExecutor(engines=["arxiv"])
        result = await executor(
            SearchAction(query="machine learning", engines=["arxiv"], max_results=3)
        )
        assert not result.is_error
        assert result.total_found > 0
        assert all(r["source"] == "arxiv" for r in result.search_results)

    @pytest.mark.asyncio
    async def test_scholar_returns_results(self):
        require_env("SEMANTIC_SCHOLAR_API_KEY")
        executor = SearchExecutor(engines=["scholar"])
        result = await executor(
            SearchAction(query="machine learning", engines=["scholar"], max_results=3)
        )
        assert not result.is_error
        assert result.total_found > 0
        assert all(r["source"] == "scholar" for r in result.search_results)

    @pytest.mark.asyncio
    async def test_serper_returns_results(self):
        require_env("SERPER_API_KEY")
        executor = SearchExecutor(engines=["serper"])
        result = await executor(
            SearchAction(query="machine learning", engines=["serper"], max_results=3)
        )
        assert not result.is_error
        assert result.total_found > 0
        assert all(r["source"] == "serper" for r in result.search_results)

    @pytest.mark.asyncio
    async def test_action_engines_filters_execution(self):
        executor = SearchExecutor(engines=["arxiv", "scholar"])
        result = await executor(
            SearchAction(query="deep learning", engines=["arxiv"], max_results=3)
        )
        assert not result.is_error
        assert result.engines_used == ["arxiv"]
        assert all(r["source"] == "arxiv" for r in result.search_results)

    @pytest.mark.asyncio
    async def test_empty_action_engines_uses_all_available(self):
        executor = SearchExecutor(engines=["arxiv"])
        result = await executor(
            SearchAction(query="deep learning", engines=[], max_results=3)
        )
        assert not result.is_error
        assert result.engines_used == ["arxiv"]
