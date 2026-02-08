from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

# === Enums for PPTX Enhancement ===


class AnalysisMode(str, Enum):
    """PPTX analysis mode [REQ-1.1.1, REQ-1.2.1]"""

    CONTENT = "content"  # Extract content (text, images, charts)
    TEMPLATE = "template"  # Extract layout only


class ContentSource(str, Enum):
    """Content source type [REQ-3.2.1]"""

    WEB_SEARCH = "web_search"
    MARKDOWN = "markdown"
    EXTRACTED = "extracted"


# === Existing Models ===


class PlaceholderInfo(BaseModel):
    idx: int
    name: str
    type: str  # e.g., 'TITLE', 'BODY', 'PICTURE'
    width: int
    height: int
    left: int
    top: int
    accepts: List[str] = []  # e.g., ["text", "image"]


class LayoutInfo(BaseModel):
    index: int
    name: str
    placeholders: List[PlaceholderInfo]


class MasterInfo(BaseModel):
    index: int
    name: str
    layouts: List[LayoutInfo]


class TemplateAnalysisResult(BaseModel):
    filename: str
    template_id: str
    masters: List[MasterInfo] = []


class BulletPoint(BaseModel):
    text: str
    level: int = 0


class ChartSeries(BaseModel):
    name: str  # Series name
    values: List[float]


class ChartData(BaseModel):
    title: str
    categories: List[str]  # X-axis labels
    series: List[ChartSeries]
    type: str = "COLUMN_CLUSTERED"  # Default or Enum: BAR, LINE, PIE


class SlideContent(BaseModel):
    layout_index: int = Field(..., description="Index of the layout to use from the template")
    title: str = Field(..., description="Title of the slide")
    bullet_points: List[str] = Field(default=[], description="Simple bullet points as flat list of strings")
    bullets: Optional[List[BulletPoint]] = Field(
        default=None,
        description="Structured bullet points with hierarchy (level support). Alternative to bullet_points.",
    )
    bullets_right: Optional[List[BulletPoint]] = Field(
        default=None,
        description=(
            "Right column bullet points for Two-Column layouts. Only used when layout has multiple BODY placeholders."
        ),
    )
    image_url: Optional[str] = Field(default=None, description="URL for slide image")
    image_caption: Optional[str] = Field(default=None, description="Caption for the slide image")
    chart: Optional[ChartData] = Field(default=None, description="Chart data for visualization")
    theme_color: Optional[str] = Field(default=None, description="Theme color name (e.g., 'ACCENT_1')")


class PresentationPlan(BaseModel):
    topic: str
    slides: List[SlideContent]


class PresentationRequest(BaseModel):
    template_filename: str
    template_id: Optional[str] = None
    slides: List[SlideContent]
    topic: Optional[str] = None


# === New Models for PPTX Enhancement ===


class ExtractedImage(BaseModel):
    """Extracted image info [REQ-1.1.2]"""

    id: str = Field(..., description="Image unique ID (UUID)")
    filename: str = Field(..., description="Original filename")
    url: str = Field(..., description="Temporary access URL")
    slide_index: int = Field(..., ge=0, description="Source slide number")
    content_type: str = Field(..., description="MIME type")


class ExtractedChart(BaseModel):
    """Extracted chart info [REQ-1.1.4]"""

    slide_index: int = Field(..., ge=0)
    chart_type: str = Field(..., description="Chart type")
    categories: List[str] = Field(default_factory=list)
    series: List[ChartSeries] = Field(default_factory=list)


class ExtractedSlideContent(BaseModel):
    """Extracted slide content [REQ-1.1.1, REQ-1.1.5]"""

    slide_index: int = Field(..., ge=0)
    layout_index: int = Field(..., ge=0)
    title: Optional[str] = None
    body_text: List[str] = Field(default_factory=list)
    bullet_points: List[BulletPoint] = Field(default_factory=list)
    image_refs: List[str] = Field(default_factory=list)
    chart: Optional[ExtractedChart] = None


class ContentExtractionResult(BaseModel):
    """Content extraction result [REQ-1.1.1~REQ-1.1.5]"""

    extraction_id: str = Field(..., description="Extraction session ID")
    filename: str = Field(..., description="Original PPTX filename")
    expires_at: str = Field(..., description="Expiry time (ISO 8601)")
    slides: List[ExtractedSlideContent]
    images: List[ExtractedImage]
    warnings: List[str] = Field(default_factory=list, description="Warnings for skipped elements")


class MarkdownParseRequest(BaseModel):
    """Markdown parse request [REQ-3.1.1~REQ-3.1.5]"""

    content: str = Field(..., max_length=102400, description="Markdown text (max 100KB)")


class MarkdownParseResponse(BaseModel):
    """Markdown parse result [REQ-3.2.2]"""

    presentation_title: Optional[str] = None
    slides: List[SlideContent]
    warnings: List[str] = Field(default_factory=list)


class ExtractContentRequest(BaseModel):
    """Content extraction request"""

    mode: AnalysisMode = Field(..., description="Analysis mode")


# === Layout Intelligence Models ===


