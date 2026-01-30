from typing import List, Optional

from pydantic import BaseModel


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
    layout_index: int
    title: str
    bullet_points: List[str] = []
    bullets: Optional[List[BulletPoint]] = None
    image_url: Optional[str] = None
    image_caption: Optional[str] = None
    chart: Optional[ChartData] = None  # Added chart field
    theme_color: Optional[str] = None  # e.g. "ACCENT_1"


class PresentationPlan(BaseModel):
    topic: str
    slides: List[SlideContent]


class PresentationRequest(BaseModel):
    template_filename: str
    template_id: Optional[str] = None
    slides: List[SlideContent]
    topic: Optional[str] = None
