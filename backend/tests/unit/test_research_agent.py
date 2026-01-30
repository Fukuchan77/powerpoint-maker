from unittest.mock import AsyncMock, patch

import pytest
from beeai_framework.backend.message import AssistantMessage

from app.schemas import SlideContent
from app.services.research import ResearchAgent


@pytest.mark.asyncio
async def test_research_flow():
    # Mock dependencies
    with (
        patch("app.services.research.DuckDuckGoSearchTool") as MockSearch,
        patch("app.services.research.get_llm") as mock_get_llm,
        patch("app.services.research.DocumentConverter") as MockConverter,
    ):
        # Setup Mock Search
        mock_tool_instance = MockSearch.return_value
        # Mock results as a list of objects with url attribute
        mock_result_item = type("obj", (object,), {"url": "http://example.com", "description": "desc"})
        mock_tool_instance.run = AsyncMock(return_value=type("obj", (object,), {"results": [mock_result_item]})())

        # Setup Mock LLM
        mock_llm_instance = mock_get_llm.return_value
        mock_llm_instance.generate = AsyncMock(
            return_value=type(
                "obj",
                (object,),
                {
                    "state": type(
                        "obj",
                        (object,),
                        {
                            "message": AssistantMessage(
                                content="""
                ```json
                {
                    "topic": "Test Topic",
                    "slides": [
                        {
                            "layout_index": 0,
                            "title": "Test Title",
                            "bullet_points": ["Point 1", "Point 2"],
                            "image_caption": null
                        }
                    ]
                }
                ```
                """
                            )
                        },
                    )()
                },
            )()
        )

        # Setup Mock Converter
        # Reviewer Note: mock_converter_instance was removed as it was unused (F841)
        MockConverter.return_value.convert = AsyncMock()  # Can be plain mock if run_in_executor mocks

        # Since we use run_in_executor, we might need to mock that or the converter call inside it
        # Easier: Mock _fetch_content method of the agent?
        # Or just trust the mock converter if we control it.

        agent = ResearchAgent()

        # Mock _fetch_content to avoid async loop issues with run_in_executor in test
        agent._fetch_content = AsyncMock(return_value="Mocked Page Content")

        slides = await agent.research("Test Topic")

        assert len(slides) == 1
        assert slides[0].title == "Test Title"
        assert slides[0].bullet_points == ["Point 1", "Point 2"]

        mock_tool_instance.run.assert_called_once()
        agent._fetch_content.assert_called_once_with("http://example.com")
        mock_llm_instance.generate.assert_called_once()


@pytest.mark.asyncio
async def test_research_llm_failure():
    with (
        patch("app.services.research.DuckDuckGoSearchTool"),
        patch("app.services.research.get_llm", side_effect=Exception("LLM Init Failed")),
    ):
        agent = ResearchAgent()
        assert agent.enabled is False

        slides = await agent.research("Test Topic")
        assert len(slides) == 3  # Returns mock data (3 slides)
        assert slides[0].title == "Introduction to Test Topic"


@pytest.mark.asyncio
async def test_research_fetch_failure():
    with (
        patch("app.services.research.DuckDuckGoSearchTool") as MockSearch,
        patch("app.services.research.get_llm") as mock_get_llm,
        patch("app.services.research.DocumentConverter"),
    ):
        # Mock Search
        mock_tool_instance = MockSearch.return_value
        mock_tool_instance.run = AsyncMock(
            return_value=type(
                "obj",
                (object,),
                {"results": [type("obj", (object,), {"url": "http://bad-url.com", "description": "Snippet"})]},
            )()
        )

        # Mock LLM (Needs to be valid to test synthesis fallback)
        mock_llm_instance = mock_get_llm.return_value
        mock_llm_instance.generate = AsyncMock(
            return_value=type(
                "obj",
                (object,),
                {
                    "state": type(
                        "obj",
                        (object,),
                        {
                            "message": AssistantMessage(content="[]")  # Empty valid JSON for simplicity or check prompt
                        },
                    )()
                },
            )()
        )

        agent = ResearchAgent()
        # Mock _fetch_content to return empty string (simulating failure)
        agent._fetch_content = AsyncMock(return_value="")

        await agent.research("Test Topic")

        # Verify LLM called with snippets since fetch failed
        # We can inspect the prompt arg to see if it contains "Snippet"
        call_args = mock_llm_instance.generate.call_args
        assert call_args
        # call_args[0][0] is the list of messages. [0] is UserMessage. content is the prompt.
        prompt_content = call_args[0][0][0].content
        if isinstance(prompt_content, list):
            prompt_text = prompt_content[0].text
        else:
            prompt_text = prompt_content
        assert "Snippet" in prompt_text


@pytest.mark.asyncio
async def test_research_malformed_response():
    with (
        patch("app.services.research.DuckDuckGoSearchTool") as MockSearch,
        patch("app.services.research.get_llm") as mock_get_llm,
    ):
        mock_tool_instance = MockSearch.return_value
        mock_tool_instance.run = AsyncMock(return_value=type("obj", (object,), {"results": []})())

        mock_llm_instance = mock_get_llm.return_value
        # Return invalid JSON
        mock_llm_instance.generate = AsyncMock(
            return_value=type(
                "obj", (object,), {"state": type("obj", (object,), {"message": AssistantMessage(content="NOT JSON")})()}
            )()
        )

        agent = ResearchAgent()
        slides = await agent.research("Test Topic")

        # Should fallback to mock data
        assert len(slides) == 3
        assert slides[0].title.startswith("Introduction to")


