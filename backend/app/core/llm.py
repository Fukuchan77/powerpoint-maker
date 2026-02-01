import os
from typing import Any, TypeVar

from beeai_framework.backend.chat import ChatModel
from tenacity import after_log, before_sleep_log, retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


# LLM related exceptions
class LLMError(Exception):
    """Base exception for LLM-related errors"""

    pass


class LLMTimeoutError(LLMError):
    """LLM request timeout"""

    pass


class LLMRateLimitError(LLMError):
    """LLM rate limit exceeded"""

    pass


class LLMConnectionError(LLMError):
    """LLM connection error"""

    pass


def create_retry_decorator(
    max_attempts: int = 3, min_wait: float = 4, max_wait: float = 10, exceptions: tuple = (Exception,)
):
    """Create a retry decorator with exponential backoff

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
        exceptions: Tuple of exceptions to retry on

    Returns:
        Retry decorator
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        before_sleep=before_sleep_log(logger, "WARNING"),
        after=after_log(logger, "INFO"),
        reraise=True,
    )


# Default retry decorator
llm_retry = create_retry_decorator(
    max_attempts=3,
    min_wait=4,
    max_wait=10,
    exceptions=(
        LLMTimeoutError,
        LLMConnectionError,
        LLMRateLimitError,
        ConnectionError,
        TimeoutError,
    ),
)


def get_llm() -> ChatModel:
    """Get LLM instance with error handling

    Returns:
        ChatModel instance

    Raises:
        LLMError: If LLM initialization fails
    """
    try:
        provider = os.getenv("LLM_PROVIDER", "ollama").lower()
        model_name = os.getenv("LLM_MODEL", "llama3.1")

        logger.info("initializing_llm", provider=provider, model=model_name)

        if provider == "ollama":
            # Assumes Ollama is running locally on default port if not specified
            return ChatModel.from_name(f"ollama:{model_name}")
        elif provider == "watsonx":
            return ChatModel.from_name(f"watsonx:{model_name}")
        elif provider == "openai":
            return ChatModel.from_name(f"openai:{model_name}")
        else:
            raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")

    except ValueError as e:
        logger.error("llm_initialization_failed", error=str(e), provider=provider)
        raise LLMError(f"Failed to initialize LLM: {e}") from e
    except Exception as e:
        logger.error("llm_initialization_error", error=str(e), provider=provider)
        raise LLMConnectionError(f"Failed to connect to LLM provider: {e}") from e


@llm_retry
async def call_llm_with_retry(llm: ChatModel, prompt: str, **kwargs: Any) -> str:
    """Call LLM with automatic retry on failure

    Args:
        llm: ChatModel instance
        prompt: Input prompt
        **kwargs: Additional arguments to pass to LLM

    Returns:
        LLM response text

    Raises:
        LLMError: If all retry attempts fail
    """
    try:
        logger.debug("calling_llm", prompt_length=len(prompt))

        response = await llm.ainvoke(prompt, **kwargs)

        logger.info("llm_call_success", response_length=len(response))
        return response

    except TimeoutError as e:
        logger.warning("llm_timeout", error=str(e))
        raise LLMTimeoutError(f"LLM request timed out: {e}") from e
    except ConnectionError as e:
        logger.warning("llm_connection_error", error=str(e))
        raise LLMConnectionError(f"Failed to connect to LLM: {e}") from e
    except Exception as e:
        logger.error("llm_call_failed", error=str(e), error_type=type(e).__name__)
        raise LLMError(f"LLM call failed: {e}") from e
