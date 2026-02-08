from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

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
