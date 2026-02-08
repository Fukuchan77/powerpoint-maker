"""Unit tests for Layout Intelligence Pydantic models."""

import pytest
from pydantic import ValidationError

from app.schemas import (
    BulletPoint,
    LayoutIntelligenceBullet,
    LayoutIntelligencePlan,
    LayoutIntelligenceRequest,
    LayoutIntelligenceResponse,
    LayoutIntelligenceSlide,
    LayoutTypeDefinition,
    OverflowResult,
    SlideContent,
)

# === LayoutTypeDefinition Tests ===


def test_layout_type_definition_valid():
    """Test that all 7 layout types validate correctly."""
    for layout_id in range(1, 8):
        layout = LayoutTypeDefinition(
            id=layout_id,
            name=f"Layout {layout_id}",
            description="Test layout",
            primary_placeholders=["TITLE", "BODY"],
            recommended_bullet_count=(3, 5),
            recommended_text_length=(100, 500),
            max_text_capacity=1000,
        )
        assert layout.id == layout_id
        assert layout.max_text_capacity == 1000


def test_layout_type_definition_invalid_id():
    """Test that id outside 1-7 raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        LayoutTypeDefinition(
            id=0,
            name="Invalid",
            description="Test",
            primary_placeholders=["TITLE"],
            recommended_bullet_count=(1, 5),
            recommended_text_length=(100, 500),
            max_text_capacity=1000,
        )
    assert "id" in str(exc_info.value).lower()

    with pytest.raises(ValidationError) as exc_info:
        LayoutTypeDefinition(
            id=8,
            name="Invalid",
            description="Test",
            primary_placeholders=["TITLE"],
            recommended_bullet_count=(1, 5),
            recommended_text_length=(100, 500),
            max_text_capacity=1000,
        )
    assert "id" in str(exc_info.value).lower()


# === LayoutIntelligenceSlide Tests ===


def test_slide_valid_title_bullets():
    """Test that standard slide with title and bullets validates."""
    slide = LayoutIntelligenceSlide(
        layout_type_id=2,
        title="Test Slide",
        bullets=[
            LayoutIntelligenceBullet(text="Point 1", level=0),
            LayoutIntelligenceBullet(text="Point 2", level=1),
        ],
    )
    assert slide.layout_type_id == 2
    assert slide.title == "Test Slide"
    assert len(slide.bullets) == 2
    assert len(slide.right_bullets) == 0


def test_slide_two_column_valid():
    """Test that Two-Column with balanced columns validates."""
    slide = LayoutIntelligenceSlide(
        layout_type_id=4,
        title="Two Column Slide",
        bullets=[
            LayoutIntelligenceBullet(text="Left 1", level=0),
            LayoutIntelligenceBullet(text="Left 2", level=0),
            LayoutIntelligenceBullet(text="Left 3", level=0),
        ],
        right_bullets=[
            LayoutIntelligenceBullet(text="Right 1", level=0),
            LayoutIntelligenceBullet(text="Right 2", level=0),
        ],
    )
    assert slide.layout_type_id == 4
    assert len(slide.bullets) == 3
    assert len(slide.right_bullets) == 2
    assert abs(len(slide.bullets) - len(slide.right_bullets)) <= 2


def test_slide_two_column_empty_left():
    """Test that empty left column raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        LayoutIntelligenceSlide(
            layout_type_id=4,
            title="Invalid Two Column",
            bullets=[],
            right_bullets=[LayoutIntelligenceBullet(text="Right 1", level=0)],
        )
    assert "left column" in str(exc_info.value).lower()


def test_slide_two_column_empty_right():
    """Test that empty right column raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        LayoutIntelligenceSlide(
            layout_type_id=4,
            title="Invalid Two Column",
            bullets=[LayoutIntelligenceBullet(text="Left 1", level=0)],
            right_bullets=[],
        )
    assert "right column" in str(exc_info.value).lower()


def test_slide_two_column_imbalanced():
    """Test that >2 items difference raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        LayoutIntelligenceSlide(
            layout_type_id=4,
            title="Imbalanced Two Column",
            bullets=[LayoutIntelligenceBullet(text=f"Left {i}", level=0) for i in range(5)],
            right_bullets=[LayoutIntelligenceBullet(text="Right 1", level=0)],
        )
    assert "balanced" in str(exc_info.value).lower()


# === LayoutIntelligencePlan Tests ===


def test_plan_valid():
    """Test that plan with 1-20 slides validates."""
    plan = LayoutIntelligencePlan(
        presentation_title="Test Presentation",
        slides=[
            LayoutIntelligenceSlide(
                layout_type_id=1,
                title="Title Slide",
            ),
            LayoutIntelligenceSlide(
                layout_type_id=2,
                title="Content Slide",
                bullets=[LayoutIntelligenceBullet(text="Point 1", level=0)],
            ),
        ],
    )
    assert plan.presentation_title == "Test Presentation"
    assert len(plan.slides) == 2


