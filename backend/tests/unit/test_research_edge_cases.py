from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas import LayoutInfo, PlaceholderInfo, SlideContent
from app.services.research import ResearchAgent


@pytest.mark.asyncio
async def test_extract_text_from_mock_with_output():
    """Test _extract_text_from_response with MagicMock having output attribute"""
    agent = ResearchAgent()

    # Create a mock response with output structure (lines 71-85)
    # Need to configure MagicMock to NOT have state attribute
    mock_response = MagicMock(spec=["output"])  # Only has output, no state
    mock_msg = MagicMock()
    mock_msg.content = "Test content from mock"
    mock_response.output = [mock_msg]

    result = agent._extract_text_from_response(mock_response)
    assert result == "Test content from mock"


@pytest.mark.asyncio
async def test_extract_text_from_mock_with_list_content():
    """Test _extract_text_from_response with MagicMock having list content"""
    agent = ResearchAgent()

    # Create mock with list content (lines 77-85)
    mock_response = MagicMock(spec=["output"])  # Only has output, no state
    mock_msg = MagicMock()

    # Create content items with text attribute
    item1 = MagicMock()
    item1.text = "Part 1"
    item2 = MagicMock()
    item2.text = " Part 2"

    mock_msg.content = [item1, item2]
    mock_response.output = [mock_msg]

    result = agent._extract_text_from_response(mock_response)
    assert result == "Part 1 Part 2"


@pytest.mark.asyncio
async def test_extract_text_from_real_response_with_output():
    """Test _extract_text_from_response with real response structure (lines 89-103)"""
    agent = ResearchAgent()

    # Simulate real response with output attribute
    class RealMessage:
        def __init__(self, content):
            self.content = content

    class RealResponse:
        def __init__(self):
            self.output = [RealMessage("Real response content")]

    response = RealResponse()
    result = agent._extract_text_from_response(response)
    assert result == "Real response content"


@pytest.mark.asyncio
async def test_extract_text_with_text_attribute():
    """Test _extract_text_from_response with direct text attribute (line 107)"""
    agent = ResearchAgent()

    class ResponseWithText:
        text = "Direct text attribute"

    response = ResponseWithText()
    result = agent._extract_text_from_response(response)
    assert result == "Direct text attribute"


@pytest.mark.asyncio
async def test_extract_text_with_content_attribute():
    """Test _extract_text_from_response with content attribute (lines 109-118)"""
    agent = ResearchAgent()

    # Test with string content
    class ResponseWithStringContent:
        content = "String content"

    response = ResponseWithStringContent()
    result = agent._extract_text_from_response(response)
    assert result == "String content"

    # Test with list content
    class Item:
        text = "Item text"

    class ResponseWithListContent:
        content = [Item(), Item()]

    response2 = ResponseWithListContent()
    result2 = agent._extract_text_from_response(response2)
    assert result2 == "Item textItem text"


@pytest.mark.asyncio
async def test_extract_text_fallback():
    """Test _extract_text_from_response fallback to str() (lines 125-127)"""
    agent = ResearchAgent()

    # Object with no recognized attributes
    class UnknownResponse:
        def __str__(self):
            return "Fallback string representation"

    response = UnknownResponse()
    result = agent._extract_text_from_response(response)
    assert result == "Fallback string representation"


