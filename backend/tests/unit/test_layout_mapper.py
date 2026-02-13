"""Unit tests for LayoutTypeMapper.

Tests the mapping of abstract layout type IDs (1-7) to template-specific layout indices
based on placeholder analysis and fallback logic.
"""

import pytest

from app.schemas import LayoutInfo, LayoutTypeDefinition, PlaceholderInfo
from app.services.layout_mapper import FALLBACK_PRIORITY, LayoutTypeMapper


@pytest.fixture
def mapper():
    """Create a LayoutTypeMapper instance."""
    return LayoutTypeMapper()


@pytest.fixture
def catalog():
    """Create a minimal catalog of layout type definitions."""
    return [
        LayoutTypeDefinition(
            id=1,
            name="Title Slide",
            description="Opening slide",
            primary_placeholders=["TITLE", "SUBTITLE"],
            recommended_bullet_count=(0, 0),
            recommended_text_length=(10, 100),
            max_text_capacity=150,
        ),
        LayoutTypeDefinition(
            id=2,
            name="Title + Bullets",
            description="Standard content slide",
            primary_placeholders=["TITLE", "BODY"],
            recommended_bullet_count=(3, 7),
            recommended_text_length=(100, 500),
            max_text_capacity=800,
        ),
        LayoutTypeDefinition(
            id=3,
            name="Section Header",
            description="Section divider",
            primary_placeholders=["TITLE"],
            recommended_bullet_count=(0, 0),
            recommended_text_length=(10, 80),
            max_text_capacity=120,
        ),
        LayoutTypeDefinition(
            id=4,
            name="Two-Column",
            description="Comparison slide",
            primary_placeholders=["TITLE", "BODY", "BODY"],
            recommended_bullet_count=(4, 10),
            recommended_text_length=(150, 600),
            max_text_capacity=900,
        ),
        LayoutTypeDefinition(
            id=6,
            name="Bullets Only",
            description="Content-dense slide",
            primary_placeholders=["BODY"],
            recommended_bullet_count=(5, 10),
            recommended_text_length=(150, 600),
            max_text_capacity=800,
        ),
        LayoutTypeDefinition(
            id=7,
            name="Summary",
            description="Closing slide",
            primary_placeholders=["TITLE", "BODY"],
            recommended_bullet_count=(3, 5),
            recommended_text_length=(80, 300),
            max_text_capacity=500,
        ),
    ]


@pytest.fixture
def default_template_layouts():
    """Create a default template with all 7 layout types represented."""
    return [
        LayoutInfo(
            index=0,
            name="Title Slide",
            placeholders=[
                PlaceholderInfo(
                    idx=0, name="Title", type="TITLE", width=100, height=20, left=10, top=10, accepts=["text"]
                ),
                PlaceholderInfo(
                    idx=1, name="Subtitle", type="SUBTITLE", width=100, height=15, left=10, top=35, accepts=["text"]
                ),
            ],
        ),
        LayoutInfo(
            index=1,
            name="Title and Content",
            placeholders=[
                PlaceholderInfo(
                    idx=0, name="Title", type="TITLE", width=100, height=15, left=10, top=5, accepts=["text"]
                ),
                PlaceholderInfo(
                    idx=1, name="Content", type="BODY", width=100, height=70, left=10, top=25, accepts=["text"]
                ),
            ],
        ),
        LayoutInfo(
            index=2,
            name="Section Header",
            placeholders=[
                PlaceholderInfo(
                    idx=0, name="Title", type="TITLE", width=100, height=30, left=10, top=35, accepts=["text"]
                ),
            ],
        ),
        LayoutInfo(
            index=3,
            name="Two Content",
            placeholders=[
                PlaceholderInfo(
                    idx=0, name="Title", type="TITLE", width=100, height=15, left=10, top=5, accepts=["text"]
                ),
                PlaceholderInfo(
                    idx=1, name="Content Left", type="BODY", width=45, height=70, left=10, top=25, accepts=["text"]
                ),
                PlaceholderInfo(
                    idx=2, name="Content Right", type="BODY", width=45, height=70, left=60, top=25, accepts=["text"]
                ),
            ],
        ),
        LayoutInfo(
            index=4,
            name="Blank",
            placeholders=[],
        ),
        LayoutInfo(
            index=5,
            name="Content Only",
            placeholders=[
                PlaceholderInfo(
                    idx=0, name="Content", type="BODY", width=100, height=85, left=10, top=10, accepts=["text"]
                ),
            ],
        ),
    ]


