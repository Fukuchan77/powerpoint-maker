"""Layout Type Mapper for Layout Intelligence.

Maps abstract layout type IDs (1-7) to template-specific layout indices by analyzing
placeholder structure and applying fallback logic when exact matches aren't available.
"""

from typing import Dict, List

import structlog

from app.schemas import LayoutInfo, LayoutTypeDefinition

logger = structlog.get_logger(__name__)

# Fallback priority matrix: when a layout type isn't available, try these alternatives in order
FALLBACK_PRIORITY: Dict[int, List[int]] = {
    1: [2, 3],  # Title Slide → Title+Bullets → Section Divider
    2: [6, 7],  # Title+Bullets → Bullets Only → Summary
    3: [1, 2],  # Section Divider → Title Slide → Title+Bullets
    4: [2, 6],  # Two-Column → Title+Bullets → Bullets Only
    5: [2, 6],  # Quote/Highlight → Title+Bullets → Bullets Only
    6: [2, 7],  # Bullets Only → Title+Bullets → Summary
    7: [2, 6],  # Summary → Title+Bullets → Bullets Only
}


class LayoutTypeMapper:
    """Maps abstract layout type IDs to template-specific layout indices.

    Uses placeholder analysis to find the best matching template layout for each
    abstract layout type. When exact matches aren't available, applies fallback
    logic to ensure all layout types can be mapped.
    """

    def build_mapping(self, layouts: List[LayoutInfo], catalog: List[LayoutTypeDefinition]) -> Dict[int, int]:
        """Build a mapping from layout_type_id to layout_index.

        Analyzes each template layout's placeholder structure and matches it to
        abstract layout type definitions using a scoring algorithm.

        Args:
            layouts: Template's actual layouts from TemplateAnalyzer.
            catalog: Abstract layout type definitions.

        Returns:
            Dict mapping layout_type_id (1-7) to layout_index.
            If no exact match found, maps to closest available layout.
        """
        mapping: Dict[int, int] = {}

        for layout_type in catalog:
            best_score = -1
            best_index = 0

            for layout in layouts:
                score = self._score_layout_match(layout, layout_type)
                if score > best_score:
                    best_score = score
                    best_index = layout.index

            mapping[layout_type.id] = best_index

            logger.debug(
                "mapped_layout_type",
                layout_type_id=layout_type.id,
                layout_type_name=layout_type.name,
                layout_index=best_index,
                score=best_score,
            )

        return mapping

    def _score_layout_match(self, layout: LayoutInfo, layout_type: LayoutTypeDefinition) -> int:
        """Score how well a template layout matches an abstract layout type.

        Scoring algorithm:
        - +10 points per matching placeholder type
        - -3 points per placeholder count difference
        - +5 points if layout name contains keywords from type name

        Args:
            layout: Template layout to score
            layout_type: Abstract layout type definition

        Returns:
            Score (higher is better)
        """
        score = 0

        # Extract placeholder types from template layout
        template_placeholder_types = [ph.type for ph in layout.placeholders]

        # Count matching placeholder types (+10 per match)
        for expected_type in layout_type.primary_placeholders:
            if expected_type in template_placeholder_types:
                score += 10

        # Penalize placeholder count difference (-3 per extra/missing)
        count_diff = abs(len(template_placeholder_types) - len(layout_type.primary_placeholders))
        score -= count_diff * 3

        # Bonus for name similarity (+5 if keywords match)
        layout_name_lower = layout.name.lower()
        type_name_lower = layout_type.name.lower()

        # Extract keywords from type name (split on spaces and common separators)
        type_keywords = [
            word
            for word in type_name_lower.replace("/", " ").replace("-", " ").split()
            if len(word) > 3  # Only consider words longer than 3 chars
        ]

        for keyword in type_keywords:
            if keyword in layout_name_lower:
                score += 5
                break  # Only apply bonus once

        return score

    def map_type_to_index(self, layout_type_id: int, mapping: Dict[int, int]) -> int:
        """Resolve a single layout_type_id to layout_index using pre-built mapping.

        If the layout_type_id is not in the mapping, tries fallback types in order.
        Logs warnings when fallback is used.

        Args:
            layout_type_id: Abstract layout type ID (1-7)
            mapping: Pre-built mapping from build_mapping()

        Returns:
            Mapped layout_index

        Raises:
            ValueError: If no compatible layout exists after exhausting fallback chain
        """
        # Try direct mapping first
        if layout_type_id in mapping:
            return mapping[layout_type_id]

        # Try fallback chain
        fallback_chain = FALLBACK_PRIORITY.get(layout_type_id, [])

        for fallback_type_id in fallback_chain:
            if fallback_type_id in mapping:
                logger.warning(
                    "layout_type_fallback",
                    requested_type=layout_type_id,
                    fallback_type=fallback_type_id,
                    layout_index=mapping[fallback_type_id],
                    message=(
                        f"Layout type {layout_type_id} not found in template, using fallback type {fallback_type_id}"
                    ),
                )
                return mapping[fallback_type_id]

        # No compatible layout found
        raise ValueError(
            f"No compatible layout found for type {layout_type_id}. Attempted fallback chain: {fallback_chain}"
        )


# Made with Bob