class LayoutTypeDefinition(BaseModel):
    """Abstract layout type definition for LLM selection."""

    id: int = Field(..., ge=1, le=7, description="Abstract layout type ID (1-7)")
    name: str = Field(..., description="Layout type name")
    description: str = Field(..., description="Layout purpose description")
    primary_placeholders: List[str] = Field(..., description="Expected placeholder types (TITLE, BODY, PICTURE, etc.)")
    recommended_bullet_count: tuple[int, int] = Field(..., description="Recommended bullet count range (min, max)")
    recommended_text_length: tuple[int, int] = Field(
        ..., description="Recommended text length range in characters (min, max)"
    )
    max_text_capacity: int = Field(..., ge=0, description="Maximum total character count for this layout")


class LayoutIntelligenceBullet(BaseModel):
    """Bullet point with hierarchy for layout intelligence output."""

    text: str = Field(..., min_length=1, max_length=200, description="Bullet text")
    level: int = Field(default=0, ge=0, le=2, description="Indent level (0-2)")


class LayoutIntelligenceSlide(BaseModel):
    """Single slide as output by the LLM during layout intelligence."""

    layout_type_id: int = Field(
        ...,
        ge=1,
        le=7,
        description="Abstract layout type ID (1=Title, 2=Title+Bullets, 3=Section, "
        "4=Two-Column, 5=Quote, 6=Bullets Only, 7=Summary)",
    )
    title: str = Field(..., min_length=1, max_length=100, description="Slide title")
    body_text: Optional[str] = Field(default=None, max_length=800, description="Body text for quote/highlight layouts")
    bullets: List[LayoutIntelligenceBullet] = Field(
        default=[], description="Structured bullet points (left column for Two-Column layout)"
    )
    right_bullets: List[LayoutIntelligenceBullet] = Field(
        default=[],
        description="Right column bullet points. Only used for Two-Column layout (layout_type_id=4). "
        "Ignored for all other layout types.",
    )
    speaker_notes: Optional[str] = Field(default=None, max_length=500, description="Optional speaker notes")

    @model_validator(mode="after")
    def validate_two_column(self) -> "LayoutIntelligenceSlide":
        """Enforce Two-Column constraints at schema level."""
        if self.layout_type_id == 4:
            if not self.bullets:
                raise ValueError("Two-Column layout (layout_type_id=4) requires non-empty bullets (left column)")
            if not self.right_bullets:
                raise ValueError("Two-Column layout (layout_type_id=4) requires non-empty right_bullets (right column)")
            if abs(len(self.bullets) - len(self.right_bullets)) > 2:
                raise ValueError(
                    f"Two-Column layout requires balanced columns (max 2 items difference). "
                    f"Got {len(self.bullets)} left bullets and {len(self.right_bullets)} right bullets."
                )
        return self

    def to_slide_content(self, layout_index: int) -> SlideContent:
        """Convert LayoutIntelligenceSlide to SlideContent for the existing pipeline.

        Mapping rules:
            - layout_type_id → layout_index (resolved via LayoutTypeMapper)
            - title → title
            - body_text → bullet_points[0] (inserted as the first element when present)
            - bullets → bullets (LayoutIntelligenceBullet.text/level → BulletPoint.text/level)
            - right_bullets → bullets_right (Two-Column only; None for other layouts)
            - speaker_notes → discarded (not supported by SlideContent; reserved for future use)

        Two-Column layout (layout_type_id=4) strategy:
            `bullets` maps to `SlideContent.bullets` (left/first BODY placeholder).
            `right_bullets` maps to `SlideContent.bullets_right` (right/second BODY placeholder).
        """
        bullet_points: List[str] = []
        if self.body_text:
            bullet_points.append(self.body_text)

        mapped_bullets: Optional[List[BulletPoint]] = None
        if self.bullets:
            mapped_bullets = [BulletPoint(text=b.text, level=b.level) for b in self.bullets]

        mapped_right_bullets: Optional[List[BulletPoint]] = None
        if self.right_bullets:
            mapped_right_bullets = [BulletPoint(text=b.text, level=b.level) for b in self.right_bullets]

        return SlideContent(
            layout_index=layout_index,
            title=self.title,
            bullet_points=bullet_points,
            bullets=mapped_bullets,
            bullets_right=mapped_right_bullets,
        )


class LayoutIntelligencePlan(BaseModel):
    """Complete presentation structure from LLM.
    Named distinctly from the existing PresentationPlan (schemas.py)
    which is used by the research agent flow.
    """

    presentation_title: str = Field(..., min_length=1, max_length=100, description="Overall presentation title")
    slides: List[LayoutIntelligenceSlide] = Field(
        ..., min_length=1, max_length=20, description="Ordered list of slides"
    )


class LayoutIntelligenceRequest(BaseModel):
    """Request body for layout intelligence endpoint."""

    text: str = Field(..., min_length=1, max_length=10000, description="Raw text input for slide generation")
    template_id: Optional[str] = Field(
        default=None, description="Template ID for layout mapping. If omitted, uses default template."
    )


class LayoutIntelligenceResponse(BaseModel):
    """Response from layout intelligence endpoint."""

    slides: List[SlideContent]
    warnings: List[str] = Field(
        default=[],
        description='e.g., ["Layout 4 (Two-Column) unavailable in template, used Title+Bullets instead"]',
    )


class OverflowResult(BaseModel):
    """Result of overflow validation for a single slide."""

    slide_index: int
    is_overflow: bool
    total_chars: int
    max_capacity: int
    overflow_amount: int = 0  # chars over limit
