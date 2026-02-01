"""Tests for application lifecycle events in app/main.py"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


def test_root_endpoint():
    """Test the root endpoint returns correct message"""
    from app.main import app

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello from PowerPoint Generator Agent"}


def test_health_check_endpoint():
    """Test the health check endpoint returns ok status"""
    from app.main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_lifespan_startup():
    """Test that startup event logs application start"""
    from fastapi import FastAPI

    from app.main import lifespan

    mock_app = FastAPI()

    with patch("app.main.logger") as mock_logger:
        async with lifespan(mock_app):
            # Verify startup logging was called
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert call_args[0][0] == "application_started"
            assert "version" in call_args[1]
            assert call_args[1]["version"] == "0.1.0"
            assert "log_level" in call_args[1]
            assert "cors_origins" in call_args[1]


@pytest.mark.asyncio
async def test_lifespan_shutdown():
    """Test that shutdown event logs application shutdown"""
    from fastapi import FastAPI

    from app.main import lifespan

    mock_app = FastAPI()

    with patch("app.main.logger") as mock_logger:
        async with lifespan(mock_app):
            # Clear the startup call
            mock_logger.info.reset_mock()

        # After context exit, shutdown should have been logged
        mock_logger.info.assert_called_once_with("application_shutdown")


@pytest.mark.asyncio
async def test_lifespan_full_cycle():
    """Test complete startup and shutdown cycle"""
    from fastapi import FastAPI

    from app.main import lifespan

    mock_app = FastAPI()

    with patch("app.main.logger") as mock_logger:
        async with lifespan(mock_app):
            # During the context, startup should be called
            assert mock_logger.info.call_count == 1
            startup_call = mock_logger.info.call_args_list[0]
            assert startup_call[0][0] == "application_started"

        # After exit, shutdown should be called
        assert mock_logger.info.call_count == 2
        shutdown_call = mock_logger.info.call_args_list[1]
        assert shutdown_call[0][0] == "application_shutdown"


def test_app_configuration():
    """Test that the FastAPI app is configured correctly"""
    from app.main import app

    assert app.title == "PowerPoint Generator Agent"
    assert app.version == "0.1.0"
    # Verify lifespan is set
    assert app.router.lifespan_context is not None


def test_middleware_configuration():
    """Test that middleware is properly configured"""
    from app.main import app

    # Check that middleware is added
    middleware_classes = [m.cls.__name__ for m in app.user_middleware]

    # Should have CORS and Security middleware
    assert "CORSMiddleware" in middleware_classes
    assert "SecurityHeadersMiddleware" in middleware_classes


def test_rate_limiter_configured():
    """Test that rate limiter is configured on app state"""
    from app.main import app

    # Verify limiter is set in app state
    assert hasattr(app.state, "limiter")
    assert app.state.limiter is not None


def test_exception_handlers_configured():
    """Test that exception handlers are configured"""
    from slowapi.errors import RateLimitExceeded

    from app.main import app

    # Verify RateLimitExceeded handler is registered
    assert RateLimitExceeded in app.exception_handlers
