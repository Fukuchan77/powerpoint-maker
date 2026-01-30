from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from pptx.enum.chart import XL_CHART_TYPE

from app.schemas import ChartData, ChartSeries, SlideContent
from app.services.generator import SlidePopulator
from app.services.research import ResearchAgent


@pytest.mark.asyncio
async def test_enrich_slides_with_images():
    """Test that image URLs are populated when caption exists"""
    agent = ResearchAgent()

    # Mock _search_images to return a dummy URL
    with patch.object(agent, "_search_images", return_value="https://example.com/image.jpg") as mock_search:
        slides = [
            SlideContent(layout_index=0, title="T1", bullet_points=[], image_caption="A cute cat"),
            SlideContent(layout_index=1, title="T2", bullet_points=[], image_caption=None),
        ]

        await agent.enrich_slides_with_images(slides)

        # Slide 1 should have image URL
        assert slides[0].image_url == "https://example.com/image.jpg"
        mock_search.assert_called_with("A cute cat")

        # Slide 2 should not change
        assert slides[1].image_url is None


def test_insert_chart():
    """Test inserting a chart into a placeholder"""
    mock_placeholder = Mock()
    mock_chart_obj = Mock()
    mock_placeholder.insert_chart.return_value.chart = mock_chart_obj

    populator = SlidePopulator(Mock())

    chart_data = ChartData(
        title="Sales Data",
        type="COLUMN_CLUSTERED",
        categories=["Q1", "Q2"],
        series=[ChartSeries(name="Revenue", values=[100.0, 150.0])],
    )

    populator.insert_chart(mock_placeholder, chart_data)

    # Verify insert_chart called with correct type
    args, _ = mock_placeholder.insert_chart.call_args
    assert args[0] == XL_CHART_TYPE.COLUMN_CLUSTERED

    # Verify data construction (checking call args deeper is hard as CategoryChartData is complex object)
    # But we can verify it didn't fail and called insert_chart.
    assert mock_placeholder.insert_chart.called

    # Verify title setting
    assert mock_chart_obj.has_title is True
    assert mock_chart_obj.chart_title.text_frame.text == "Sales Data"


@pytest.mark.asyncio
async def test_research_agent_parses_chart_data():
    """Test that the ResearchAgent correctly parses chart data from LLM response"""
    agent = ResearchAgent()
    agent.enabled = True
    agent.llm = AsyncMock()
    agent.tool = AsyncMock()
    agent.tool.run.return_value = MagicMock(results=[])  # Emtpy search results

    # Mock LLM response with JSON containing chart
    mock_json = """
    {
        "topic": "Test Topic",
        "slides": [
            {
                "layout_index": 0,
                "title": "Slide with Chart",
                "bullet_points": [],
                "chart": {
                    "title": "Growth",
                    "type": "LINE",
                    "categories": ["2020", "2021"],
                    "series": [
                        { "name": "Users", "values": [100, 200] }
                    ]
                }
            }
        ]
    }
    """

    mock_response = MagicMock()
    mock_response.state.message.content = f"```json\n{mock_json}\n```"
    agent.llm.generate.return_value = mock_response

    # Mock dependencies to avoid side effects
    with patch.object(agent, "enrich_slides_with_images", new_callable=AsyncMock):
        slides = await agent.research("Test Topic")

        assert len(slides) == 1
        assert slides[0].chart is not None
        assert slides[0].chart.title == "Growth"
        assert slides[0].chart.type == "LINE"
        assert len(slides[0].chart.series) == 1
        assert slides[0].chart.series[0].values == [100, 200]
