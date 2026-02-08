"""Layout Template Catalog for Layout Intelligence.

Provides the canonical definitions of all 7 abstract layout types that the LLM
can select from. These definitions are technology-agnostic and describe layout
purposes, not specific PowerPoint template layouts.
"""

from typing import List

from app.schemas import LayoutTypeDefinition

# Canonical catalog of all 7 abstract layout types
# These are the layout types the LLM can choose from when structuring content
LAYOUT_CATALOG: List[LayoutTypeDefinition] = [
    LayoutTypeDefinition(
        id=1,
        name="Title Slide",
        description="Opening slide with presentation title and optional subtitle. No bullet points.",
        primary_placeholders=["TITLE", "SUBTITLE"],
        recommended_bullet_count=(0, 0),
        recommended_text_length=(10, 100),
        max_text_capacity=150,
    ),
    LayoutTypeDefinition(
        id=2,
        name="Title + Bullets",
        description=(
            "Standard content slide with title and bullet points. "
            "Most common layout for presenting lists, steps, or key points."
        ),
        primary_placeholders=["TITLE", "BODY"],
        recommended_bullet_count=(3, 7),
        recommended_text_length=(100, 500),
        max_text_capacity=800,
    ),
    LayoutTypeDefinition(
        id=3,
        name="Section Header",
        description=(
            "Section divider slide with large title text. Used to introduce new topics or chapters. No bullet points."
        ),
        primary_placeholders=["TITLE"],
        recommended_bullet_count=(0, 0),
        recommended_text_length=(10, 80),
        max_text_capacity=120,
    ),
    LayoutTypeDefinition(
        id=4,
        name="Two-Column",
        description=(
            "Comparison or parallel content slide with title and two side-by-side bullet columns. "
            "Use for comparisons, pros/cons, before/after, or parallel concepts. "
            "Columns should be balanced (max 2 items difference)."
        ),
        primary_placeholders=["TITLE", "BODY", "BODY"],
        recommended_bullet_count=(4, 10),
        recommended_text_length=(150, 600),
        max_text_capacity=900,
    ),
    LayoutTypeDefinition(
        id=5,
        name="Quote/Highlight",
        description=(
            "Emphasis slide with title and single prominent text block. "
            "Use for quotes, key takeaways, or important statements. No bullet points."
        ),
        primary_placeholders=["TITLE", "BODY"],
        recommended_bullet_count=(0, 0),
        recommended_text_length=(20, 200),
        max_text_capacity=300,
    ),
    LayoutTypeDefinition(
        id=6,
        name="Bullets Only",
        description=(
            "Content-dense slide with bullet points but no title. "
            "Use when title is implied from previous context or for continuation slides."
        ),
        primary_placeholders=["BODY"],
        recommended_bullet_count=(5, 10),
        recommended_text_length=(150, 600),
        max_text_capacity=800,
    ),
    LayoutTypeDefinition(
        id=7,
        name="Summary/Conclusion",
        description=(
            "Closing slide with title and concise bullet points summarizing key takeaways. "
            "Similar to Title + Bullets but with emphasis on brevity."
        ),
        primary_placeholders=["TITLE", "BODY"],
        recommended_bullet_count=(3, 5),
        recommended_text_length=(80, 300),
        max_text_capacity=500,
    ),
]


class LayoutTemplateCatalog:
    """Provides access to the canonical layout type definitions.

    This catalog defines the 7 abstract layout types that the LLM can select from
    when structuring content. These are technology-agnostic descriptions that get
    mapped to actual PowerPoint template layouts by the LayoutTypeMapper.
    """

    def __init__(self):
        """Initialize the catalog with the canonical layout definitions."""
        self._catalog = LAYOUT_CATALOG

    def get_all_layouts(self) -> List[LayoutTypeDefinition]:
        """Get all 7 layout type definitions.

        Returns:
            List of all layout type definitions in ID order (1-7)
        """
        return self._catalog.copy()

    def get_layout_by_id(self, layout_type_id: int) -> LayoutTypeDefinition:
        """Get a specific layout type definition by ID.

        Args:
            layout_type_id: Layout type ID (1-7)

        Returns:
            The layout type definition

        Raises:
            ValueError: If layout_type_id is not in range 1-7
        """
        if not 1 <= layout_type_id <= 7:
            raise ValueError(f"Invalid layout_type_id: {layout_type_id}. Must be between 1 and 7.")

        # Find layout by ID (catalog is ordered but we search to be safe)
        for layout in self._catalog:
            if layout.id == layout_type_id:
                return layout

        # Should never reach here if catalog is properly defined
        raise ValueError(f"Layout type {layout_type_id} not found in catalog")

    def get_catalog_prompt_context(self) -> str:
        """Generate formatted catalog description for LLM prompts.

        Returns a formatted string describing all 7 layout types with their
        characteristics. This is used in the LLM prompt to help it select
        appropriate layouts for content.

        Returns:
            Formatted string with all layout descriptions
        """
        lines = ["Available Layout Types:"]
        lines.append("")

        for layout in self._catalog:
            lines.append(f"Layout {layout.id}: {layout.name}")
            lines.append(f"  Purpose: {layout.description}")
            lines.append(f"  Placeholders: {', '.join(layout.primary_placeholders)}")

            min_bullets, max_bullets = layout.recommended_bullet_count
            if max_bullets == 0:
                lines.append("  Bullets: None (text-only layout)")
            else:
                lines.append(f"  Bullets: {min_bullets}-{max_bullets} recommended")

            min_chars, max_chars = layout.recommended_text_length
            lines.append(f"  Text Length: {min_chars}-{max_chars} characters recommended")
            lines.append(f"  Max Capacity: {layout.max_text_capacity} characters total")
            lines.append("")

        return "\n".join(lines)


# Made with Bob