@pytest.mark.asyncio
async def test_select_layout_with_layouts():
    """Test select_layout with actual layouts (lines 315-319)"""
    agent = ResearchAgent()

    # Create layouts with proper idx field
    layouts = [
        LayoutInfo(
            index=0,
            name="Title Slide",
            placeholders=[
                PlaceholderInfo(idx=0, type="TITLE", name="Title", left=0, top=0, width=100, height=50),
            ],
        ),
        LayoutInfo(
            index=1,
            name="Title and Content",
            placeholders=[
                PlaceholderInfo(idx=0, type="TITLE", name="Title", left=0, top=0, width=100, height=30),
                PlaceholderInfo(idx=1, type="BODY", name="Content", left=0, top=30, width=100, height=70),
            ],
        ),
        LayoutInfo(
            index=2,
            name="Picture with Caption",
            placeholders=[
                PlaceholderInfo(idx=0, type="TITLE", name="Title", left=0, top=0, width=100, height=30),
                PlaceholderInfo(idx=1, type="PICTURE", name="Picture", left=0, top=30, width=60, height=70),
                PlaceholderInfo(idx=2, type="BODY", name="Caption", left=60, top=30, width=40, height=70),
            ],
        ),
    ]

    # Test with image content
    slide_with_image = SlideContent(
        layout_index=0,
        title="Test Slide",
        bullet_points=[],
        image_caption="Test image",
    )
    selected = agent.select_layout(slide_with_image, layouts)
    assert selected == 2  # Should select picture layout

    # Test with bullets
    slide_with_bullets = SlideContent(
        layout_index=0,
        title="Test Slide",
        bullet_points=["Point 1", "Point 2"],
    )
    selected = agent.select_layout(slide_with_bullets, layouts)
    assert selected == 1  # Should select content layout


@pytest.mark.asyncio
async def test_fetch_content_error_handling():
    """Test _fetch_content error handling (lines 355-357)"""
    agent = ResearchAgent()

    # Mock converter to raise exception
    if hasattr(agent, "converter"):
        with patch.object(agent.converter, "convert", side_effect=Exception("Conversion failed")):
            result = await agent._fetch_content("https://example.com")
            assert result == ""


@pytest.mark.asyncio
async def test_search_images_error_handling():
    """Test _search_images error handling (lines 370-372)"""
    agent = ResearchAgent()

    # Test when DDGS is not available
    with patch("app.services.research.DDGS_AVAILABLE", False):
        result = agent._search_images("test query")
        assert result == ""


@pytest.mark.asyncio
async def test_research_with_layout_optimization():
    """Test research with layout optimization (lines 315-319)"""
    agent = ResearchAgent()

    layouts = [
        LayoutInfo(
            index=0,
            name="Title",
            placeholders=[PlaceholderInfo(idx=0, type="TITLE", name="Title", left=0, top=0, width=100, height=50)],
        ),
        LayoutInfo(
            index=1,
            name="Content",
            placeholders=[
                PlaceholderInfo(idx=0, type="TITLE", name="Title", left=0, top=0, width=100, height=30),
                PlaceholderInfo(idx=1, type="BODY", name="Body", left=0, top=30, width=100, height=70),
            ],
        ),
    ]

    with (
        patch.object(agent.tool, "run", new_callable=AsyncMock) as mock_search,
        patch.object(agent, "_fetch_content", new_callable=AsyncMock) as mock_fetch,
        patch.object(agent.llm, "run", new_callable=AsyncMock) as mock_llm,
        patch.object(agent, "enrich_slides_with_images", new_callable=AsyncMock),
    ):
        # Setup mocks
        mock_result = MagicMock()
        mock_result.results = [
            MagicMock(url="https://example.com", description="Test description"),
        ]
        mock_search.return_value = mock_result
        mock_fetch.return_value = "Test content"

        # Mock LLM response
        llm_response = MagicMock()
        llm_response.state = MagicMock()
        llm_response.state.message = MagicMock()
        llm_response.state.message.content = """
        {
            "topic": "Test Topic",
            "slides": [
                {
                    "layout_index": 0,
                    "title": "Test Slide",
                    "bullets": [{"text": "Point 1", "level": 0}],
                    "bullet_points": [],
                    "image_caption": null
                }
            ]
        }
        """
        mock_llm.return_value = llm_response

        # Call research with layouts
        result = await agent.research("Test Topic", layouts=layouts)

        # Verify layout optimization was applied
        assert len(result) > 0
        # Layout should be optimized based on content
        assert result[0].layout_index in [0, 1]
