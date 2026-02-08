"""Markdown to SlideContent conversion service.

Implements REQ-3.1.1~REQ-3.2.2
"""

from typing import Optional
from urllib.parse import urlparse

import structlog
from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode

from app.exceptions import MarkdownSyntaxError
from app.schemas import BulletPoint, MarkdownParseResponse, SlideContent

logger = structlog.get_logger(__name__)

ALLOWED_PROTOCOLS = {"http", "https"}
VALID_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"}
MAX_HEADING_LENGTH = 100


class SlideBuilder:
    """Build slide structure from parsed Markdown AST."""

    def __init__(self):
        self.slides: list[dict] = []
        self.current_slide: Optional[dict] = None
        self.presentation_title: Optional[str] = None
        self.warnings: list[str] = []
        self.current_line: int = 0  # Track line number for warnings

    def process_heading(self, text: str, level: int) -> None:
        """Process headings [REQ-3.1.1, REQ-3.1.2]

        level=1: Presentation title
        level=2: Slide separator + slide title
        """
        self._validate_heading_length(text, level)
        if level == 1:
            self.presentation_title = text
        elif level == 2:
            self._finalize_current_slide()
            self.current_slide = {"title": text, "bullets": [], "images": []}

    def process_list_item(self, text: str, level: int = 0) -> None:
        """Process list items with hierarchy [REQ-3.1.3]"""
        if self.current_slide:
            self.current_slide["bullets"].append({"text": text.strip(), "level": level})

    def process_image(self, url: str) -> None:
        """Process image references [REQ-3.1.4]"""
        if self._validate_url(url):
            self._validate_image_extension(url)
            if self.current_slide:
                self.current_slide["images"].append(url)

    def process_code_block(self, code: str) -> None:
        """Process code blocks as plain text [REQ-3.1.5]"""
        if self.current_slide:
            self.current_slide["bullets"].append({"text": code.strip(), "level": 0})

    def _validate_url(self, url: str) -> bool:
        """Validate URL protocol and domain [REQ-6.3]"""
        try:
            parsed = urlparse(url)

            # Check protocol
            if parsed.scheme and parsed.scheme not in ALLOWED_PROTOCOLS:
                self.warnings.append(
                    f"Invalid URL protocol '{parsed.scheme}'. Only {', '.join(ALLOWED_PROTOCOLS)} are supported."
                )
                return False

            # Check domain exists
            if not parsed.netloc:
                self.warnings.append(f"URL missing domain: {url}")
                return False

            return True
        except Exception as e:
            self.warnings.append(f"Invalid URL format: {url} ({str(e)})")
            return False

    def _validate_image_extension(self, url: str) -> None:
        """Validate image file extension."""
        try:
            parsed = urlparse(url)
            path = parsed.path.lower()

            # Check if path has a valid image extension
            has_valid_ext = any(path.endswith(ext) for ext in VALID_IMAGE_EXTENSIONS)

            if not has_valid_ext:
                self.warnings.append(
                    f"Image URL may not have a valid extension. Supported: {', '.join(VALID_IMAGE_EXTENSIONS)}"
                )
        except Exception:
            pass  # URL validation will catch this

    def _validate_heading_length(self, heading: str, level: int) -> None:
        """Validate heading length."""
        if len(heading) > MAX_HEADING_LENGTH:
            heading_type = "Presentation title" if level == 1 else "Slide title"
            self.warnings.append(
                f"{heading_type} exceeds {MAX_HEADING_LENGTH} characters "
                f"({len(heading)} chars). Long headings may not display properly."
            )

    def _finalize_current_slide(self):
        """Save current slide to slides list"""
        if self.current_slide:
            self.slides.append(self.current_slide)

    def finalize(self) -> tuple[list[dict], Optional[str], list[str]]:
        """Finalize and return results"""
        self._finalize_current_slide()
        return self.slides, self.presentation_title, self.warnings


