"""Unit tests for the Markdown parser service.

Target coverage: 95%
"""

import pytest

from app.services.markdown_parser import MarkdownParser, SlideBuilder


class TestSlideBuilder:
    """Tests for the SlideBuilder class."""

    def test_process_heading_level1_sets_presentation_title(self):
        """Test that H1 heading sets presentation title."""
        builder = SlideBuilder()
        builder.process_heading("My Presentation", 1)
        assert builder.presentation_title == "My Presentation"
        assert len(builder.slides) == 0

    def test_process_heading_level2_creates_slide(self):
        """Test that H2 heading creates a new slide."""
        builder = SlideBuilder()
        builder.process_heading("Slide 1", 2)
        builder._finalize_current_slide()
        assert len(builder.slides) == 1
        assert builder.slides[0]["title"] == "Slide 1"

    def test_multiple_h2_headings_create_multiple_slides(self):
        """Test multiple slides from multiple H2 headings."""
        builder = SlideBuilder()
        builder.process_heading("Slide 1", 2)
        builder.process_heading("Slide 2", 2)
        builder.process_heading("Slide 3", 2)
        _, _, _ = builder.finalize()
        assert len(builder.slides) == 3

    def test_process_list_item_adds_bullet(self):
        """Test that list items are added as bullets."""
        builder = SlideBuilder()
        builder.process_heading("Slide 1", 2)
        builder.process_list_item("Bullet point 1", 0)
        builder.process_list_item("Bullet point 2", 1)
        _, _, _ = builder.finalize()
        assert len(builder.slides[0]["bullets"]) == 2
        assert builder.slides[0]["bullets"][0]["text"] == "Bullet point 1"
        assert builder.slides[0]["bullets"][0]["level"] == 0
        assert builder.slides[0]["bullets"][1]["level"] == 1

    def test_process_list_item_without_slide_is_ignored(self):
        """Test that list items without a current slide are ignored."""
        builder = SlideBuilder()
        builder.process_list_item("Orphan bullet", 0)
        _, _, _ = builder.finalize()
        assert len(builder.slides) == 0

    def test_process_image_adds_to_current_slide(self):
        """Test that valid images are added to current slide."""
        builder = SlideBuilder()
        builder.process_heading("Slide 1", 2)
        builder.process_image("https://example.com/image.png")
        _, _, _ = builder.finalize()
        assert builder.slides[0]["images"] == ["https://example.com/image.png"]

    def test_process_image_rejects_invalid_protocol(self):
        """Test that non-http(s) URLs are rejected."""
        builder = SlideBuilder()
        builder.process_heading("Slide 1", 2)
        builder.process_image("ftp://example.com/image.png")
        _, _, warnings = builder.finalize()
        assert len(builder.slides[0]["images"]) == 0
        assert len(warnings) == 1
        assert "Invalid URL protocol" in warnings[0]

    def test_process_code_block_adds_as_bullet(self):
        """Test that code blocks are added as plain text bullets."""
        builder = SlideBuilder()
        builder.process_heading("Slide 1", 2)
        builder.process_code_block("def hello():\n    print('hello')")
        _, _, _ = builder.finalize()
        assert len(builder.slides[0]["bullets"]) == 1

    def test_finalize_returns_all_data(self):
        """Test that finalize returns slides, title, and warnings."""
        builder = SlideBuilder()
        builder.process_heading("My Title", 1)
        builder.process_heading("Slide 1", 2)
        builder.process_image("ftp://invalid.com/img.png")
        slides, title, warnings = builder.finalize()
        assert title == "My Title"
        assert len(slides) == 1
        assert len(warnings) == 1


class TestMarkdownParser:
    """Tests for the MarkdownParser class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = MarkdownParser()

    def test_parse_simple_presentation(self):
        """Test parsing a simple presentation."""
        markdown = """# My Presentation

## Introduction

This is the introduction.

## Conclusion

Summary of key points.
"""
        result = self.parser.parse(markdown)
        assert result.presentation_title == "My Presentation"
        assert len(result.slides) == 2
        assert result.slides[0].title == "Introduction"
        assert result.slides[1].title == "Conclusion"

    def test_parse_with_bullet_points(self):
        """Test parsing bullet points."""
        markdown = """# Presentation

## Features

- Feature 1
- Feature 2
- Feature 3
"""
        result = self.parser.parse(markdown)
        assert len(result.slides) == 1
        assert result.slides[0].bullets is not None
        assert len(result.slides[0].bullets) == 3
        assert result.slides[0].bullets[0].text == "Feature 1"

    def test_parse_with_nested_bullets(self):
        """Test parsing nested bullet points."""
        markdown = """# Presentation

## Topics

- Main point
  - Sub point 1
  - Sub point 2
