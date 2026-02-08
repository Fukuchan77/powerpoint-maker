"""Script to create the default PPTX template.

This creates a simple, clean template with 4 standard layouts:
- Title Slide
- Title and Content
- Two Column
- Picture with Caption
"""

from pathlib import Path

from pptx import Presentation
from pptx.util import Inches

# Output path
OUTPUT_PATH = Path(__file__).parent.parent / "templates" / "default.pptx"


def create_default_template():
    """Create a minimal default template."""
    # Start with blank presentation
    prs = Presentation()

    # Set slide dimensions (16:9 widescreen)
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # The built-in layouts are sufficient for our needs:
    # 0: Title Slide
    # 1: Title and Content
    # 2: Section Header
    # 3: Two Content
    # 4: Comparison
    # 5: Title Only
    # 6: Blank
    # 7: Content with Caption
    # 8: Picture with Caption

    # Save the presentation
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUTPUT_PATH))
    print(f"Default template created at: {OUTPUT_PATH}")


if __name__ == "__main__":
    create_default_template()
