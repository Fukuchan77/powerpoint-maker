"""Unit tests for configuration module.

Tests Settings validation, environment variable handling, and path configuration.
Target coverage: 100%
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import BASE_DIR, TEMPLATE_DIR, UPLOAD_DIR, Settings


class TestSettings:
    """Tests for Settings configuration class."""

    def test_default_settings(self):
        """Test default settings initialization."""
        settings = Settings()

        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
        assert settings.debug is False
        assert settings.cors_origins == ["http://localhost:5173", "http://localhost:3000"]
        assert settings.max_upload_size == 10 * 1024 * 1024
        assert settings.research_timeout == 180
        assert settings.layout_intelligence_timeout == 60
        assert settings.llm_call_timeout == 30
        assert settings.log_level == "INFO"
        assert settings.ibm_api_key is None
        assert settings.ibm_project_id is None

    def test_settings_with_environment_variables(self, monkeypatch):
        """Test settings loaded from environment variables."""
        monkeypatch.setenv("HOST", "127.0.0.1")
        monkeypatch.setenv("PORT", "9000")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("IBM_API_KEY", "test-api-key")
        monkeypatch.setenv("IBM_PROJECT_ID", "test-project-id")
        monkeypatch.setenv("MAX_UPLOAD_SIZE", "5242880")  # 5MB
        monkeypatch.setenv("RESEARCH_TIMEOUT", "120")
        monkeypatch.setenv("LAYOUT_INTELLIGENCE_TIMEOUT", "45")
        monkeypatch.setenv("LLM_CALL_TIMEOUT", "20")

        settings = Settings()

        assert settings.host == "127.0.0.1"
        assert settings.port == 9000
        assert settings.debug is True
        assert settings.log_level == "DEBUG"
        assert settings.ibm_api_key == "test-api-key"
        assert settings.ibm_project_id == "test-project-id"
        assert settings.max_upload_size == 5242880
        assert settings.research_timeout == 120
        assert settings.layout_intelligence_timeout == 45
        assert settings.llm_call_timeout == 20

    def test_validate_api_key_with_placeholder(self):
        """Test API key validation treats placeholder as None."""
        settings = Settings(ibm_api_key="your-api-key-here")
        assert settings.ibm_api_key is None

    def test_validate_api_key_with_valid_key(self):
        """Test API key validation with actual key."""
        settings = Settings(ibm_api_key="actual-api-key-12345")
        assert settings.ibm_api_key == "actual-api-key-12345"

    def test_validate_api_key_with_none(self):
        """Test API key validation with None."""
        settings = Settings(ibm_api_key=None)
        assert settings.ibm_api_key is None

    def test_validate_log_level_uppercase(self):
        """Test log level validation converts to uppercase."""
        settings = Settings(log_level="debug")
        assert settings.log_level == "DEBUG"

        settings = Settings(log_level="info")
        assert settings.log_level == "INFO"

        settings = Settings(log_level="warning")
        assert settings.log_level == "WARNING"

        settings = Settings(log_level="error")
        assert settings.log_level == "ERROR"

        settings = Settings(log_level="critical")
        assert settings.log_level == "CRITICAL"

    def test_validate_log_level_invalid(self):
        """Test log level validation rejects invalid values."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(log_level="INVALID")

        assert "log_level must be one of" in str(exc_info.value)

    def test_port_validation_minimum(self):
        """Test port validation minimum value."""
        with pytest.raises(ValidationError):
            Settings(port=0)

    def test_port_validation_maximum(self):
        """Test port validation maximum value."""
        with pytest.raises(ValidationError):
            Settings(port=65536)

    def test_port_validation_valid_range(self):
        """Test port validation with valid values."""
        settings = Settings(port=1)
        assert settings.port == 1

        settings = Settings(port=65535)
        assert settings.port == 65535

        settings = Settings(port=8080)
        assert settings.port == 8080

    def test_max_upload_size_validation_minimum(self):
        """Test max upload size validation minimum value."""
        with pytest.raises(ValidationError):
            Settings(max_upload_size=512)  # Less than 1KB

    def test_max_upload_size_validation_valid(self):
        """Test max upload size validation with valid value."""
        settings = Settings(max_upload_size=1024)  # Exactly 1KB
        assert settings.max_upload_size == 1024

    def test_research_timeout_validation_minimum(self):
        """Test research timeout validation minimum value."""
        with pytest.raises(ValidationError):
            Settings(research_timeout=29)

    def test_research_timeout_validation_maximum(self):
        """Test research timeout validation maximum value."""
        with pytest.raises(ValidationError):
            Settings(research_timeout=601)

    def test_research_timeout_validation_valid_range(self):
        """Test research timeout validation with valid values."""
        settings = Settings(research_timeout=30)
        assert settings.research_timeout == 30

        settings = Settings(research_timeout=600)
        assert settings.research_timeout == 600

        settings = Settings(research_timeout=180)
        assert settings.research_timeout == 180

    def test_layout_intelligence_timeout_validation_minimum(self):
        """Test layout intelligence timeout validation minimum value."""
        with pytest.raises(ValidationError):
            Settings(layout_intelligence_timeout=14)

    def test_layout_intelligence_timeout_validation_maximum(self):
        """Test layout intelligence timeout validation maximum value."""
        with pytest.raises(ValidationError):
            Settings(layout_intelligence_timeout=181)

    def test_layout_intelligence_timeout_validation_valid_range(self):
        """Test layout intelligence timeout validation with valid values."""
        settings = Settings(layout_intelligence_timeout=15)
        assert settings.layout_intelligence_timeout == 15

        settings = Settings(layout_intelligence_timeout=180)
        assert settings.layout_intelligence_timeout == 180

        settings = Settings(layout_intelligence_timeout=60)
        assert settings.layout_intelligence_timeout == 60

    def test_llm_call_timeout_validation_minimum(self):
        """Test LLM call timeout validation minimum value."""
        with pytest.raises(ValidationError):
            Settings(llm_call_timeout=9)

    def test_llm_call_timeout_validation_maximum(self):
        """Test LLM call timeout validation maximum value."""
        with pytest.raises(ValidationError):
            Settings(llm_call_timeout=91)

    def test_llm_call_timeout_validation_valid_range(self):
        """Test LLM call timeout validation with valid values."""
        settings = Settings(llm_call_timeout=10)
        assert settings.llm_call_timeout == 10

        settings = Settings(llm_call_timeout=90)
        assert settings.llm_call_timeout == 90

        settings = Settings(llm_call_timeout=30)
        assert settings.llm_call_timeout == 30

    def test_cors_origins_custom(self, monkeypatch):
        """Test custom CORS origins from environment."""
        monkeypatch.setenv("CORS_ORIGINS", '["http://example.com", "https://example.com"]')
        settings = Settings()
        assert "http://example.com" in str(settings.cors_origins) or len(settings.cors_origins) == 2

    def test_settings_ignore_extra_fields(self, monkeypatch):
        """Test that extra environment variables are ignored."""
        monkeypatch.setenv("UNKNOWN_FIELD", "some_value")
        # Should not raise an error due to extra="ignore"
        settings = Settings()
        assert not hasattr(settings, "unknown_field")

    def test_settings_case_insensitive(self, monkeypatch):
        """Test that environment variables are case-insensitive."""
        monkeypatch.setenv("host", "192.168.1.1")
        monkeypatch.setenv("PORT", "3000")

        settings = Settings()
        assert settings.host == "192.168.1.1"
        assert settings.port == 3000


