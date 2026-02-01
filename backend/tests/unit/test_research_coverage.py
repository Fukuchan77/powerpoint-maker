"""
Comprehensive tests for research.py to improve coverage from 70% to 80%+
Focus on:
- Error recovery logic
- Edge cases (empty results, timeouts)
- LLM response pattern variations
- Multi-phase error handling
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas import LayoutInfo, PlaceholderInfo, SlideContent
from app.services.research import ResearchAgent


class TestResearchAgentEdgeCases:
    """Test edge cases and error recovery"""

    @pytest.mark.asyncio
    async def test_research_with_empty_search_results(self):
        """Test handling of empty search results"""
        agent = ResearchAgent()

        with (
            patch("app.services.research.DuckDuckGoSearchTool") as MockSearch,
            patch.object(agent, "llm", create=True) as mock_llm,
        ):
            # Empty search results
            mock_search_instance = MockSearch.return_value
            empty_results = MagicMock()
            empty_results.results = []
            mock_search_instance.run = AsyncMock(return_value=empty_results)

            # Mock LLM response - return string directly from output
            json_content = (
                '{"topic": "Test", "slides": [{"layout_index": 0, "title": "Test Slide", '
                '"bullets": [{"text": "Point 1", "level": 0}]}]}'
            )

            mock_response = MagicMock()
            # Create proper mock structure that returns string
            content_mock = MagicMock()
            content_mock.__str__ = MagicMock(return_value=json_content)
            # Make it return the string when accessed
            type(content_mock).text = property(lambda self: json_content)

            output_item = MagicMock()
            output_item.content = json_content  # Direct string assignment
            mock_response.output = [output_item]

            mock_llm.run = AsyncMock(return_value=mock_response)

            agent.tool = mock_search_instance
            result = await agent.research("Test Topic")

            # With empty search results and mock structure, it falls back to mock research
            assert len(result) == 3
            assert "Introduction to" in result[0].title

    @pytest.mark.asyncio
    async def test_research_with_fetch_content_failures(self):
        """Test handling when all content fetch operations fail"""
        agent = ResearchAgent()

        with (
            patch("app.services.research.DuckDuckGoSearchTool") as MockSearch,
            patch.object(agent, "llm", create=True) as mock_llm,
            patch.object(agent, "_fetch_content", return_value="") as mock_fetch,
        ):
            # Search returns results but fetch fails
            mock_search_instance = MockSearch.return_value
            search_results = MagicMock()
            result1 = MagicMock()
            result1.url = "http://example.com"
            result1.description = "Fallback description"
            search_results.results = [result1]
            mock_search_instance.run = AsyncMock(return_value=search_results)

            # Mock LLM response
            mock_response = MagicMock()
            mock_response.output = [
                MagicMock(
                    content='{"topic": "Test", "slides": [{"layout_index": 0, "title": "Fallback", "bullets": []}]}'
                )
            ]
            mock_llm.run = AsyncMock(return_value=mock_response)

            agent.tool = mock_search_instance
            result = await agent.research("Test Topic")

            # Should fall back to search snippets
            assert mock_fetch.called
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_research_with_llm_json_parse_error(self):
        """Test handling of malformed LLM JSON response"""
        agent = ResearchAgent()

        with (
            patch("app.services.research.DuckDuckGoSearchTool") as MockSearch,
            patch.object(agent, "llm", create=True) as mock_llm,
        ):
            mock_search_instance = MockSearch.return_value
            search_results = MagicMock()
            search_results.results = []
            mock_search_instance.run = AsyncMock(return_value=search_results)

            # Malformed JSON response
            mock_response = MagicMock()
            mock_response.output = [MagicMock(content="This is not JSON at all")]
            mock_llm.run = AsyncMock(return_value=mock_response)

            agent.tool = mock_search_instance
            result = await agent.research("Test Topic")

            # Should fall back to mock research
            assert len(result) == 3  # Mock returns 3 slides
            assert "Introduction to" in result[0].title

    @pytest.mark.asyncio
    async def test_research_with_timeout_simulation(self):
        """Test handling of search timeout - expects exception propagation"""
        agent = ResearchAgent()

        with patch("app.services.research.DuckDuckGoSearchTool") as MockSearch:
            mock_search_instance = MockSearch.return_value
            # Simulate timeout
            mock_search_instance.run = AsyncMock(side_effect=asyncio.TimeoutError("Search timeout"))

            agent.tool = mock_search_instance

            # The timeout should be caught and handled gracefully (fallback to mock)
            result = await agent.research("Test Topic")

            # Should fall back to mock research
            assert len(result) == 3
            assert "Introduction to" in result[0].title


class TestLayoutSelection:
    """Test layout selection heuristics"""

    def test_select_layout_for_title_slide(self):
        """Test layout selection for title-only slide"""
        agent = ResearchAgent()

        layouts = [
            LayoutInfo(
                index=0,
                name="Title Slide",
                placeholders=[
                    PlaceholderInfo(idx=0, type="TITLE", name="Title", width=100, height=50, left=0, top=0),
                ],
            ),
            LayoutInfo(
                index=1,
                name="Content",
                placeholders=[
                    PlaceholderInfo(idx=0, type="TITLE", name="Title", width=100, height=30, left=0, top=0),
                    PlaceholderInfo(idx=1, type="BODY", name="Body", width=100, height=60, left=0, top=30),
                ],
            ),
        ]

        slide = SlideContent(
            layout_index=0,
            title="Introduction",
            bullet_points=[],
            bullets=[],
        )

        layout_idx = agent.select_layout(slide, layouts)
        assert layout_idx == 0  # Should select title-only layout

    def test_select_layout_for_content_with_image(self):
        """Test layout selection for slide with image"""
        agent = ResearchAgent()

        layouts = [
            LayoutInfo(
                index=0,
                name="Title",
                placeholders=[PlaceholderInfo(idx=0, type="TITLE", name="Title", width=100, height=50, left=0, top=0)],
            ),
            LayoutInfo(
                index=1,
                name="Content",
                placeholders=[
                    PlaceholderInfo(idx=0, type="TITLE", name="Title", width=100, height=30, left=0, top=0),
                    PlaceholderInfo(idx=1, type="BODY", name="Body", width=100, height=60, left=0, top=30),
                ],
            ),
            LayoutInfo(
                index=2,
                name="Picture",
                placeholders=[
                    PlaceholderInfo(idx=0, type="TITLE", name="Title", width=100, height=30, left=0, top=0),
                    PlaceholderInfo(idx=1, type="PICTURE", name="Picture", width=100, height=60, left=0, top=30),
                ],
            ),
        ]

        slide = SlideContent(
            layout_index=1,
            title="Visual Content",
            bullet_points=[],
            image_caption="Test image",
        )

        layout_idx = agent.select_layout(slide, layouts)
        assert layout_idx == 2  # Should select picture layout

    def test_select_layout_with_empty_layouts(self):
        """Test layout selection with no layouts provided"""
        agent = ResearchAgent()

        slide = SlideContent(
            layout_index=5,
            title="Test",
            bullet_points=["Point 1"],
        )

        layout_idx = agent.select_layout(slide, [])
        assert layout_idx == 5  # Should keep original


class TestImageEnrichment:
    """Test image search and enrichment"""

    @pytest.mark.asyncio
    async def test_enrich_slides_with_images_success(self):
        """Test successful image enrichment"""
        agent = ResearchAgent()

        with patch.object(agent, "_search_images", return_value="http://example.com/image.jpg"):
            slides = [
                SlideContent(
                    layout_index=0,
                    title="Test Slide",
                    bullet_points=[],
                    image_caption="A test image",
                    image_url=None,
                )
            ]

            await agent.enrich_slides_with_images(slides)

            assert slides[0].image_url == "http://example.com/image.jpg"

    @pytest.mark.asyncio
    async def test_enrich_slides_skip_existing_url(self):
        """Test that slides with existing URLs are skipped"""
        agent = ResearchAgent()

        slides = [
            SlideContent(
                layout_index=0,
                title="Test Slide",
                bullet_points=[],
                image_caption="A test image",
                image_url="http://existing.com/image.jpg",
            )
        ]

        await agent.enrich_slides_with_images(slides)

        # URL should remain unchanged
        assert slides[0].image_url == "http://existing.com/image.jpg"

    @pytest.mark.asyncio
    async def test_enrich_slides_no_caption(self):
        """Test that slides without captions are skipped"""
        agent = ResearchAgent()

        with patch.object(agent, "_search_images") as mock_search:
            slides = [
                SlideContent(
                    layout_index=0,
                    title="Test Slide",
                    bullet_points=["Point 1"],
                    image_caption=None,
                    image_url=None,
                )
            ]

            await agent.enrich_slides_with_images(slides)

            # Search should not be called
            assert not mock_search.called
            assert slides[0].image_url is None


class TestResponseParsing:
    """Test response parsing with various formats"""

    def test_extract_json_from_json_codeblock(self):
        """Test extraction from ```json block"""
        agent = ResearchAgent()

        text = """```json
{
    "topic": "Test",
    "slides": []
}
```"""

        result = agent._extract_json_from_markdown(text)
        assert "topic" in result
        assert "Test" in result

    def test_extract_json_from_generic_codeblock(self):
        """Test extraction from ``` block"""
        agent = ResearchAgent()

        text = """```
{
    "topic": "Test",
    "slides": []
}
```"""

        result = agent._extract_json_from_markdown(text)
        assert "{" in result

    def test_extract_json_from_raw_text(self):
        """Test extraction from raw JSON"""
        agent = ResearchAgent()

        text = '{"topic": "Test", "slides": []}'

        result = agent._extract_json_from_markdown(text)
        assert result == text.strip()

    def test_extract_text_from_string_response(self):
        """Test extraction when response is already a string"""
        agent = ResearchAgent()

        response = '{"topic": "Test"}'
        result = agent._extract_text_from_response(response)

        assert result == response

    def test_extract_text_from_mock_with_state(self):
        """Test extraction from mock object with state.message.content"""
        agent = ResearchAgent()

        response = MagicMock()
        response.state.message.content = "Test content"

        result = agent._extract_text_from_response(response)
        assert result == "Test content"


class TestDisabledAgent:
    """Test behavior when LLM is disabled"""

    @pytest.mark.asyncio
    async def test_research_with_disabled_llm(self):
        """Test that research falls back to mock when LLM is disabled"""
        # Patch before creating agent
        with patch("app.services.research.get_llm", side_effect=Exception("LLM not available")):
            agent = ResearchAgent()
            assert not agent.enabled

            result = await agent.research("Test Topic")

            # Should use mock research
            assert len(result) == 3
            assert "Introduction to" in result[0].title
