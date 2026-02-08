"""Unit tests for LayoutTemplateCatalog."""

import pytest

from app.services.layout_catalog import LAYOUT_CATALOG, LayoutTemplateCatalog


class TestLayoutCatalog:
    """Test the LayoutTemplateCatalog class."""

    @pytest.fixture
    def catalog(self):
        """Create a LayoutTemplateCatalog instance."""
        return LayoutTemplateCatalog()

    def test_catalog_returns_7_layouts(self, catalog):
        """Test that get_all_layouts() returns exactly 7 layout definitions."""
        layouts = catalog.get_all_layouts()
        assert len(layouts) == 7

    def test_catalog_ids_sequential(self, catalog):
        """Test that layout IDs are sequential from 1 to 7."""
        layouts = catalog.get_all_layouts()
        ids = [layout.id for layout in layouts]
        assert ids == [1, 2, 3, 4, 5, 6, 7]

    def test_catalog_ids_unique(self, catalog):
        """Test that all layout IDs are unique."""
        layouts = catalog.get_all_layouts()
        ids = [layout.id for layout in layouts]
        assert len(ids) == len(set(ids))

    def test_get_layout_by_id_valid(self, catalog):
        """Test that get_layout_by_id() returns correct definition for each ID 1-7."""
        for layout_id in range(1, 8):
            layout = catalog.get_layout_by_id(layout_id)
            assert layout.id == layout_id
            assert layout.name is not None
            assert layout.description is not None

    def test_get_layout_by_id_invalid_raises(self, catalog):
        """Test that get_layout_by_id() raises ValueError for invalid IDs."""
        invalid_ids = [0, 8, -1, 100]
        for invalid_id in invalid_ids:
            with pytest.raises(ValueError, match=f"Invalid layout_type_id: {invalid_id}"):
                catalog.get_layout_by_id(invalid_id)

    def test_catalog_capacities_positive(self, catalog):
        """Test that all max_text_capacity values are positive."""
        layouts = catalog.get_all_layouts()
        for layout in layouts:
            assert layout.max_text_capacity > 0

    def test_catalog_names_unique(self, catalog):
        """Test that all layout names are unique."""
        layouts = catalog.get_all_layouts()
        names = [layout.name for layout in layouts]
        assert len(names) == len(set(names))

    def test_catalog_has_expected_layout_names(self, catalog):
        """Test that catalog contains expected layout type names."""
        layouts = catalog.get_all_layouts()
        names = [layout.name for layout in layouts]

        expected_names = [
            "Title Slide",
            "Title + Bullets",
            "Section Header",
            "Two-Column",
            "Quote/Highlight",
            "Bullets Only",
            "Summary/Conclusion",
        ]

        assert names == expected_names

    def test_two_column_layout_has_two_body_placeholders(self, catalog):
        """Test that Two-Column layout (ID 4) has two BODY placeholders."""
        two_column = catalog.get_layout_by_id(4)
        assert two_column.name == "Two-Column"
        assert two_column.primary_placeholders.count("BODY") == 2

    def test_prompt_context_contains_all_ids(self, catalog):
        """Test that get_catalog_prompt_context() includes all 7 layout IDs."""
        context = catalog.get_catalog_prompt_context()

        for layout_id in range(1, 8):
            assert f"Layout {layout_id}:" in context

    def test_prompt_context_contains_capacities(self, catalog):
        """Test that prompt context includes max capacity values."""
        context = catalog.get_catalog_prompt_context()

        layouts = catalog.get_all_layouts()
        for layout in layouts:
            assert f"Max Capacity: {layout.max_text_capacity}" in context

    def test_prompt_context_format(self, catalog):
        """Test that prompt context has expected structure."""
        context = catalog.get_catalog_prompt_context()

        # Should start with header
        assert context.startswith("Available Layout Types:")

        # Should be non-empty
        assert len(context) > 100

        # Should contain key sections for each layout
        assert "Purpose:" in context
        assert "Placeholders:" in context
        assert "Bullets:" in context
        assert "Text Length:" in context

    def test_prompt_context_includes_layout_names(self, catalog):
        """Test that prompt context includes all layout names."""
        context = catalog.get_catalog_prompt_context()

        layouts = catalog.get_all_layouts()
        for layout in layouts:
            assert layout.name in context

    def test_prompt_context_includes_descriptions(self, catalog):
        """Test that prompt context includes layout descriptions."""
        context = catalog.get_catalog_prompt_context()

        layouts = catalog.get_all_layouts()
        for layout in layouts:
            # Check that at least part of the description is present
            # (descriptions might be long, so we check for the first few words)
            desc_start = layout.description.split()[:3]
            assert any(word in context for word in desc_start)

    def test_get_all_layouts_returns_copy(self, catalog):
        """Test that get_all_layouts() returns a copy, not the original list."""
        layouts1 = catalog.get_all_layouts()
        layouts2 = catalog.get_all_layouts()

        # Should be equal in content
        assert len(layouts1) == len(layouts2)

        # But not the same object
        assert layouts1 is not layouts2

    def test_catalog_constant_has_7_layouts(self):
        """Test that LAYOUT_CATALOG constant has exactly 7 layouts."""
        assert len(LAYOUT_CATALOG) == 7

    def test_catalog_constant_ids_valid(self):
        """Test that LAYOUT_CATALOG has valid IDs (1-7)."""
        ids = [layout.id for layout in LAYOUT_CATALOG]
        assert all(1 <= id <= 7 for id in ids)

    def test_recommended_bullet_counts_valid(self, catalog):
        """Test that recommended bullet counts are valid (min <= max)."""
        layouts = catalog.get_all_layouts()
        for layout in layouts:
            min_bullets, max_bullets = layout.recommended_bullet_count
            assert min_bullets <= max_bullets
            assert min_bullets >= 0
            assert max_bullets >= 0

    def test_recommended_text_lengths_valid(self, catalog):
        """Test that recommended text lengths are valid (min <= max)."""
        layouts = catalog.get_all_layouts()
        for layout in layouts:
            min_length, max_length = layout.recommended_text_length
            assert min_length <= max_length
            assert min_length > 0
            assert max_length > 0

    def test_max_capacity_exceeds_recommended_max(self, catalog):
        """Test that max_text_capacity is >= recommended max text length."""
        layouts = catalog.get_all_layouts()
        for layout in layouts:
            _, max_recommended = layout.recommended_text_length
            assert layout.max_text_capacity >= max_recommended


# Made with Bob
