from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request

from app.api.routes import (
    analyze_template,
    extract_content,
    generate_presentation,
    get_extracted_image,
    parse_markdown,
    research_topic,
)
from app.schemas import (
    AnalysisMode,
    ContentExtractionResult,
    MarkdownParseRequest,
    MarkdownParseResponse,
    PresentationRequest,
    SlideContent,
)


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
    """Test error when template is not found and default template doesn't exist"""
    mock_request = MagicMock(spec=Request)
    request = PresentationRequest(slides=[], template_filename="nonexistent.pptx")

    with (
        patch("app.api.routes.find_template_by_id", return_value=None),
        patch("os.path.exists", return_value=False),
        patch("app.api.routes.config.UPLOAD_DIR") as mock_dir,
        patch("app.api.routes.config.DEFAULT_TEMPLATE_PATH") as mock_default,
    ):
        mock_dir.__truediv__.return_value.exists.return_value = False
        mock_default.exists.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await generate_presentation(mock_request, request)

        assert exc_info.value.status_code == 404
        assert "Template file not found" in exc_info.value.detail


# === PPTX Enhancement API Endpoints Tests ===


@pytest.mark.asyncio
async def test_extract_content_success():
    """Test successful content extraction"""
    mock_request = MagicMock(spec=Request)
    mock_request.base_url = "http://localhost:8000/"

    mock_file = MagicMock()
    mock_file.filename = "test.pptx"

    mock_result = ContentExtractionResult(
        extraction_id="test-id",
        filename="test.pptx",
        expires_at="2026-02-02T12:00:00",
        slides=[],
        images=[],
        warnings=[],
    )

    with (
        patch("app.api.routes.validate_template_file", return_value=b"content"),
        patch("app.api.routes.config.UPLOAD_DIR") as mock_dir,
        patch("app.api.routes.ContentExtractor") as mock_extractor_class,
    ):
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_dir.__truediv__.return_value = mock_path

        mock_extractor = MagicMock()
        mock_extractor.extract = AsyncMock(return_value=mock_result)
        mock_extractor_class.return_value = mock_extractor

        result = await extract_content(mock_request, mock_file, AnalysisMode.CONTENT)

        assert result.extraction_id == "test-id"
        assert result.filename == "test.pptx"


