"""Integration tests for PPTX Enhancement API endpoints.

Tests REQ-4.1.1, REQ-4.1.2, REQ-5.2, REQ-5.3
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestParseMarkdownAPI:
    """Tests for /api/parse-markdown endpoint [REQ-4.1.2, REQ-5.2]."""

    def test_parse_valid_markdown(self):
        """Test parsing valid Markdown returns slides."""
        payload = {"content": "# Presentation\n\n## Slide 1\n- Point A\n- Point B"}
        response = client.post("/api/parse-markdown", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["presentation_title"] == "Presentation"
        assert len(data["slides"]) == 1
        assert data["slides"][0]["title"] == "Slide 1"

    def test_parse_empty_content_returns_400(self):
        """Test that empty content returns 400 with structured error [REQ-5.2]."""
        payload = {"content": ""}
        response = client.post("/api/parse-markdown", json=payload)

        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["error_code"] == "MARKDOWN_SYNTAX_ERROR"
        assert "Empty" in detail["message"]
        assert "line" in detail["location"]
        assert "column" in detail["location"]
        assert detail["location"]["line"] == 1
        assert detail["location"]["column"] == 1

    def test_parse_whitespace_only_returns_400(self):
        """Test that whitespace-only content returns 400."""
        payload = {"content": "   \n\n  "}
        response = client.post("/api/parse-markdown", json=payload)

        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["error_code"] == "MARKDOWN_SYNTAX_ERROR"

    def test_parse_no_slides_returns_400(self):
        """Test that content without ## returns 400 [REQ-5.2]."""
        payload = {"content": "# Title\n\nJust some text"}
        response = client.post("/api/parse-markdown", json=payload)

        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["error_code"] == "MARKDOWN_SYNTAX_ERROR"
        assert "No slides found" in detail["message"]
        assert "## Heading" in detail["message"]

    def test_parse_multiple_slides(self):
        """Test parsing multiple slides."""
        payload = {"content": "# Presentation\n\n## Slide 1\n- A\n\n## Slide 2\n- B"}
        response = client.post("/api/parse-markdown", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert len(data["slides"]) == 2

    def test_parse_with_warnings(self):
        """Test that warnings are returned for invalid URLs."""
        payload = {"content": "# Presentation\n\n## Slide\n\n![Image](ftp://invalid.com/img.png)"}
        response = client.post("/api/parse-markdown", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert len(data["warnings"]) > 0

    def test_parse_exceeds_max_size(self):
        """Test that content exceeding max size returns 422 (Pydantic validation)."""
        # Create content larger than MAX_MARKDOWN_SIZE (100KB)
        large_content = "# Title\n\n## Slide\n\n" + ("x" * 110000)
        payload = {"content": large_content}
        response = client.post("/api/parse-markdown", json=payload)

        # Pydantic validates max_length and returns 422
        assert response.status_code == 422


class TestExtractContentAPI:
    """Tests for /api/extract-content endpoint [REQ-4.1.1]."""

    def test_extract_content_mode(self, sample_pptx_with_content):
        """Test content extraction mode."""
        with open(sample_pptx_with_content, "rb") as f:
            response = client.post(
                "/api/extract-content?mode=content",
                files={
                    "file": (
                        sample_pptx_with_content,
                        f,
                        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    )
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "extraction_id" in data
        assert "slides" in data
        assert "images" in data
        assert "warnings" in data
        assert "expires_at" in data

    def test_extract_template_mode(self, sample_pptx):
        """Test template extraction mode."""
        with open(sample_pptx, "rb") as f:
            response = client.post(
                "/api/extract-content?mode=template",
                files={
                    "file": (
                        sample_pptx,
                        f,
                        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    )
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "extraction_id" in data
        assert "slides" in data

    def test_extract_invalid_file_type(self):
        """Test invalid file upload [REQ-6.1]."""
        response = client.post("/api/extract-content", files={"file": ("test.txt", b"dummy", "text/plain")})

        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    def test_extract_empty_file(self):
        """Test empty file upload."""
        response = client.post(
            "/api/extract-content",
            files={
                "file": (
                    "test.pptx",
                    b"",
                    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                )
            },
        )

        assert response.status_code == 400


class TestExtractedImagesAPI:
    """Tests for /api/extracted-images endpoint [REQ-5.3]."""

    def test_get_nonexistent_extraction_returns_404(self):
        """Test 404 for non-existent extraction_id."""
        response = client.get(
            "/api/extracted-images/00000000-0000-0000-0000-000000000000/00000000-0000-0000-0000-000000000000"
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_invalid_uuid_returns_400(self):
        """Test 400 for invalid UUID format."""
        response = client.get("/api/extracted-images/invalid-id/invalid-id")

        assert response.status_code == 400
        assert "Invalid ID format" in response.json()["detail"]

    def test_get_invalid_extraction_id_only(self):
        """Test with invalid extraction_id but valid image_id."""
        response = client.get("/api/extracted-images/invalid/00000000-0000-0000-0000-000000000000")

        assert response.status_code == 400

    def test_get_valid_extraction_invalid_image(self):
        """Test with valid extraction_id but invalid image_id."""
        response = client.get("/api/extracted-images/00000000-0000-0000-0000-000000000000/invalid")

        assert response.status_code == 400


class TestGenerateDefaultTemplate:
    """Tests for default template fallback in /api/generate [REQ-4.2.3]."""

    def test_generate_uses_default_template_when_id_missing(self, sample_pptx):
        """Test that generate uses default template when no ID provided."""
        payload = {"template_filename": "nonexistent.pptx", "slides": [{"layout_index": 0, "title": "Test"}]}

        # Mock DEFAULT_TEMPLATE_PATH to point to our sample
        with patch("app.api.routes.config.DEFAULT_TEMPLATE_PATH") as mock_default:
            mock_default.exists.return_value = True
            mock_default.__str__.return_value = sample_pptx

            response = client.post("/api/generate", json=payload)

            # Should succeed with default template
            assert response.status_code == 200

    def test_generate_template_not_found_without_default(self):
        """Test 404 when template not found and no default exists."""
        payload = {
            "template_id": "non-existent-id",
            "template_filename": "dummy.pptx",
            "slides": [{"layout_index": 0, "title": "Test"}],
        }

        # Mock DEFAULT_TEMPLATE_PATH to not exist
        with patch("app.api.routes.config.DEFAULT_TEMPLATE_PATH") as mock_default:
            mock_default.exists.return_value = False
            response = client.post("/api/generate", json=payload)

        assert response.status_code == 404
        assert "Template file not found" in response.json()["detail"]