@pytest.fixture
def minimal_template_layouts():
    """Create a minimal template with only one layout."""
    return [
        LayoutInfo(
            index=0,
            name="Title and Content",
            placeholders=[
                PlaceholderInfo(
                    idx=0, name="Title", type="TITLE", width=100, height=15, left=10, top=5, accepts=["text"]
                ),
                PlaceholderInfo(
                    idx=1, name="Content", type="BODY", width=100, height=70, left=10, top=25, accepts=["text"]
                ),
            ],
        ),
    ]


# Test T031: build_mapping() method
def test_build_mapping_default_template(mapper, catalog, default_template_layouts):
    """Test that build_mapping() maps all 7 types with a complete template."""
    mapping = mapper.build_mapping(default_template_layouts, catalog)

    # Should have mappings for all 6 catalog types (we only have 6 in fixture)
    assert len(mapping) == 6
    assert all(1 <= type_id <= 7 for type_id in mapping.keys())
    assert all(0 <= layout_idx < len(default_template_layouts) for layout_idx in mapping.values())

    # Verify specific expected mappings based on placeholder matching
    assert mapping[1] == 0  # Title Slide → index 0 (TITLE + SUBTITLE)
    assert mapping[2] == 1  # Title + Bullets → index 1 (TITLE + BODY)
    assert mapping[3] == 2  # Section Header → index 2 (TITLE only)
    assert mapping[4] == 3  # Two-Column → index 3 (TITLE + BODY + BODY)
    assert mapping[6] == 5  # Bullets Only → index 5 (BODY only)
    assert mapping[7] == 1  # Summary → index 1 (TITLE + BODY, same as type 2)


def test_scoring_placeholder_type_overlap(mapper, catalog):
    """Test that placeholder type overlap gives highest score."""
    # Create a layout with exact TITLE+BODY match
    layouts = [
        LayoutInfo(
            index=0,
            name="Perfect Match",
            placeholders=[
                PlaceholderInfo(
                    idx=0, name="Title", type="TITLE", width=100, height=15, left=10, top=5, accepts=["text"]
                ),
                PlaceholderInfo(
                    idx=1, name="Body", type="BODY", width=100, height=70, left=10, top=25, accepts=["text"]
                ),
            ],
        ),
        LayoutInfo(
            index=1,
            name="Partial Match",
            placeholders=[
                PlaceholderInfo(
                    idx=0, name="Title", type="TITLE", width=100, height=15, left=10, top=5, accepts=["text"]
                ),
            ],
        ),
    ]

    # Type 2 (Title + Bullets) should map to index 0 (perfect match)
    mapping = mapper.build_mapping(layouts, catalog)
    assert mapping[2] == 0


def test_scoring_placeholder_count_penalty(mapper, catalog):
    """Test that extra placeholders reduce score."""
    layouts = [
        LayoutInfo(
            index=0,
            name="Exact Count",
            placeholders=[
                PlaceholderInfo(
                    idx=0, name="Title", type="TITLE", width=100, height=15, left=10, top=5, accepts=["text"]
                ),
                PlaceholderInfo(
                    idx=1, name="Body", type="BODY", width=100, height=70, left=10, top=25, accepts=["text"]
                ),
            ],
        ),
        LayoutInfo(
            index=1,
            name="Extra Placeholders",
            placeholders=[
                PlaceholderInfo(
                    idx=0, name="Title", type="TITLE", width=100, height=15, left=10, top=5, accepts=["text"]
                ),
                PlaceholderInfo(
                    idx=1, name="Body", type="BODY", width=100, height=70, left=10, top=25, accepts=["text"]
                ),
                PlaceholderInfo(
                    idx=2, name="Picture", type="PICTURE", width=50, height=50, left=10, top=10, accepts=["image"]
                ),
                PlaceholderInfo(
                    idx=3, name="Footer", type="FOOTER", width=100, height=5, left=10, top=95, accepts=["text"]
                ),
            ],
        ),
    ]

    # Type 2 should prefer index 0 (exact count) over index 1 (extra placeholders)
    mapping = mapper.build_mapping(layouts, catalog)
    assert mapping[2] == 0