@pytest.mark.asyncio
async def test_extract_content_validation_error():
    """Test extraction with validation error"""
    mock_request = MagicMock(spec=Request)
    mock_file = MagicMock()

    with patch(
        "app.api.routes.validate_template_file",
        side_effect=HTTPException(status_code=400, detail="Invalid file"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await extract_content(mock_request, mock_file, AnalysisMode.CONTENT)

        assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_extract_content_extraction_error():
    """Test extraction with internal error"""
    mock_request = MagicMock(spec=Request)
    mock_request.base_url = "http://localhost:8000/"
    mock_file = MagicMock()

    with (
        patch("app.api.routes.validate_template_file", return_value=b"content"),
        patch("app.api.routes.config.UPLOAD_DIR") as mock_dir,
        patch("app.api.routes.ContentExtractor") as mock_extractor_class,
    ):
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_dir.__truediv__.return_value = mock_path

        mock_extractor = MagicMock()
        mock_extractor.extract = AsyncMock(side_effect=Exception("Extraction failed"))
        mock_extractor_class.return_value = mock_extractor

        with pytest.raises(HTTPException) as exc_info:
            await extract_content(mock_request, mock_file, AnalysisMode.CONTENT)

        assert exc_info.value.status_code == 500
        assert "Content extraction failed" in exc_info.value.detail


@pytest.mark.asyncio
async def test_parse_markdown_success():
    """Test successful markdown parsing"""
    mock_request = MagicMock(spec=Request)
    body = MarkdownParseRequest(content="# Slide 1\n\n- Point 1\n- Point 2")

    mock_result = MarkdownParseResponse(slides=[], warnings=[])

    with patch("app.api.routes.markdown_parser") as mock_parser:
        mock_parser.parse.return_value = mock_result

        result = await parse_markdown(mock_request, body)

        assert isinstance(result, MarkdownParseResponse)
        mock_parser.parse.assert_called_once_with(body.content)


@pytest.mark.asyncio
async def test_parse_markdown_size_exceeded():
    """Test markdown parsing with content size exceeded"""
    mock_request = MagicMock(spec=Request)

    # Create content larger than MAX_MARKDOWN_SIZE
    with patch("app.api.routes.config.MAX_MARKDOWN_SIZE", 100):
        body = MarkdownParseRequest(content="x" * 200)

        with pytest.raises(HTTPException) as exc_info:
            await parse_markdown(mock_request, body)

        assert exc_info.value.status_code == 400
        assert "exceeds maximum size" in exc_info.value.detail


@pytest.mark.asyncio
async def test_parse_markdown_parsing_error():
    """Test markdown parsing with internal error"""
    mock_request = MagicMock(spec=Request)
    body = MarkdownParseRequest(content="# Test")

    with patch("app.api.routes.markdown_parser") as mock_parser:
        mock_parser.parse.side_effect = Exception("Parse error")

        with pytest.raises(HTTPException) as exc_info:
            await parse_markdown(mock_request, body)

        assert exc_info.value.status_code == 500
        assert "Markdown parsing failed" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_extracted_image_invalid_extraction_id():
    """Test image retrieval with invalid extraction ID"""
    with pytest.raises(HTTPException) as exc_info:
        await get_extracted_image("not-a-uuid", "12345678-1234-1234-1234-123456789abc")

    assert exc_info.value.status_code == 400
    assert "Invalid ID format" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_extracted_image_invalid_image_id():
    """Test image retrieval with invalid image ID"""
    with pytest.raises(HTTPException) as exc_info:
        await get_extracted_image("12345678-1234-1234-1234-123456789abc", "not-a-uuid")

    assert exc_info.value.status_code == 400
    assert "Invalid ID format" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_extracted_image_not_found():
    """Test image retrieval when extraction directory doesn't exist"""
    with patch("app.api.routes.config.EXTRACTED_IMAGES_DIR") as mock_dir:
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_dir.__truediv__.return_value.__truediv__.return_value = mock_path

        with pytest.raises(HTTPException) as exc_info:
            await get_extracted_image(
                "12345678-1234-1234-1234-123456789abc",
                "87654321-4321-4321-4321-cba987654321",
            )

        assert exc_info.value.status_code == 404
        assert "not found or expired" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_extracted_image_success(tmp_path):
    """Test successful image retrieval"""
    # Create test image directory structure
    extraction_id = "12345678-1234-1234-1234-123456789abc"
    image_id = "87654321-4321-4321-4321-cba987654321"
    images_dir = tmp_path / extraction_id / "images"
    images_dir.mkdir(parents=True)

    # Create a test image file
    test_image = images_dir / f"{image_id}.png"
    test_image.write_bytes(b"fake image data")

    with patch("app.api.routes.config.EXTRACTED_IMAGES_DIR", tmp_path):
        response = await get_extracted_image(extraction_id, image_id)

        assert response.path == str(test_image)
        assert response.media_type == "image/png"


@pytest.mark.asyncio
async def test_get_extracted_image_missing_file(tmp_path):
    """Test image retrieval when image file is missing"""
    extraction_id = "12345678-1234-1234-1234-123456789abc"
    image_id = "87654321-4321-4321-4321-cba987654321"
    images_dir = tmp_path / extraction_id / "images"
    images_dir.mkdir(parents=True)

    # Don't create the image file

    with patch("app.api.routes.config.EXTRACTED_IMAGES_DIR", tmp_path):
        with pytest.raises(HTTPException) as exc_info:
            await get_extracted_image(extraction_id, image_id)

        assert exc_info.value.status_code == 404
        assert "Image not found" in exc_info.value.detail
