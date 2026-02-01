from io import BytesIO
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.utils.file_validation import get_safe_filename, validate_template_file


def create_upload_file(filename: str, content: bytes, content_type: str):
    """Helper to create a mock UploadFile"""
    file = MagicMock()
    file.filename = filename
    file.content_type = content_type
    file.file = BytesIO(content)

    # Make read async
    async def async_read():
        return content

    # Make seek async
    async def async_seek(pos):
        return file.file.seek(pos)

    file.read = async_read
    file.seek = async_seek
    return file


@pytest.mark.asyncio
async def test_validate_valid_file():
    """Test validation of valid PPTX file"""
    # Use correct PPTX magic bytes (ZIP format: PK\x03\x04)
    content = b"PK\x03\x04" + b"\x00" * 1000  # Mock PPTX content with correct magic bytes
    file = create_upload_file(
        "test.pptx", content, "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )

    result = await validate_template_file(file)
    assert result == content


@pytest.mark.asyncio
async def test_validate_invalid_extension():
    """Test rejection of invalid file extension"""
    file = create_upload_file("test.pdf", b"content", "application/pdf")

    with pytest.raises(HTTPException) as exc_info:
        await validate_template_file(file)

    assert exc_info.value.status_code == 400
    assert "Invalid file type" in exc_info.value.detail


@pytest.mark.asyncio
async def test_validate_invalid_mime_type():
    """Test rejection of invalid MIME type"""
    file = create_upload_file("test.pptx", b"content", "application/pdf")

    with pytest.raises(HTTPException) as exc_info:
        await validate_template_file(file)

    assert exc_info.value.status_code == 400
    assert "Invalid content type" in exc_info.value.detail


@pytest.mark.asyncio
async def test_validate_file_too_large():
    """Test rejection of oversized file"""
    large_content = b"x" * (11 * 1024 * 1024)  # 11MB
    file = create_upload_file(
        "test.pptx", large_content, "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )

    with pytest.raises(HTTPException) as exc_info:
        await validate_template_file(file)

    assert exc_info.value.status_code == 413
    assert "too large" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_validate_empty_file():
    """Test rejection of empty file"""
    file = create_upload_file(
        "test.pptx", b"", "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )

    with pytest.raises(HTTPException) as exc_info:
        await validate_template_file(file)

    assert exc_info.value.status_code == 400
    assert "Empty file" in exc_info.value.detail


@pytest.mark.asyncio
async def test_validate_no_filename():
    """Test rejection when no filename provided"""
    file = create_upload_file(
        None, b"content", "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )

    with pytest.raises(HTTPException) as exc_info:
        await validate_template_file(file)

    assert exc_info.value.status_code == 400
    assert "No filename provided" in exc_info.value.detail


def test_safe_filename_basic():
    """Test basic filename sanitization"""
    assert get_safe_filename("test.pptx") == "test.pptx"
    assert get_safe_filename("my template.pptx") == "my_template.pptx"


def test_safe_filename_path_traversal():
    """Test prevention of path traversal"""
    assert get_safe_filename("../../etc/passwd") == "passwd"
    assert get_safe_filename("/etc/passwd") == "passwd"
    # On Unix systems, backslashes are valid filename characters
    result = get_safe_filename("..\\..\\windows\\system32")
    # Just verify it doesn't contain path separators
    assert "/" not in result
    assert result != "..\\..\\windows\\system32"  # Should be sanitized


def test_safe_filename_special_chars():
    """Test removal of special characters"""
    assert get_safe_filename("test@#$.pptx") == "test.pptx"
    assert get_safe_filename("file<>name.pptx") == "filename.pptx"
    assert get_safe_filename("file:name.pptx") == "filename.pptx"


def test_safe_filename_length_limit():
    """Test filename length limiting"""
    long_name = "a" * 300 + ".pptx"
    result = get_safe_filename(long_name)
    assert len(result) <= 255
    assert result.endswith(".pptx")


def test_safe_filename_unicode():
    """Test handling of unicode characters"""
    # Unicode characters should be preserved
    result = get_safe_filename("テスト.pptx")
    assert ".pptx" in result