@pytest.mark.asyncio
async def test_research_without_docling():
    """Test behavior when Docling is not available"""
    with (
        patch("app.services.research.DuckDuckGoSearchTool") as MockSearch,
        patch("app.services.research.get_llm") as mock_get_llm,
        patch("app.services.research.DOCLING_AVAILABLE", False),
    ):
        mock_tool_instance = MockSearch.return_value
        mock_tool_instance.run = AsyncMock(
            return_value=type(
                "obj",
                (object,),
                {"results": [type("obj", (object,), {"url": "http://example.com", "description": "desc"})]},
            )()
        )

        mock_llm_instance = mock_get_llm.return_value
        mock_llm_instance.generate = AsyncMock(
            return_value=type(
                "obj",
                (object,),
                {
                    "state": type(
                        "obj",
                        (object,),
                        {
                            "message": AssistantMessage(
                                content="""
                ```json
                { "topic": "T", "slides": [] }
                ```
                """
                            )
                        },
                    )()
                },
            )()
        )

        agent = ResearchAgent()
        # _fetch_content should return empty string immediately if DOCLING_AVAILABLE is False
        content = await agent._fetch_content("http://example.com")
        assert content == ""

        # Ensure research runs without crashing and uses snippets (implicit in logic)
        await agent.research("Test")
        mock_llm_instance.generate.assert_called()


@pytest.mark.asyncio
async def test_research_llm_returns_list():
    """Test when LLM returns a list in message content"""
    # This simulates the `if isinstance(text_response, list):` block
    with (
        patch("app.services.research.DuckDuckGoSearchTool") as MockSearch,
        patch("app.services.research.get_llm") as mock_get_llm,
    ):
        # Fix: Mock run as AsyncMock
        mock_tool_instance = MockSearch.return_value
        # Use simple mock result
        mock_tool_instance.run = AsyncMock(return_value=type("obj", (object,), {"results": []})())

        mock_llm_instance = mock_get_llm.return_value

        # Mocking a list response
        mock_content_item = type("obj", (object,), {"text": '{"topic": "T", "slides": []}'})

        mock_llm_instance.generate = AsyncMock(
            return_value=type(
                "obj",
                (object,),
                {"state": type("obj", (object,), {"message": AssistantMessage(content=[mock_content_item])})()},
            )()
        )

        agent = ResearchAgent()
        slides = await agent.research("Test")
        assert isinstance(slides, list)


@pytest.mark.asyncio
async def test_research_empty_search_results():
    """Test fallback when no search results found"""
    with (
        patch("app.services.research.DuckDuckGoSearchTool") as MockSearch,
        patch("app.services.research.get_llm") as mock_get_llm,
    ):
        mock_tool = MockSearch.return_value
        # Empty results - Fix: Ensure run is AsyncMock
        mock_tool.run = AsyncMock(return_value=type("obj", (object,), {"results": []})())

        mock_llm = mock_get_llm.return_value
        mock_llm.generate = AsyncMock(
            return_value=type(
                "obj",
                (object,),
                {
                    "state": type(
                        "obj", (object,), {"message": AssistantMessage(content='{"topic": "T", "slides": []}')}
                    )()
                },
            )()
        )

        agent = ResearchAgent()
        await agent.research("Test")

        # Verify LLM called even with empty results
        mock_llm.generate.assert_called()


@pytest.mark.asyncio
async def test_research_fetch_content_success():
    """Test successful content fetching via DocumentConverter"""
    # Patch DOCLING_AVAILABLE to True to ensure we enter the block
    with (
        patch("app.services.research.DocumentConverter"),
        patch("app.services.research.DuckDuckGoSearchTool"),
        patch("app.services.research.get_llm"),
        patch("app.services.research.DOCLING_AVAILABLE", True),
        patch("asyncio.get_event_loop") as mock_get_loop,
        patch("builtins.print") as mock_print,
    ):
        # mock_converter_instance = MockConverter.return_value (Unused)
        # Mock convert return value
        mock_doc = type(
            "obj",
            (object,),
            {"document": type("obj", (object,), {"export_to_markdown": lambda *args: "Markdown Content"})()},
        )

        # Mock loop and run_in_executor
        mock_loop = mock_get_loop.return_value
        mock_loop.run_in_executor = AsyncMock(return_value=mock_doc)

        agent = ResearchAgent()
        # Call _fetch_content strictly
        content = await agent._fetch_content("http://example.com")

        # If content is empty, check if print was called with exception
        if content == "":
            print_calls = [str(call) for call in mock_print.mock_calls]
            pytest.fail(f"Content was empty. Print calls: {print_calls}")

        assert content == "Markdown Content"
        mock_loop.run_in_executor.assert_called()


