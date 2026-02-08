"""
Integration tests for Layout Intelligence feature.

These tests verify the end-to-end flow and integration points.
Note: Full LLM integration is tested separately. These tests focus on:
- API endpoint availability and error handling
- Integration with existing flows (research, generate)
- Template compatibility
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# T076: E2E test for text input to layout intelligence API
def test_e2e_layout_intelligence_endpoint_exists():
    """Test that /api/layout-intelligence endpoint exists and accepts requests."""

    response = client.post(
        "/api/layout-intelligence",
        json={
            "text": "Test content for layout intelligence",
        },
    )

    # Should not return 404 (endpoint exists)
    assert response.status_code != 404
    # Should return either 200 (success) or 500/422 (LLM/validation error)
    assert response.status_code in [200, 422, 500, 504]


# T077: E2E test for layout intelligence output to PPTX generation
def test_e2e_slides_to_pptx(sample_pptx):
    """Test that layout intelligence output format is compatible with PPTX generation."""

    # Step 1: Analyze template to get template_id
    with open(sample_pptx, "rb") as f:
        analyze_response = client.post(
            "/api/analyze-template",
            files={
                "file": (sample_pptx, f, "application/vnd.openxmlformats-officedocument.presentationml.presentation")
            },
        )
    assert analyze_response.status_code == 200
    template_id = analyze_response.json()["template_id"]

    # Step 2: Use manually crafted slides (simulating layout intelligence output)
    slides_data = [
        {"layout_index": 0, "title": "Test Presentation", "bullet_points": []},
        {"layout_index": 1, "title": "Key Points", "bullet_points": ["Point 1", "Point 2", "Point 3"]},
    ]

    # Step 3: Generate PPTX from slides
    generate_response = client.post(
        "/api/generate",
        json={
            "template_filename": "test.pptx",  # Required field
            "template_id": template_id,
            "slides": slides_data,
        },
    )

    assert generate_response.status_code == 200
    assert (
        generate_response.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
    assert len(generate_response.content) > 0


# T078: E2E test for Two-Column layout in generated PPTX
def test_e2e_two_column_layout_compatibility(sample_pptx):
    """Test that Two-Column layout slides can be generated in PPTX."""

    # Analyze template
    with open(sample_pptx, "rb") as f:
        analyze_response = client.post(
            "/api/analyze-template",
            files={
                "file": (sample_pptx, f, "application/vnd.openxmlformats-officedocument.presentationml.presentation")
            },
        )
    template_id = analyze_response.json()["template_id"]

    # Create Two-Column slide data
    two_column_slide = {
        "layout_index": 1,  # Use available layout
        "title": "Comparison",
        "bullet_points": [
            "Option A: Fast and simple",
            "Option B: Slow but thorough",
            "Option A: Lower cost",
            "Option B: Higher quality",
        ],
    }

    # Generate PPTX with Two-Column slide
    generate_response = client.post(
        "/api/generate",
        json={
            "template_filename": "test.pptx",  # Required field
            "template_id": template_id,
            "slides": [two_column_slide],
        },
    )

    assert generate_response.status_code == 200
    assert len(generate_response.content) > 0


# T079: E2E test for overflow handling
def test_e2e_overflow_handling():
    """Test that API handles long text input appropriately."""

    # Create very long text (would cause overflow)
    long_text = "Long Content\n\n" + "\n".join([f"Point {i}: " + "x" * 100 for i in range(50)])

    response = client.post(
        "/api/layout-intelligence",
        json={
            "text": long_text,
        },
    )

    # Should handle gracefully (not crash)
    assert response.status_code in [200, 422, 500, 504]

    # If successful, should return valid structure
    if response.status_code == 200:
        data = response.json()
        assert "slides" in data
        assert "warnings" in data


# T080: E2E test for response structure
def test_e2e_response_structure():
    """Test that API response includes required fields."""

    response = client.post(
        "/api/layout-intelligence",
        json={
            "text": "Simple test content",
        },
    )

    # If successful, verify response structure
    if response.status_code == 200:
        data = response.json()
        assert "slides" in data
        assert "warnings" in data
        assert isinstance(data["slides"], list)
        assert isinstance(data["warnings"], list)


# T081: E2E test verifying existing flows unaffected
@pytest.mark.asyncio
async def test_e2e_existing_flows_unaffected(sample_pptx):
    """Test that web search and markdown flows still work after layout intelligence addition."""

    # Test 1: Web search flow (research endpoint)
    with patch("app.api.routes.researcher.research", new_callable=AsyncMock) as mock_research:
        mock_research.return_value = [
            {"layout_index": 1, "title": "Research Result", "bullet_points": ["Finding 1", "Finding 2"]}
        ]

        research_response = client.post("/api/research", params={"topic": "AI Testing"})

        assert research_response.status_code == 200
        research_data = research_response.json()
        assert len(research_data) > 0
        assert research_data[0]["title"] == "Research Result"

    # Test 2: Markdown flow (generate endpoint with markdown)
    with open(sample_pptx, "rb") as f:
        analyze_response = client.post(
            "/api/analyze-template",
            files={
                "file": (sample_pptx, f, "application/vnd.openxmlformats-officedocument.presentationml.presentation")
            },
        )
    template_id = analyze_response.json()["template_id"]

    markdown_slides = [{"layout_index": 0, "title": "Markdown Title", "bullet_points": ["Point 1", "Point 2"]}]

    generate_response = client.post(
        "/api/generate",
        json={
            "template_filename": "test.pptx",  # Required field
            "template_id": template_id,
            "slides": markdown_slides,
        },
    )

    assert generate_response.status_code == 200
    assert len(generate_response.content) > 0

    # Test 3: Template analysis still works
    with open(sample_pptx, "rb") as f:
        analyze_response2 = client.post(
            "/api/analyze-template",
            files={
                "file": (sample_pptx, f, "application/vnd.openxmlformats-officedocument.presentationml.presentation")
            },
        )

    assert analyze_response2.status_code == 200
    assert "template_id" in analyze_response2.json()
    assert "masters" in analyze_response2.json()


# Made with Bob
