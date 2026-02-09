"""Unit tests for layout intelligence API endpoint.

Tests POST /api/layout-intelligence endpoint with request validation,
template resolution, timeout handling, rate limiting, and error responses.
Target coverage: 100% of layout intelligence endpoint code
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request
from pydantic import ValidationError

from app.api.routes import layout_intelligence_endpoint
from app.schemas import (
    LayoutIntelligenceRequest,
    LayoutIntelligenceResponse,
    SlideContent,
)
from app.services.layout_intelligence import LayoutIntelligenceResult


@pytest.fixture
def mock_request():
    """Create mock FastAPI request."""
    return MagicMock(spec=Request)


@pytest.fixture
def valid_request():
    """Create valid layout intelligence request."""
    return LayoutIntelligenceRequest(
        text="Introduction to AI\n\nAI is transforming technology. Key benefits include automation and insights.",
        template_id="test-template-123",
    )


@pytest.fixture
def mock_slide_content():
    """Create mock LayoutIntelligenceResult for successful response."""
    return LayoutIntelligenceResult(
        slides=[
            SlideContent(
                layout_index=1,
                title="Introduction to AI",
                bullet_points=["AI is transforming technology", "Key benefits include automation and insights"],
            )
        ],
        warnings=[],
    )


@pytest.mark.asyncio
async def test_layout_intelligence_success_with_template(mock_request, valid_request, mock_slide_content):
    """Test successful layout intelligence with template_id"""
    with (
        patch("app.api.routes.find_template_by_id", return_value="/path/to/template.pptx"),
        patch("app.api.routes.layout_registry") as mock_registry,
        patch("app.api.routes.LayoutIntelligenceService") as mock_service_class,
    ):
        # Mock template analysis
        mock_analysis = MagicMock()
        mock_analysis.masters = [MagicMock(layouts=[MagicMock(index=0), MagicMock(index=1)])]
        mock_registry.get_or_analyze.return_value = mock_analysis

        # Mock service
        mock_service = AsyncMock()
        mock_service.process.return_value = mock_slide_content
        mock_service_class.return_value = mock_service

        # Call endpoint
        response = await layout_intelligence_endpoint(mock_request, valid_request)

        # Assertions
        assert isinstance(response, LayoutIntelligenceResponse)
        assert len(response.slides) == 1
        assert response.slides[0].title == "Introduction to AI"
        mock_service.process.assert_called_once()


@pytest.mark.asyncio
async def test_layout_intelligence_success_without_template(mock_request, mock_slide_content):
    """Test successful layout intelligence without template_id (uses default)"""
    request = LayoutIntelligenceRequest(text="Test content for default template")

    with (
        patch("app.api.routes.config.DEFAULT_TEMPLATE_PATH") as mock_default_path,
        patch("app.api.routes.layout_registry") as mock_registry,
        patch("app.api.routes.LayoutIntelligenceService") as mock_service_class,
    ):
        # Mock default template
        mock_default_path.exists.return_value = True
        mock_default_path.__str__.return_value = "/path/to/default.pptx"

        # Mock template analysis
        mock_analysis = MagicMock()
        mock_analysis.masters = [MagicMock(layouts=[MagicMock(index=0)])]
        mock_registry.get_or_analyze.return_value = mock_analysis

        # Mock service
        mock_service = AsyncMock()
        mock_service.process.return_value = mock_slide_content
        mock_service_class.return_value = mock_service

        # Call endpoint
        response = await layout_intelligence_endpoint(mock_request, request)

        # Assertions
        assert isinstance(response, LayoutIntelligenceResponse)
        assert len(response.slides) == 1


@pytest.mark.asyncio
async def test_layout_intelligence_template_not_found(mock_request, valid_request):
    """Test error when template_id not found"""
    with patch("app.api.routes.find_template_by_id", return_value=None):
        with pytest.raises(HTTPException) as exc_info:
            await layout_intelligence_endpoint(mock_request, valid_request)

        assert exc_info.value.status_code == 404
        assert "Template not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_layout_intelligence_default_template_not_found(mock_request):
    """Test error when default template not found"""
    request = LayoutIntelligenceRequest(text="Test content")

    with patch("app.api.routes.config.DEFAULT_TEMPLATE_PATH") as mock_default_path:
        mock_default_path.exists.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await layout_intelligence_endpoint(mock_request, request)

        assert exc_info.value.status_code == 404
        assert "Default template not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_layout_intelligence_template_analysis_error(mock_request, valid_request):
    """Test error during template analysis"""
    with (
        patch("app.api.routes.find_template_by_id", return_value="/path/to/template.pptx"),
        patch("app.api.routes.layout_registry") as mock_registry,
    ):
        mock_registry.get_or_analyze.side_effect = Exception("Analysis failed")

        with pytest.raises(HTTPException) as exc_info:
            await layout_intelligence_endpoint(mock_request, valid_request)

        assert exc_info.value.status_code == 500
        assert "Failed to analyze template" in exc_info.value.detail


@pytest.mark.asyncio
async def test_layout_intelligence_timeout(mock_request, valid_request):
    """Test timeout handling during layout intelligence processing"""
    with (
        patch("app.api.routes.find_template_by_id", return_value="/path/to/template.pptx"),
        patch("app.api.routes.layout_registry") as mock_registry,
        patch("app.api.routes.LayoutIntelligenceService") as mock_service_class,
    ):
        # Mock template analysis
        mock_analysis = MagicMock()
        mock_analysis.masters = [MagicMock(layouts=[MagicMock(index=0)])]
        mock_registry.get_or_analyze.return_value = mock_analysis

        # Mock service to raise TimeoutError
        mock_service = AsyncMock()
        mock_service.process.side_effect = asyncio.TimeoutError()
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            await layout_intelligence_endpoint(mock_request, valid_request)

        assert exc_info.value.status_code == 504
        assert "Layout intelligence processing timed out" in exc_info.value.detail


@pytest.mark.asyncio
async def test_layout_intelligence_validation_error(mock_request, valid_request):
    """Test handling of validation errors from LLM"""
    with (
        patch("app.api.routes.find_template_by_id", return_value="/path/to/template.pptx"),
        patch("app.api.routes.layout_registry") as mock_registry,
        patch("app.api.routes.LayoutIntelligenceService") as mock_service_class,
    ):
        # Mock template analysis
        mock_analysis = MagicMock()
        mock_analysis.masters = [MagicMock(layouts=[MagicMock(index=0)])]
        mock_registry.get_or_analyze.return_value = mock_analysis

        # Mock service to raise ValueError (validation error)
        mock_service = AsyncMock()
        mock_service.process.side_effect = ValueError("Invalid LLM response format")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            await layout_intelligence_endpoint(mock_request, valid_request)

        assert exc_info.value.status_code == 422
        assert "Invalid LLM response format" in exc_info.value.detail


@pytest.mark.asyncio
async def test_layout_intelligence_generic_error(mock_request, valid_request):
    """Test handling of unexpected errors"""
    with (
        patch("app.api.routes.find_template_by_id", return_value="/path/to/template.pptx"),
        patch("app.api.routes.layout_registry") as mock_registry,
        patch("app.api.routes.LayoutIntelligenceService") as mock_service_class,
    ):
        # Mock template analysis
        mock_analysis = MagicMock()
        mock_analysis.masters = [MagicMock(layouts=[MagicMock(index=0)])]
        mock_registry.get_or_analyze.return_value = mock_analysis

        # Mock service to raise generic exception
        mock_service = AsyncMock()
        mock_service.process.side_effect = Exception("Unexpected error")
        mock_service_class.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            await layout_intelligence_endpoint(mock_request, valid_request)

        assert exc_info.value.status_code == 500
        assert "Layout intelligence processing failed" in exc_info.value.detail


@pytest.mark.asyncio
async def test_layout_intelligence_empty_text(mock_request):
    """Test validation error for empty text"""
    # Pydantic validation should catch this before endpoint
    with pytest.raises(ValidationError):
        LayoutIntelligenceRequest(text="", template_id="test")


@pytest.mark.asyncio
async def test_layout_intelligence_text_too_long(mock_request):
    """Test validation error for text exceeding max length"""
    # Pydantic validation should catch this before endpoint
    with pytest.raises(ValidationError):
        LayoutIntelligenceRequest(text="x" * 10001, template_id="test")


@pytest.mark.asyncio
async def test_layout_intelligence_with_warnings(mock_request, valid_request):
    """Test response includes warnings propagated from service."""
    mock_result = LayoutIntelligenceResult(
        slides=[
            SlideContent(
                layout_index=1,
                title="Test Slide",
                bullet_points=["Point 1"],
            )
        ],
        warnings=["No compatible layout found for layout type 4 (Two-Column), used Title+Bullets instead"],
    )

    with (
        patch("app.api.routes.find_template_by_id", return_value="/path/to/template.pptx"),
        patch("app.api.routes.layout_registry") as mock_registry,
        patch("app.api.routes.LayoutIntelligenceService") as mock_service_class,
    ):
        # Mock template analysis
        mock_analysis = MagicMock()
        mock_analysis.masters = [MagicMock(layouts=[MagicMock(index=0)])]
        mock_registry.get_or_analyze.return_value = mock_analysis

        # Mock service
        mock_service = AsyncMock()
        mock_service.process.return_value = mock_result
        mock_service_class.return_value = mock_service

        # Call endpoint
        response = await layout_intelligence_endpoint(mock_request, valid_request)

        # Assertions
        assert isinstance(response, LayoutIntelligenceResponse)
        assert len(response.warnings) == 1
        assert "Two-Column" in response.warnings[0]


@pytest.mark.asyncio
async def test_layout_intelligence_empty_warnings(mock_request, valid_request, mock_slide_content):
    """Test response has empty warnings when no fallback occurs."""
    with (
        patch("app.api.routes.find_template_by_id", return_value="/path/to/template.pptx"),
        patch("app.api.routes.layout_registry") as mock_registry,
        patch("app.api.routes.LayoutIntelligenceService") as mock_service_class,
    ):
        # Mock template analysis
        mock_analysis = MagicMock()
        mock_analysis.masters = [MagicMock(layouts=[MagicMock(index=0)])]
        mock_registry.get_or_analyze.return_value = mock_analysis

        # Mock service — mock_slide_content has warnings=[]
        mock_service = AsyncMock()
        mock_service.process.return_value = mock_slide_content
        mock_service_class.return_value = mock_service

        # Call endpoint
        response = await layout_intelligence_endpoint(mock_request, valid_request)

        # Assertions
        assert isinstance(response, LayoutIntelligenceResponse)
        assert response.warnings == []