def test_scoring_name_keyword_bonus(mapper, catalog):
    """Test that layout name keywords add bonus score."""
    layouts = [
        LayoutInfo(
            index=0,
            name="Generic Layout",
            placeholders=[
                PlaceholderInfo(
                    idx=0, name="Title", type="TITLE", width=100, height=15, left=10, top=5, accepts=["text"]
                ),
            ],
        ),
        LayoutInfo(
            index=1,
            name="Section Header Layout",  # Contains "Section" keyword
            placeholders=[
                PlaceholderInfo(
                    idx=0, name="Title", type="TITLE", width=100, height=15, left=10, top=5, accepts=["text"]
                ),
            ],
        ),
    ]

    # Type 3 (Section Header) should prefer index 1 due to name match
    mapping = mapper.build_mapping(layouts, catalog)
    assert mapping[3] == 1


def test_build_mapping_minimal_template(mapper, catalog, minimal_template_layouts):
    """Test that minimal template maps all types to the single available layout."""
    mapping = mapper.build_mapping(minimal_template_layouts, catalog)

    # All types should map to index 0 (the only layout)
    assert len(mapping) == 6
    assert all(layout_idx == 0 for layout_idx in mapping.values())


# Test T035: map_type_to_index() with fallback logic
def test_map_type_to_index_exact_match(mapper):
    """Test that direct mapping returns correct index."""
    mapping = {1: 0, 2: 1, 3: 2, 4: 3, 6: 5, 7: 1}

    assert mapper.map_type_to_index(1, mapping) == 0
    assert mapper.map_type_to_index(2, mapping) == 1
    assert mapper.map_type_to_index(4, mapping) == 3


def test_map_type_to_index_fallback_first(mapper, caplog):
    """Test that first fallback is used when primary missing."""
    # Mapping missing type 4 (Two-Column), but has type 2 (first fallback)
    mapping = {1: 0, 2: 1, 3: 2, 6: 5, 7: 1}

    result = mapper.map_type_to_index(4, mapping)

    # Should fall back to type 2 (Title + Bullets)
    assert result == 1

    # Verify warning was logged (use caplog to capture structured logs)
    assert any("layout_type_fallback" in record.message.lower() for record in caplog.records)
    # Verify the log contains the expected type information
    log_messages = " ".join(record.message.lower() for record in caplog.records)
    assert "4" in log_messages and "2" in log_messages


def test_map_type_to_index_fallback_second(mapper, caplog):
    """Test that second fallback is used when first also missing."""
    # Mapping missing type 4 and its first fallback (type 2), but has type 6 (second fallback)
    mapping = {1: 0, 3: 2, 6: 5, 7: 1}

    result = mapper.map_type_to_index(4, mapping)

    # Should fall back to type 6 (Bullets Only)
    assert result == 5

    # Verify warning was logged (use caplog to capture structured logs)
    assert any("layout_type_fallback" in record.message.lower() for record in caplog.records)
    # Verify the log contains the expected type information
    log_messages = " ".join(record.message.lower() for record in caplog.records)
    assert "4" in log_messages and "6" in log_messages


def test_map_type_to_index_fallback_exhausted_raises(mapper):
    """Test that ValueError is raised when no compatible layout exists."""
    # Mapping with only type 1, but trying to map type 4 whose fallback chain doesn't include type 1
    mapping = {1: 0}

    with pytest.raises(ValueError) as exc_info:
        mapper.map_type_to_index(4, mapping)

    error_msg = str(exc_info.value)
    assert "No compatible layout found for type 4" in error_msg
    assert "Attempted fallback chain: [2, 6]" in error_msg


def test_map_type_to_index_logs_warning(mapper, caplog):
    """Test that structlog warning is emitted on fallback."""
    mapping = {1: 0, 2: 1, 3: 2, 6: 5, 7: 1}

    mapper.map_type_to_index(4, mapping)

    # Verify warning was logged (use caplog to capture structured logs)
    assert any("layout_type_fallback" in record.message.lower() or "fallback" in record.message.lower() for record in caplog.records)


def test_fallback_priority_matrix_defined():
    """Test that FALLBACK_PRIORITY matrix is properly defined."""
    # Verify all 7 types have fallback chains
    assert len(FALLBACK_PRIORITY) == 7
    assert all(1 <= type_id <= 7 for type_id in FALLBACK_PRIORITY.keys())

    # Verify expected fallback chains from design doc
    assert FALLBACK_PRIORITY[1] == [2, 3]
    assert FALLBACK_PRIORITY[2] == [6, 7]
    assert FALLBACK_PRIORITY[3] == [1, 2]
    assert FALLBACK_PRIORITY[4] == [2, 6]
    assert FALLBACK_PRIORITY[5] == [2, 6]
    assert FALLBACK_PRIORITY[6] == [2, 7]
    assert FALLBACK_PRIORITY[7] == [2, 6]


# Made with Bob