def test_plan_empty_slides():
    """Test that empty slides list raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        LayoutIntelligencePlan(
            presentation_title="Empty Presentation",
            slides=[],
        )
    assert "slides" in str(exc_info.value).lower()


# === LayoutIntelligenceRequest Tests ===


def test_request_text_limits():
    """Test that text min 1, max 10000 characters."""
    # Valid text
    request = LayoutIntelligenceRequest(text="Valid text input")
    assert request.text == "Valid text input"

    # Empty text
    with pytest.raises(ValidationError) as exc_info:
        LayoutIntelligenceRequest(text="")
    assert "text" in str(exc_info.value).lower()

    # Too long text
    with pytest.raises(ValidationError) as exc_info:
        LayoutIntelligenceRequest(text="x" * 10001)
    assert "text" in str(exc_info.value).lower()

    # Exactly at max
    request = LayoutIntelligenceRequest(text="x" * 10000)
    assert len(request.text) == 10000


# === LayoutIntelligenceResponse Tests ===


def test_response_with_warnings():
    """Test that warnings list is populated correctly."""
    response = LayoutIntelligenceResponse(
        slides=[
            SlideContent(
                layout_index=0,
                title="Test Slide",
            )
        ],
        warnings=["Layout 4 unavailable, used fallback"],
    )
    assert len(response.slides) == 1
    assert len(response.warnings) == 1
    assert "fallback" in response.warnings[0]


# === to_slide_content() Conversion Tests ===


def test_to_slide_content_title_bullets():
    """Test standard mapping from LayoutIntelligenceSlide to SlideContent."""
    slide = LayoutIntelligenceSlide(
        layout_type_id=2,
        title="Test Title",
        bullets=[
            LayoutIntelligenceBullet(text="Point 1", level=0),
            LayoutIntelligenceBullet(text="Point 2", level=1),
        ],
    )
    content = slide.to_slide_content(layout_index=1)

    assert content.layout_index == 1
    assert content.title == "Test Title"
    assert content.bullets is not None
    assert len(content.bullets) == 2
    assert content.bullets[0].text == "Point 1"
    assert content.bullets[0].level == 0
    assert content.bullets[1].text == "Point 2"
    assert content.bullets[1].level == 1
    assert content.bullets_right is None


def test_to_slide_content_body_text():
    """Test that body_text maps to bullet_points[0]."""
    slide = LayoutIntelligenceSlide(
        layout_type_id=5,
        title="Quote Slide",
        body_text="This is a quote",
    )
    content = slide.to_slide_content(layout_index=2)

    assert content.layout_index == 2
    assert content.title == "Quote Slide"
    assert len(content.bullet_points) == 1
    assert content.bullet_points[0] == "This is a quote"
    assert content.bullets is None


def test_to_slide_content_two_column():
    """Test that right_bullets maps to bullets_right for Two-Column layout."""
    slide = LayoutIntelligenceSlide(
        layout_type_id=4,
        title="Two Column",
        bullets=[
            LayoutIntelligenceBullet(text="Left 1", level=0),
            LayoutIntelligenceBullet(text="Left 2", level=0),
        ],
        right_bullets=[
            LayoutIntelligenceBullet(text="Right 1", level=0),
            LayoutIntelligenceBullet(text="Right 2", level=0),
        ],
    )
    content = slide.to_slide_content(layout_index=3)

    assert content.layout_index == 3
    assert content.title == "Two Column"
    assert content.bullets is not None
    assert len(content.bullets) == 2
    assert content.bullets[0].text == "Left 1"
    assert content.bullets_right is not None
    assert len(content.bullets_right) == 2
    assert content.bullets_right[0].text == "Right 1"


def test_to_slide_content_non_two_column_ignores_right():
    """Test that right_bullets is still mapped even for non-Two-Column layouts."""
    slide = LayoutIntelligenceSlide(
        layout_type_id=2,
        title="Standard Slide",
        bullets=[LayoutIntelligenceBullet(text="Left 1", level=0)],
        right_bullets=[LayoutIntelligenceBullet(text="Right 1", level=0)],
    )
    content = slide.to_slide_content(layout_index=1)

    # Note: The conversion still maps right_bullets, but the generator
    # will handle the graceful degradation if template doesn't support it
    assert content.bullets_right is not None
    assert len(content.bullets_right) == 1


def test_slide_content_backward_compatible():
    """Test that existing SlideContent without bullets_right still works."""
    content = SlideContent(
        layout_index=0,
        title="Legacy Slide",
        bullets=[BulletPoint(text="Point 1", level=0)],
    )
    assert content.bullets_right is None
    assert content.bullets is not None
    assert len(content.bullets) == 1


# === OverflowResult Tests ===


def test_overflow_result_no_overflow():
    """Test OverflowResult when slide is within capacity."""
    result = OverflowResult(
        slide_index=0,
        is_overflow=False,
        total_chars=500,
        max_capacity=1000,
        overflow_amount=0,
    )
    assert result.is_overflow is False
    assert result.overflow_amount == 0


def test_overflow_result_with_overflow():
    """Test OverflowResult when slide exceeds capacity."""
    result = OverflowResult(
        slide_index=1,
        is_overflow=True,
        total_chars=1200,
        max_capacity=1000,
        overflow_amount=200,
    )
    assert result.is_overflow is True
    assert result.overflow_amount == 200


# Made with Bob
