import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# Note: sample_pptx fixture is provided by conftest.py


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_template_endpoint(sample_pptx):
    with open(sample_pptx, "rb") as f:
        response = client.post(
            "/api/analyze-template",
            files={
                "file": (sample_pptx, f, "application/vnd.openxmlformats-officedocument.presentationml.presentation")
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] in [sample_pptx, os.path.basename(sample_pptx)]
    assert "masters" in data
    assert "template_id" in data


@pytest.mark.asyncio
async def test_research_endpoint():
    # Mock the ResearchAgent within the route
    topic = "AI Integration"
    with patch("app.api.routes.researcher.research", new_callable=AsyncMock) as mock_research:
        mock_research.return_value = [{"layout_index": 0, "title": "Intro", "bullet_points": ["A", "B"]}]

        response = client.post("/api/research", params={"topic": topic})

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Intro"
        mock_research.assert_called_once_with(topic, None)


@pytest.mark.asyncio
async def test_research_with_template_id():
    """Test research endpoint with template_id, verifying layouts are passed"""
    topic = "Advanced AI"
    template_id = "test-template-id"

    # Mock LayoutRegistry result
    mock_analysis = AsyncMock()
    mock_analysis.masters = [AsyncMock(layouts=[{"index": 0, "name": "Title Slide", "placeholders": []}])]
    # We need to make sure layouts is a list of objects that match LayoutInfo or dict,
    # dependent on how it's used. In schemas.py LayoutInfo is Pydantic model.
    # But get_or_analyze returns TemplateAnalysisResult.

    from app.schemas import LayoutInfo, MasterInfo, TemplateAnalysisResult

    mock_layouts = [LayoutInfo(index=0, name="Title", placeholders=[])]
    mock_result = TemplateAnalysisResult(
        filename="test.pptx",
        template_id=template_id,
        masters=[MasterInfo(index=0, name="Master", layouts=mock_layouts)],
    )

    with patch("app.api.routes.researcher.research", new_callable=AsyncMock) as mock_research:
        mock_research.return_value = []

        # Patch layout registry
        with patch("app.api.routes.layout_registry.get_or_analyze") as mock_registry:
            mock_registry.return_value = mock_result

            # Patch find_template_by_id to return a path
            with patch("app.api.routes.find_template_by_id", return_value="/fake/path/template.pptx"):
                response = client.post("/api/research", params={"topic": topic, "template_id": template_id})

            assert response.status_code == 200

            # Use ANY for Path object in call args if needed, or check call args
            mock_registry.assert_called_once()

            # Verify research called with layouts
            mock_research.assert_called_once()
            args, _ = mock_research.call_args
            assert args[0] == topic
            assert args[1] == mock_layouts


def test_generate_presentation_endpoint(sample_pptx):
    # 1. Analyze first to get ID
    with open(sample_pptx, "rb") as f:
        # but pure independent test is better.
        # But wait, test_analyze_template_endpoint returns the ID?
        # No, pytest fixtures don't work like that easily across funcs unless session scoped.
        # Let's just do the flow inside this test.
        resp = client.post(
            "/api/analyze-template",
            files={
                "file": (sample_pptx, f, "application/vnd.openxmlformats-officedocument.presentationml.presentation")
            },
        )

    assert resp.status_code == 200
    template_id = resp.json()["template_id"]

    # 2. Generate using valid ID
    payload = {
        "template_filename": sample_pptx,  # Legacy/Metadata
        "template_id": template_id,
        "slides": [{"layout_index": 0, "title": "Generated Slide", "bullet_points": ["Item 1"]}],
    }

    response = client.post("/api/generate", json=payload)

    assert response.status_code == 200
    assert (
        response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
    # Ensure some content was returned
    assert len(response.content) > 0


def test_analyze_template_invalid_file_type():
    """Test uploading a non-pptx file"""
    response = client.post("/api/analyze-template", files={"file": ("test.txt", b"dummy content", "text/plain")})
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


def test_generate_template_not_found():
    """Test generating with a non-existent template ID"""
    payload = {
        "template_id": "non-existent-id",
        "template_filename": "dummy.pptx",  # Required by schema
        "slides": [{"layout_index": 0, "title": "Test"}],
    }
    response = client.post("/api/generate", json=payload)
    assert response.status_code == 404
    assert "Template file not found" in response.json()["detail"]


def test_generate_with_filename_fallback(sample_pptx):
    """Test generating using template_filename when template_id is missing/invalid"""
    # In this test environment, sample_pptx is in the current directory.
    # The route checks absolute path existence first in fallback logic (lines 73-74 of routes.py)
    # So passing the absolute path of sample_pptx should work.

    abs_path = os.path.abspath(sample_pptx)

    payload = {"template_filename": abs_path, "slides": [{"layout_index": 0, "title": "Test"}]}

    response = client.post("/api/generate", json=payload)
    assert response.status_code == 200
    assert (
        response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )


def test_analyze_template_empty_file():
    """Test error handling for empty file"""
    response = client.post(
        "/api/analyze-template",
        files={
            "file": (
                "test.pptx",
                b"",  # Empty file
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            )
        },
    )

    assert response.status_code == 400
    assert "Empty file" in response.json()["detail"]


def test_analyze_template_analysis_error(sample_pptx):
    """Test error handling during analysis"""
    # Patch the layout_registry to raise exception
    with patch("app.api.routes.layout_registry.get_or_analyze", side_effect=Exception("Corrupt file")):
        with open(sample_pptx, "rb") as f:
            response = client.post(
                "/api/analyze-template",
                files={
                    "file": (
                        sample_pptx,
                        f,
                        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    )
                },
            )

    assert response.status_code == 500
    assert "Failed to analyze template structure" in response.json()["detail"]
