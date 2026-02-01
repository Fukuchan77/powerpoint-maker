"""Advanced tests for LLM module to increase coverage from 67% to 85%+"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.llm import (
    LLMConnectionError,
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
    call_llm_with_retry,
    create_retry_decorator,
    get_llm,
)


class TestCallLLMWithRetry:
    """Test suite for call_llm_with_retry function"""

    @pytest.mark.asyncio
    async def test_successful_llm_call(self):
        """Test successful LLM call returns response"""
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value="Test response")

        result = await call_llm_with_retry(mock_llm, "Test prompt")

        assert result == "Test response"
        mock_llm.ainvoke.assert_called_once_with("Test prompt")

    @pytest.mark.asyncio
    async def test_successful_call_with_kwargs(self):
        """Test LLM call with additional kwargs"""
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value="Response with params")

        result = await call_llm_with_retry(mock_llm, "Test prompt", temperature=0.7, max_tokens=100)

        assert result == "Response with params"
        mock_llm.ainvoke.assert_called_once_with("Test prompt", temperature=0.7, max_tokens=100)

    @pytest.mark.asyncio
    async def test_generic_exception_conversion(self):
        """Test generic exceptions are converted to LLMError"""
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(side_effect=ValueError("Invalid input"))

        with pytest.raises(LLMError) as exc_info:
            await call_llm_with_retry(mock_llm, "Test prompt")

        assert "LLM call failed" in str(exc_info.value)
        # Generic exceptions should not retry (only specific errors retry)
        assert mock_llm.ainvoke.call_count == 1


class TestCreateRetryDecorator:
    """Test suite for create_retry_decorator function"""

    def test_decorator_creation(self):
        """Test that create_retry_decorator returns a valid decorator"""
        retry_decorator = create_retry_decorator(max_attempts=2, min_wait=1, max_wait=2, exceptions=(ValueError,))

        # Verify it's a callable decorator
        assert callable(retry_decorator)

    def test_decorator_with_custom_exceptions(self):
        """Test creating decorator with custom exception types"""
        retry_decorator = create_retry_decorator(max_attempts=3, exceptions=(TypeError, ValueError))

        # Verify it's created successfully
        assert callable(retry_decorator)

    def test_decorator_with_custom_wait_times(self):
        """Test creating decorator with custom wait configuration"""
        retry_decorator = create_retry_decorator(max_attempts=5, min_wait=0.1, max_wait=1.0, exceptions=(Exception,))

        # Verify it's created successfully
        assert callable(retry_decorator)


class TestLLMErrorClasses:
    """Test suite for LLM error classes"""

    def test_llm_error_base_class(self):
        """Test LLMError base exception"""
        error = LLMError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"

    def test_llm_timeout_error(self):
        """Test LLMTimeoutError inherits from LLMError"""
        error = LLMTimeoutError("Timeout occurred")
        assert isinstance(error, LLMError)
        assert isinstance(error, Exception)
        assert str(error) == "Timeout occurred"

    def test_llm_connection_error(self):
        """Test LLMConnectionError inherits from LLMError"""
        error = LLMConnectionError("Connection failed")
        assert isinstance(error, LLMError)
        assert isinstance(error, Exception)
        assert str(error) == "Connection failed"

    def test_llm_rate_limit_error(self):
        """Test LLMRateLimitError inherits from LLMError"""
        error = LLMRateLimitError("Rate limit exceeded")
        assert isinstance(error, LLMError)
        assert isinstance(error, Exception)
        assert str(error) == "Rate limit exceeded"


class TestGetLLMErrorHandling:
    """Test suite for get_llm error handling"""

    def test_connection_error_on_initialization(self):
        """Test LLMConnectionError when ChatModel initialization fails"""
        with patch.dict("os.environ", {"LLM_PROVIDER": "ollama", "LLM_MODEL": "test"}):
            with patch("app.core.llm.ChatModel.from_name", side_effect=ConnectionError("Cannot connect")):
                with pytest.raises(LLMConnectionError) as exc_info:
                    get_llm()
                assert "Failed to connect to LLM provider" in str(exc_info.value)

    def test_generic_error_on_initialization(self):
        """Test LLMConnectionError on generic initialization error"""
        with patch.dict("os.environ", {"LLM_PROVIDER": "ollama", "LLM_MODEL": "test"}):
            with patch("app.core.llm.ChatModel.from_name", side_effect=RuntimeError("Unexpected error")):
                with pytest.raises(LLMConnectionError) as exc_info:
                    get_llm()
                assert "Failed to connect to LLM provider" in str(exc_info.value)


class TestLLMRetryIntegration:
    """Integration tests for LLM retry behavior"""

    @pytest.mark.asyncio
    async def test_error_handling_without_retry(self):
        """Test that errors are properly converted to LLM-specific exceptions"""
        # Test with generic exception (no retry)
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(side_effect=RuntimeError("Unexpected error"))

        with pytest.raises(LLMError) as exc_info:
            await call_llm_with_retry(mock_llm, "Test prompt")

        assert "LLM call failed" in str(exc_info.value)
        # Should not retry on generic exceptions
        assert mock_llm.ainvoke.call_count == 1
