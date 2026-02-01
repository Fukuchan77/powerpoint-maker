from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, Request

from app.api.routes import analyze_template, generate_presentation, research_topic
from app.schemas import PresentationRequest, SlideContent


@pytest.mark.asyncio
async def test_analyze_template_save_error():
    """Test error handling when saving template file fails"""
    mock_request = MagicMock(spec=Request)
    mock_file = MagicMock()
    mock_file.filename = "test.pptx"
    mock_file.content_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

    # Mock validate_template_file to return content
    with (
        patch("app.api.routes.validate_template_file", return_value=b"content"),
        patch("builtins.open", side_effect=IOError("Write failed")),
        patch("app.api.routes.config.UPLOAD_DIR") as mock_dir,
    ):
        mock_dir.__truediv__.return_value = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await analyze_template(mock_request, mock_file)

        assert exc_info.value.status_code == 500
        assert "Failed to save template file" in exc_info.value.detail


@pytest.mark.asyncio
async def test_analyze_template_analysis_error():
    """Test error handling when template analysis fails"""
    mock_request = MagicMock(spec=Request)
    mock_file = MagicMock()
    mock_file.filename = "test.pptx"
    mock_file.content_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

    mock_path = MagicMock()
    mock_path.exists.return_value = True

    with (
        patch("app.api.routes.validate_template_file", return_value=b"content"),
        patch("builtins.open", MagicMock()),
        patch("app.api.routes.config.UPLOAD_DIR") as mock_dir,
        patch("app.api.routes.layout_registry") as mock_registry,
    ):
        mock_dir.__truediv__.return_value = mock_path
        mock_registry.get_or_analyze.side_effect = Exception("Analysis failed")

        with pytest.raises(HTTPException) as exc_info:
            await analyze_template(mock_request, mock_file)

        assert exc_info.value.status_code == 500
        assert "Failed to analyze template structure" in exc_info.value.detail
        # Verify file cleanup was attempted
        mock_path.unlink.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_template_unexpected_error():
    """Test handling of unexpected errors in analyze_template"""
    mock_request = MagicMock(spec=Request)
    mock_file = MagicMock()

    # Force an unexpected error early (e.g. during logging or validation setup)
    with patch("app.api.routes.validate_template_file", side_effect=Exception("Unexpected boom")):
        with pytest.raises(HTTPException) as exc_info:
            await analyze_template(mock_request, mock_file)

        assert exc_info.value.status_code == 500
        assert "An unexpected error occurred" in exc_info.value.detail


@pytest.mark.asyncio
async def test_research_topic_unexpected_error():
    """Test unexpected error handling in research_topic"""
    mock_request = MagicMock(spec=Request)
    with patch("app.api.routes.researcher") as mock_researcher:
        mock_researcher.research.side_effect = Exception("Research boom")

        with pytest.raises(HTTPException) as exc_info:
            await research_topic(mock_request, "test topic")

        assert exc_info.value.status_code == 500
        assert "Research boom" in exc_info.value.detail


@pytest.mark.asyncio
async def test_generate_presentation_error():
    """Test error handling in generate_presentation"""
    mock_request = MagicMock(spec=Request)
    request = PresentationRequest(
        slides=[SlideContent(title="Test Slide", bullet_points=["Point 1"], layout_index=0)],
        template_filename="test.pptx",
    )

    with (
        patch("app.api.routes.find_template_by_id", return_value=None),
        patch("os.path.exists", return_value=True),
        patch("os.path.isabs", return_value=True),
        patch("app.api.routes.generator") as mock_generator,
    ):
        mock_generator.generate.side_effect = Exception("Generation failed")

        with pytest.raises(HTTPException) as exc_info:
            await generate_presentation(mock_request, request)

        assert exc_info.value.status_code == 500
        assert "Generation failed: Generation failed" in exc_info.value.detail


@pytest.mark.asyncio
async def test_generate_presentation_template_not_found():
    """Test error when template is not found"""
    mock_request = MagicMock(spec=Request)
    request = PresentationRequest(slides=[], template_filename="nonexistent.pptx")

    with (
        patch("app.api.routes.find_template_by_id", return_value=None),
        patch("os.path.exists", return_value=False),
        patch("app.api.routes.config.UPLOAD_DIR") as mock_dir,
    ):
        mock_dir.__truediv__.return_value.exists.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await generate_presentation(mock_request, request)

        assert exc_info.value.status_code == 404
        assert "Template file not found" in exc_info.value.detail
