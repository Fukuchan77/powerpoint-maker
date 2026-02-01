"""Tests for rate limiting middleware"""

from unittest.mock import MagicMock

import pytest
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler


class TestRateLimitMiddleware:
    """Test rate limiting middleware functionality"""

    def _create_mock_rate_limit_exc(self):
        """Create a mock RateLimitExceeded exception"""
        from slowapi.errors import RateLimitExceeded

        # Create a mock Limit object
        mock_limit = MagicMock()
        mock_limit.error_message = None
        mock_limit.limit = "10/minute"

        exc = RateLimitExceeded.__new__(RateLimitExceeded)
        exc.limit = mock_limit
        exc.status_code = 429
        exc.detail = "Rate limit exceeded"
        return exc

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_handler_returns_429(self):
        """Rate limit exceeded handler should return 429 status code"""
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/test",
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)
        exc = self._create_mock_rate_limit_exc()

        response = await rate_limit_exceeded_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_handler_response_content(self):
        """Rate limit exceeded handler should return proper error message"""
        import json

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/research",
            "query_string": b"topic=test",
            "headers": [],
        }
        request = Request(scope)
        exc = self._create_mock_rate_limit_exc()

        response = await rate_limit_exceeded_handler(request, exc)

        # Parse response body
        content = json.loads(response.body.decode())

        assert "error" in content
        assert content["error"] == "Rate limit exceeded"
        assert "detail" in content
        assert "Too many requests" in content["detail"]

    def test_limiter_configuration(self):
        """Limiter should be configured with correct defaults"""
        assert limiter is not None
        assert limiter._default_limits is not None

    def test_limiter_key_func(self):
        """Limiter should use remote address as key function"""
        from slowapi.util import get_remote_address

        assert limiter._key_func == get_remote_address
