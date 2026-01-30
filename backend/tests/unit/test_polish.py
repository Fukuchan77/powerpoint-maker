from unittest.mock import Mock, patch

from app.services.generator import SlidePopulator
from app.services.template import LayoutRegistry, _analyze_file_cached


def test_set_japanese_font_xml():
    """Test standard valid XML structure for Japanese font"""
    populator = SlidePopulator(Mock())

    mock_run = Mock()
    mock_rpr = Mock()
    # Mock XML element behavior
    mock_run._r.get_or_add_rPr.return_value = mock_rpr
    mock_rpr.find.return_value = None  # first time, no a:ea

    # We mock etree.SubElement to verify it's called
    with patch("app.services.generator.etree.SubElement") as mock_sub:
        mock_ea = Mock()
        mock_sub.return_value = mock_ea

        populator.set_japanese_font(mock_run, "Meiryo UI")

        # Verify get_or_add_rPr called
        assert mock_run._r.get_or_add_rPr.called

        # Verify SubElement called with correct args
        # (we can't easily check qn('a:ea') equality due to lxml internals)
        # But we can verify it was called.
        assert mock_sub.called

        # Verify typeface set
        mock_ea.set.assert_called_with("typeface", "Meiryo UI")

        # Verify latin font also set
        assert mock_run.font.name == "Meiryo UI"


def test_template_analysis_caching():
    """Test that template analysis is cached"""

    # We need to test _analyze_file_cached directly or via LayoutRegistry
    # But checking lru_cache behavior requires calling the function multiple times

    # We'll patch Presentation to avoid FS I/O and count calls
    with patch("app.services.template.Presentation") as mock_prs:
        mock_prs.return_value.slide_masters = []

        # Clear cache first
        _analyze_file_cached.cache_clear()

        registry = LayoutRegistry()

        # 1. First call
        res1 = registry.get_or_analyze("path/to/template.pptx", "id_1")
        assert mock_prs.call_count == 1

        # 2. Second call same ID
        res2 = registry.get_or_analyze("path/to/template.pptx", "id_1")
        assert mock_prs.call_count == 1  # Should NOT increase

        assert res1 is res2

        # 3. Different ID - should trigger new analysis
        res3 = registry.get_or_analyze("path/to/template.pptx", "id_2")
        assert mock_prs.call_count == 2
        assert res3 is not None
