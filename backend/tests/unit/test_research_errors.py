from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.research import ResearchAgent


@pytest.mark.asyncio
async def test_research_search_429_ratelimit():
    """Test handling of 429 Rate Limit from Search Tool"""
    agent = ResearchAgent()

    with (
        patch("app.services.research.DuckDuckGoSearchTool") as MockSearch,
        patch("app.services.research.DDGS_AVAILABLE", False),
        patch("app.services.research.DOCLING_AVAILABLE", False),
    ):
        mock_search_instance = MockSearch.return_value
        # Simulate an exception that might represent a 429 (e.g. from duckduckgo_search)
        mock_search_instance.run = AsyncMock(side_effect=Exception("429 Ratelimit exceeded"))

        agent.tool = mock_search_instance

        # The research method has a try/except that catches all exceptions
        # and falls back to mock research
        result = await agent.research("Test Topic")

        # Should fallback to mock research (3 slides)
        assert len(result) == 3
        assert "Introduction to" in result[0].title
        assert result[0].title == "Introduction to Test Topic"


@pytest.mark.asyncio
async def test_research_llm_500_error():
    """Test handling of 500 Error from LLM"""
    # Mock at module level to prevent any real initialization
    with (
        patch("app.services.research.DuckDuckGoSearchTool") as MockSearch,
        patch("app.services.research.get_llm") as mock_get_llm,
        patch("app.services.research.DDGS_AVAILABLE", False),
        patch("app.services.research.DOCLING_AVAILABLE", False),
    ):
        # Setup search tool mock
        mock_search_instance = MockSearch.return_value
        mock_search_results = MagicMock()
        mock_search_results.results = []
        mock_search_instance.run = AsyncMock(return_value=mock_search_results)

        # Setup LLM mock to raise error
        mock_llm_instance = MagicMock()
        mock_llm_instance.run = AsyncMock(side_effect=Exception("500 Internal Server Error"))
        mock_get_llm.return_value = mock_llm_instance

        # Create agent after mocks are in place
        agent = ResearchAgent()
        agent.tool = mock_search_instance

        # Execute research - should catch LLM error and fallback to mock research
        result = await agent.research("Test Topic")

        # Should fallback to mock research (3 slides)
        assert len(result) == 3
        assert "Introduction to" in result[0].title
        assert result[0].title == "Introduction to Test Topic"
        assert result[1].title == "Key Concepts"
        assert result[2].title == "Future Trends"
