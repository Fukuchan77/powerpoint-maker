import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.research import ResearchAgent


@pytest.mark.asyncio
async def test_research_llm_timeout():
    """Test handling of LLM timeout"""
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

        # Setup LLM mock to raise TimeoutError
        mock_llm_instance = MagicMock()
        mock_llm_instance.run = AsyncMock(side_effect=asyncio.TimeoutError("LLM Timeout"))
        mock_get_llm.return_value = mock_llm_instance

        # Create agent
        agent = ResearchAgent()
        agent.tool = mock_search_instance

        # Execute research - should catch TimeoutError and fallback
        result = await agent.research("Test Topic")

        # Fallback to mock research
        assert len(result) == 3
        assert result[0].title == "Introduction to Test Topic"
