"""Configuration management with validation."""

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore unknown environment variables
    )

    # IBM Watson settings (optional, may not be configured yet)
    ibm_api_key: Optional[str] = Field(
        default=None,
        description="IBM Watson API Key",
    )
    ibm_project_id: Optional[str] = Field(
        default=None,
        description="IBM Watson Project ID",
    )

    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")

    # CORS settings
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        description="Allowed CORS origins",
    )

    # File upload settings
    max_upload_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        ge=1024,  # Minimum 1KB
        description="Maximum upload file size in bytes",
    )

    # Timeout settings
    research_timeout: int = Field(
        default=180,
        ge=30,
        le=600,
        description="Research timeout in seconds",
    )
    layout_intelligence_timeout: int = Field(
        default=60,
        ge=15,
        le=180,
        description="Layout intelligence pipeline timeout in seconds",
    )
    llm_call_timeout: int = Field(
        default=30,
        ge=10,
        le=90,
        description="Individual LLM call timeout in seconds",
    )

    # Logging settings
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    @field_validator("ibm_api_key")
    @classmethod
    def validate_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate API Key format."""
        if v and v == "your-api-key-here":
            return None  # Treat placeholder as None
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper


# Global settings instance
settings = Settings()

# Directory paths
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
TEMPLATE_DIR = BASE_DIR / "templates"

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

# === PPTX Enhancement Configuration ===

# Default template settings [REQ-2.1]
DEFAULT_TEMPLATE_PATH: Path = TEMPLATE_DIR / "default.pptx"

# Temporary image settings [REQ-1.1.3]
EXTRACTED_IMAGE_EXPIRY_HOURS: int = 24
EXTRACTED_IMAGES_DIR: Path = UPLOAD_DIR / "extracted"

# Markdown input settings [REQ-3.1.x]
MAX_MARKDOWN_SIZE: int = 102400  # 100KB

# Ensure extracted images directory exists
EXTRACTED_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
