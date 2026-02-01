from typing import List, Optional

from pydantic import BaseModel, Field


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
