"""Security-related tests"""

import logging
from io import BytesIO

import pytest
from fastapi import FastAPI, UploadFile
from fastapi.testclient import TestClient

from app.core.logging import SensitiveDataFilter, sanitize_dict
from app.middleware.security import SecurityHeadersMiddleware
from app.utils.file_validation import get_safe_filename, validate_template_file


class TestSecurityHeaders:
    """Test security headers middleware"""

    def test_security_headers_present(self):
        """Responses should contain security headers"""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/")
        def read_root():
            return {"Hello": "World"}

        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


class TestFileValidation:
    """Test file upload security validations"""

    @pytest.mark.asyncio
    async def test_validate_magic_bytes_valid_pptx(self):
        """Valid PPTX file with correct magic bytes should pass"""
        # PPTX files start with PK\x03\x04 (ZIP signature)
        content = b"PK\x03\x04" + b"\x00" * 100
        file = UploadFile(
            filename="test.pptx",
            file=BytesIO(content),
            headers={"content-type": "application/vnd.openxmlformats-officedocument.presentationml.presentation"},
        )

        result = await validate_template_file(file)
        assert result == content

    @pytest.mark.asyncio
    async def test_validate_magic_bytes_invalid_pptx(self):
        """File with wrong magic bytes should fail"""
        # Wrong magic bytes (not a ZIP file)
        content = b"INVALID" + b"\x00" * 100
        file = UploadFile(
            filename="test.pptx",
            file=BytesIO(content),
            headers={"content-type": "application/vnd.openxmlformats-officedocument.presentationml.presentation"},
        )

        with pytest.raises(Exception) as exc_info:
            await validate_template_file(file)
        assert "signature" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_file_size_limit(self):
        """File exceeding size limit should fail"""
        # Create file larger than 10MB
        content = b"PK\x03\x04" + b"\x00" * (11 * 1024 * 1024)
        file = UploadFile(
            filename="large.pptx",
            file=BytesIO(content),
            headers={"content-type": "application/vnd.openxmlformats-officedocument.presentationml.presentation"},
        )

        with pytest.raises(Exception) as exc_info:
            await validate_template_file(file)
        assert "too large" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_empty_file(self):
        """Empty file should fail"""
        content = b""
        file = UploadFile(
            filename="empty.pptx",
            file=BytesIO(content),
            headers={"content-type": "application/vnd.openxmlformats-officedocument.presentationml.presentation"},
        )

        with pytest.raises(Exception) as exc_info:
            await validate_template_file(file)
        assert "empty" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_invalid_extension(self):
        """File with invalid extension should fail"""
        content = b"PK\x03\x04" + b"\x00" * 100
        file = UploadFile(
            filename="test.exe", file=BytesIO(content), headers={"content-type": "application/x-msdownload"}
        )

        with pytest.raises(Exception) as exc_info:
            await validate_template_file(file)
        assert "invalid file type" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_invalid_mime_type(self):
        """File with invalid MIME type should fail"""
        content = b"PK\x03\x04" + b"\x00" * 100
        file = UploadFile(
            filename="test.pptx", file=BytesIO(content), headers={"content-type": "application/octet-stream"}
        )

        with pytest.raises(Exception) as exc_info:
            await validate_template_file(file)
        assert "invalid content type" in str(exc_info.value).lower()

    def test_safe_filename_path_traversal(self):
        """Path traversal attempts should be sanitized"""
        dangerous_names = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
        ]

        for dangerous in dangerous_names:
            safe = get_safe_filename(dangerous)
            assert ".." not in safe
            assert "/" not in safe
            assert "\\" not in safe

    def test_safe_filename_special_chars(self):
        """Special characters should be removed"""
        assert get_safe_filename('test<>:"|?*.pptx') == "test.pptx"
        assert get_safe_filename("test file.pptx") == "test_file.pptx"

    def test_safe_filename_length_limit(self):
        """Long filenames should be truncated"""
        long_name = "a" * 300 + ".pptx"
        safe = get_safe_filename(long_name)
        assert len(safe) <= 255


class TestSensitiveDataFiltering:
    """Test sensitive data filtering in logs"""

    def test_sanitize_dict_api_keys(self):
        """API keys should be redacted"""
        data = {"api_key": "secret_key_12345", "ibm_api_key": "watson_key_67890", "other_data": "public_info"}

        sanitized = sanitize_dict(data)
        assert sanitized["api_key"] == "***REDACTED***"
        assert sanitized["ibm_api_key"] == "***REDACTED***"
        assert sanitized["other_data"] == "public_info"

    def test_sanitize_dict_tokens(self):
        """Tokens should be redacted"""
        data = {"access_token": "token_abc123", "refresh_token": "token_xyz789", "user_id": "user123"}

        sanitized = sanitize_dict(data)
        assert sanitized["access_token"] == "***REDACTED***"
        assert sanitized["refresh_token"] == "***REDACTED***"
        assert sanitized["user_id"] == "user123"

    def test_sanitize_dict_passwords(self):
        """Passwords should be redacted"""
        data = {"password": "secret123", "username": "john_doe"}

        sanitized = sanitize_dict(data)
        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["username"] == "john_doe"

    def test_sanitize_dict_nested(self):
        """Nested dictionaries should be sanitized"""
        data = {"user": {"name": "John", "api_key": "secret123"}, "config": {"timeout": 30}}

        sanitized = sanitize_dict(data)
        assert sanitized["user"]["name"] == "John"
        assert sanitized["user"]["api_key"] == "***REDACTED***"
        assert sanitized["config"]["timeout"] == 30

    def test_sanitize_dict_list(self):
        """Lists with dictionaries should be sanitized"""
        data = {"users": [{"name": "John", "token": "abc123"}, {"name": "Jane", "token": "xyz789"}]}

        sanitized = sanitize_dict(data)
        assert sanitized["users"][0]["name"] == "John"
        assert sanitized["users"][0]["token"] == "***REDACTED***"
        assert sanitized["users"][1]["name"] == "Jane"
        assert sanitized["users"][1]["token"] == "***REDACTED***"

    def test_sensitive_data_filter_log_message(self):
        """Log messages should have sensitive data filtered"""
        filter_instance = SensitiveDataFilter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="User logged in with api_key=secret123",
            args=(),
            exc_info=None,
        )

        result = filter_instance.filter(record)
        assert result is True
        assert "secret123" not in record.msg
        assert "***REDACTED***" in record.msg

    def test_sensitive_data_filter_password_pattern(self):
        """Password patterns should be filtered"""
        filter_instance = SensitiveDataFilter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Auth failed: password=mypassword123",
            args=(),
            exc_info=None,
        )

        result = filter_instance.filter(record)
        assert result is True
        assert "mypassword123" not in record.msg
        assert "***REDACTED***" in record.msg

    def test_sensitive_data_filter_authorization_header(self):
        """Authorization headers should be filtered"""
        filter_instance = SensitiveDataFilter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Request headers: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            args=(),
            exc_info=None,
        )

        result = filter_instance.filter(record)
        assert result is True
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in record.msg
        assert "***REDACTED***" in record.msg


class TestCORSConfiguration:
    """Test CORS configuration security"""

    def test_cors_origins_not_wildcard(self):
        """CORS origins should not be wildcard in production"""
        from app.config import settings

        # Ensure CORS is not set to allow all origins
        assert "*" not in settings.cors_origins

        # Ensure origins are specific
        for origin in settings.cors_origins:
            assert origin.startswith("http://") or origin.startswith("https://")