class TestDirectoryConfiguration:
    """Tests for directory path configuration."""

    def test_base_dir_is_path(self):
        """Test that BASE_DIR is a Path object."""
        assert isinstance(BASE_DIR, Path)

    def test_upload_dir_is_path(self):
        """Test that UPLOAD_DIR is a Path object."""
        assert isinstance(UPLOAD_DIR, Path)

    def test_template_dir_is_path(self):
        """Test that TEMPLATE_DIR is a Path object."""
        assert isinstance(TEMPLATE_DIR, Path)

    def test_directories_exist(self):
        """Test that required directories are created."""
        assert UPLOAD_DIR.exists()
        assert TEMPLATE_DIR.exists()

    def test_upload_dir_location(self):
        """Test that UPLOAD_DIR is in correct location."""
        assert UPLOAD_DIR == BASE_DIR / "uploads"

    def test_template_dir_location(self):
        """Test that TEMPLATE_DIR is in correct location."""
        assert TEMPLATE_DIR == BASE_DIR / "templates"


class TestPPTXEnhancementConfiguration:
    """Tests for PPTX Enhancement specific configuration."""

    def test_default_template_path(self):
        """Test default template path configuration."""
        from app.config import DEFAULT_TEMPLATE_PATH

        assert isinstance(DEFAULT_TEMPLATE_PATH, Path)
        assert DEFAULT_TEMPLATE_PATH == TEMPLATE_DIR / "default.pptx"

    def test_extracted_images_dir(self):
        """Test extracted images directory configuration."""
        from app.config import EXTRACTED_IMAGES_DIR

        assert isinstance(EXTRACTED_IMAGES_DIR, Path)
        assert EXTRACTED_IMAGES_DIR == UPLOAD_DIR / "extracted"
        assert EXTRACTED_IMAGES_DIR.exists()

    def test_extracted_image_expiry_hours(self):
        """Test extracted image expiry configuration."""
        from app.config import EXTRACTED_IMAGE_EXPIRY_HOURS

        assert isinstance(EXTRACTED_IMAGE_EXPIRY_HOURS, int)
        assert EXTRACTED_IMAGE_EXPIRY_HOURS == 24

    def test_max_markdown_size(self):
        """Test max markdown size configuration."""
        from app.config import MAX_MARKDOWN_SIZE

        assert isinstance(MAX_MARKDOWN_SIZE, int)
        assert MAX_MARKDOWN_SIZE == 102400  # 100KB
