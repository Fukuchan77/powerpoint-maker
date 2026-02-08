"""Unit tests for custom exceptions.

Target coverage: 100% for app/exceptions.py
"""

import pytest

from app.exceptions import ExtractionError, ImageExpiredError, MarkdownSyntaxError


class TestExtractionError:
    """Tests for ExtractionError exception."""

    def test_instantiation(self):
        """Test basic exception instantiation."""
        error = ExtractionError("Content extraction failed")
        assert str(error) == "Content extraction failed"

    def test_inheritance(self):
        """Test that ExtractionError inherits from Exception."""
        error = ExtractionError("test")
        assert isinstance(error, Exception)

    def test_raise_and_catch(self):
        """Test raising and catching ExtractionError."""
        with pytest.raises(ExtractionError) as exc_info:
            raise ExtractionError("Failed to extract content from PPTX")
        assert "Failed to extract content" in str(exc_info.value)


class TestMarkdownSyntaxError:
    """Tests for MarkdownSyntaxError exception."""

    def test_instantiation_with_attributes(self):
        """Test exception with line, column, and message attributes."""
        error = MarkdownSyntaxError(line=10, column=5, message="Invalid heading format")
        assert error.line == 10
        assert error.column == 5
        assert error.message == "Invalid heading format"

    def test_formatted_str_message(self):
        """Test the formatted string representation."""
        error = MarkdownSyntaxError(line=3, column=12, message="Unclosed code block")
        assert str(error) == "Line 3, Column 12: Unclosed code block"

    def test_inheritance(self):
        """Test that MarkdownSyntaxError inherits from Exception."""
        error = MarkdownSyntaxError(line=1, column=1, message="test")
        assert isinstance(error, Exception)

    def test_raise_and_catch(self):
        """Test raising and catching MarkdownSyntaxError."""
        with pytest.raises(MarkdownSyntaxError) as exc_info:
            raise MarkdownSyntaxError(line=5, column=10, message="Missing list marker")
        assert exc_info.value.line == 5
        assert exc_info.value.column == 10
        assert "Missing list marker" in exc_info.value.message

    def test_zero_line_column(self):
        """Test with zero line and column values."""
        error = MarkdownSyntaxError(line=0, column=0, message="Start of file error")
        assert error.line == 0
        assert error.column == 0
        assert "Line 0, Column 0" in str(error)


class TestImageExpiredError:
    """Tests for ImageExpiredError exception."""

    def test_instantiation(self):
        """Test basic exception instantiation."""
        error = ImageExpiredError("Image has expired")
        assert str(error) == "Image has expired"

    def test_inheritance(self):
        """Test that ImageExpiredError inherits from Exception."""
        error = ImageExpiredError("test")
        assert isinstance(error, Exception)

    def test_raise_and_catch(self):
        """Test raising and catching ImageExpiredError."""
        with pytest.raises(ImageExpiredError) as exc_info:
            raise ImageExpiredError("The requested image has expired or been deleted")
        assert "expired" in str(exc_info.value)

    def test_empty_message(self):
        """Test with empty message."""
        error = ImageExpiredError()
        assert isinstance(error, ImageExpiredError)