class MarkdownParser:
    """Parse Markdown text to SlideContent array.

    Implements REQ-3.1.1~REQ-3.2.2
    """

    def __init__(self):
        self.logger = structlog.get_logger(__name__)

    def parse(self, content: str) -> MarkdownParseResponse:
        """Parse Markdown and convert to SlideContent [REQ-3.2.2]

        Args:
            content: Markdown text

        Returns:
            MarkdownParseResponse: Parsed result with slides and warnings

        Raises:
            MarkdownSyntaxError: If content is empty or contains no slides [REQ-5.2]
        """
        # Validate input is not empty [REQ-5.2]
        if not content or not content.strip():
            raise MarkdownSyntaxError(
                line=1,
                column=1,
                message="Empty Markdown content. Please provide valid Markdown text.",
            )

        md = MarkdownIt()
        tokens = md.parse(content)
        tree = SyntaxTreeNode(tokens)

        builder = SlideBuilder()
        self._walk_tree(tree, builder)

        raw_slides, title, warnings = builder.finalize()

        # Validate that at least one slide was created [REQ-5.2]
        if len(raw_slides) == 0:
            raise MarkdownSyntaxError(
                line=1,
                column=1,
                message="No slides found. Use '## Heading' to create slides.",
            )

        slides = self._convert_to_slide_content(raw_slides)

        self.logger.info(
            "markdown_parsed",
            slide_count=len(slides),
            title=title,
            warning_count=len(warnings),
        )

        return MarkdownParseResponse(
            presentation_title=title,
            slides=slides,
            warnings=warnings,
        )

    def _walk_tree(self, node: SyntaxTreeNode, builder: SlideBuilder, list_level: int = 0) -> None:
        """Walk the AST and extract content"""
        for child in node.children:
            if child.type == "heading":
                # Get heading level from tag (h1 -> 1, h2 -> 2)
                level = int(child.tag[1]) if child.tag else 0
                text = self._extract_text(child)
                builder.process_heading(text, level)

            elif child.type == "bullet_list":
                self._process_list(child, builder, list_level)

            elif child.type == "ordered_list":
                self._process_list(child, builder, list_level)

            elif child.type == "code_block":
                builder.process_code_block(child.content or "")

            elif child.type == "fence":
                builder.process_code_block(child.content or "")

            elif child.type == "paragraph":
                # Check for images in paragraph
                for inline in child.children:
                    if inline.type == "inline":
                        self._process_inline(inline, builder)

            elif child.children:
                self._walk_tree(child, builder, list_level)

    def _process_list(self, list_node: SyntaxTreeNode, builder: SlideBuilder, level: int) -> None:
        """Process a list (bullet or ordered)"""
        for item in list_node.children:
            if item.type == "list_item":
                # Extract text from the list item
                text = self._extract_list_item_text(item)
                if text:
                    builder.process_list_item(text, level)

                # Check for nested lists
                for child in item.children:
                    if child.type in ("bullet_list", "ordered_list"):
                        self._process_list(child, builder, level + 1)

    def _extract_list_item_text(self, item: SyntaxTreeNode) -> str:
        """Extract text from a list item, excluding nested lists"""
        texts = []
        for child in item.children:
            if child.type == "paragraph":
                texts.append(self._extract_text(child))
            elif child.type == "inline":
                texts.append(self._extract_text(child))
        return " ".join(texts).strip()

    def _process_inline(self, inline: SyntaxTreeNode, builder: SlideBuilder) -> None:
        """Process inline elements for images"""
        for child in inline.children:
            if child.type == "image":
                src = child.attrGet("src")
                if src:
                    builder.process_image(src)

    def _extract_text(self, node: SyntaxTreeNode) -> str:
        """Extract text content from node"""
        if node.type == "text":
            return node.content or ""
        if node.type == "code_inline":
            return node.content or ""

        texts = []
        for child in node.children:
            texts.append(self._extract_text(child))
        return "".join(texts)

    def _convert_to_slide_content(self, raw_slides: list[dict]) -> list[SlideContent]:
        """Convert internal format to SlideContent [REQ-3.2.2]"""
        result = []
        for slide in raw_slides:
            bullets = [BulletPoint(text=b["text"], level=b["level"]) for b in slide.get("bullets", [])]
            result.append(
                SlideContent(
                    layout_index=1,  # Default to Title and Content
                    title=slide.get("title", ""),
                    bullets=bullets if bullets else None,
                    image_url=slide["images"][0] if slide.get("images") else None,
                )
            )
        return result