- Another main
"""
        result = self.parser.parse(markdown)
        assert result.slides[0].bullets is not None
        # Check that we have bullets with different levels
        levels = [b.level for b in result.slides[0].bullets]
        assert 0 in levels
        assert 1 in levels

    def test_parse_with_image(self):
        """Test parsing image references."""
        markdown = """# Presentation

## Diagram

![Architecture](https://example.com/diagram.png)
"""
        result = self.parser.parse(markdown)
        assert result.slides[0].image_url == "https://example.com/diagram.png"

    def test_parse_with_code_block(self):
        """Test parsing code blocks as plain text."""
        markdown = """# Presentation

## Code Example

```python
def hello():
    print("Hello")
```
"""
        result = self.parser.parse(markdown)
        assert result.slides[0].bullets is not None
        assert len(result.slides[0].bullets) > 0

    def test_parse_empty_content_raises_error(self):
        """Test parsing empty content raises MarkdownSyntaxError."""
        from app.exceptions import MarkdownSyntaxError

        with pytest.raises(MarkdownSyntaxError):
            self.parser.parse("")

    def test_parse_only_title_raises_error(self):
        """Test parsing content with only a title raises error."""
        from app.exceptions import MarkdownSyntaxError

        markdown = "# Just a Title"
        with pytest.raises(MarkdownSyntaxError):
            self.parser.parse(markdown)

    def test_parse_returns_warnings(self):
        """Test that warnings are returned for invalid URLs."""
        markdown = """# Presentation

## Slide

![Invalid](ftp://invalid.com/image.png)
"""
        result = self.parser.parse(markdown)
        assert len(result.warnings) == 1

    def test_slide_layout_index_defaults_to_1(self):
        """Test that slides default to layout index 1."""
        markdown = """# Presentation

## Slide 1
"""
        result = self.parser.parse(markdown)
        assert result.slides[0].layout_index == 1

    def test_parse_ordered_list(self):
        """Test parsing ordered lists."""
        markdown = """# Presentation

## Steps

1. First step
2. Second step
3. Third step
"""
        result = self.parser.parse(markdown)
        assert result.slides[0].bullets is not None
        assert len(result.slides[0].bullets) == 3

    def test_parse_inline_code(self):
        """Test parsing inline code in text."""
        markdown = """# Presentation

## Code

- Use `print()` function
"""
        result = self.parser.parse(markdown)
        assert result.slides[0].bullets is not None
        assert "print()" in result.slides[0].bullets[0].text

    def test_parse_multiple_images_uses_first(self):
        """Test that only the first image is used per slide."""
        markdown = """# Presentation

## Images

![First](https://example.com/first.png)
![Second](https://example.com/second.png)
"""
        result = self.parser.parse(markdown)
        assert result.slides[0].image_url == "https://example.com/first.png"

    def test_response_model_is_valid(self):
        """Test that the response is a valid MarkdownParseResponse."""
        markdown = """# Test

## Slide 1

- Point 1
"""
        result = self.parser.parse(markdown)
        assert hasattr(result, "presentation_title")
        assert hasattr(result, "slides")
        assert hasattr(result, "warnings")


class TestMarkdownParserErrors:
    """Tests for MarkdownParser error handling [REQ-5.2]."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = MarkdownParser()

    def test_parse_empty_content_raises_error(self):
        """Test that empty content raises MarkdownSyntaxError."""
        from app.exceptions import MarkdownSyntaxError

        with pytest.raises(MarkdownSyntaxError) as exc_info:
            self.parser.parse("")

        assert exc_info.value.line == 1
        assert exc_info.value.column == 1
        assert "Empty" in exc_info.value.message

    def test_parse_whitespace_only_raises_error(self):
        """Test that whitespace-only content raises MarkdownSyntaxError."""
        from app.exceptions import MarkdownSyntaxError

        with pytest.raises(MarkdownSyntaxError) as exc_info:
            self.parser.parse("   \n\n  \t  ")

        assert exc_info.value.line == 1
        assert exc_info.value.column == 1
        assert "Empty" in exc_info.value.message

    def test_parse_no_slides_raises_error(self):
        """Test that content without ## headings raises error."""
        from app.exceptions import MarkdownSyntaxError

        markdown = "# Presentation Title\n\nSome text but no slides"
        with pytest.raises(MarkdownSyntaxError) as exc_info:
            self.parser.parse(markdown)

        assert exc_info.value.line == 1
        assert exc_info.value.column == 1
        assert "No slides found" in exc_info.value.message
        assert "## Heading" in exc_info.value.message

    def test_parse_only_h1_no_slides_raises_error(self):
        """Test that content with only H1 heading raises error."""
        from app.exceptions import MarkdownSyntaxError

        markdown = "# Just a Title"
        with pytest.raises(MarkdownSyntaxError) as exc_info:
            self.parser.parse(markdown)

        assert "No slides found" in exc_info.value.message