@pytest.mark.asyncio
async def test_research_generic_markdown_block():
    """Test LLM response with generic markdown block"""
    with (
        patch("app.services.research.DuckDuckGoSearchTool") as MockSearch,
        patch("app.services.research.get_llm") as mock_get_llm,
    ):
        # KEY FIX: Mock the search tool run method as AsyncMock
        mock_tool = MockSearch.return_value
        mock_tool.run = AsyncMock(return_value=type("obj", (object,), {"results": []})())

        mock_llm_instance = mock_get_llm.return_value
        mock_llm_instance.generate = AsyncMock(
            return_value=type(
                "obj",
                (object,),
                {
                    "state": type(
                        "obj",
                        (object,),
                        {
                            "message": AssistantMessage(
                                content="""
                ```
                { "topic": "T", "slides": [] }
                ```
                """
                            )
                        },
                    )()
                },
            )()
        )

        agent = ResearchAgent()
        slides = await agent.research("Test")
        # Should parse correctly despite generic code block
        assert len(slides) == 0  # Or check content if I put slides in it

        # Should parse correctly despite generic code block
        assert len(slides) == 0  # Or check content if I put slides in it


def test_select_layout_logic():
    agent = ResearchAgent()

    # Mock Layouts
    # Layout 0: Title only
    # Layout 1: Title + Body
    # Layout 2: Title + Picture + Body (Ideal for content + img)
    # Layout 3: Title + Picture only

    from app.schemas import LayoutInfo, PlaceholderInfo

    l0 = LayoutInfo(
        index=0,
        name="Title Slide",
        placeholders=[PlaceholderInfo(idx=0, name="Title", type="TITLE", width=0, height=0, left=0, top=0)],
    )
    l1 = LayoutInfo(
        index=1,
        name="Content",
        placeholders=[
            PlaceholderInfo(idx=0, name="Title", type="TITLE", width=0, height=0, left=0, top=0),
            PlaceholderInfo(idx=1, name="Body", type="BODY", width=0, height=0, left=0, top=0),
        ],
    )
    l2 = LayoutInfo(
        index=2,
        name="Picture Content",
        placeholders=[
            PlaceholderInfo(idx=0, name="Title", type="TITLE", width=0, height=0, left=0, top=0),
            PlaceholderInfo(idx=1, name="Body", type="BODY", width=0, height=0, left=0, top=0),
            PlaceholderInfo(idx=2, name="Px", type="PICTURE", width=0, height=0, left=0, top=0),
        ],
    )

    layouts = [l0, l1, l2]

    # Case 1: Slide with Image and Bullets -> Should pick l2
    s1 = SlideContent(layout_index=0, title="Img Slide", bullet_points=["A"], image_url="http://img.png")
    assert agent.select_layout(s1, layouts) == 2

    # Case 2: Slide with Bullets only -> Should pick l1
    s2 = SlideContent(layout_index=0, title="Text Slide", bullet_points=["A"])
    assert agent.select_layout(s2, layouts) == 1

    # Case 3: Title only (Intro) -> Should pick l0 (or keep 0 if it was 0)
    # ... (previous content)
    s3 = SlideContent(layout_index=0, title="Intro", bullet_points=[])
    # Note: "Intro" triggers is_title heuristic
    assert agent.select_layout(s3, layouts) == 0


@pytest.mark.asyncio
async def test_image_enrichment():
    """Test that slides with captions get enriched with image URLs"""
    with (
        patch("app.services.research.DDGS_AVAILABLE", True),
        patch("app.services.research.DDGS") as MockDDGS,
        patch("asyncio.get_event_loop") as mock_get_loop,
    ):
        # Mock DDGS context manager
        mock_ddgs_instance = MockDDGS.return_value
        mock_ddgs_instance.__enter__.return_value = mock_ddgs_instance
        mock_ddgs_instance.__exit__.return_value = None

        # Mock images results
        mock_ddgs_instance.images.return_value = [{"image": "http://found-image.com/pic.jpg"}]

        # Mock loop
        mock_loop = mock_get_loop.return_value

        # When run_in_executor is called, we just run the function immediately for simplification or return mocks
        # But _search_images is called inside run_in_executor.
        # A better way is to invoke the lambda.
        async def side_effect(executor, func):
            return func()

        mock_loop.run_in_executor.side_effect = side_effect

        agent = ResearchAgent()

        slides = [
            SlideContent(layout_index=1, title="Has Caption", bullet_points=[], image_caption="A beautiful sunset"),
            SlideContent(layout_index=1, title="No Caption", bullet_points=[]),
            SlideContent(
                layout_index=1,
                title="Already Has URL",
                bullet_points=[],
                image_caption="Sunset",
                image_url="http://existing.com/pic.jpg",
            ),
        ]

        await agent.enrich_slides_with_images(slides)

        # Verify call args
        mock_ddgs_instance.images.assert_called_with("A beautiful sunset", max_results=1)

        # Verify modifications
        assert slides[0].image_url == "http://found-image.com/pic.jpg"  # assigned
        assert slides[1].image_url is None  # Not touched
        assert slides[2].image_url == "http://existing.com/pic.jpg"  # Not overwritten
