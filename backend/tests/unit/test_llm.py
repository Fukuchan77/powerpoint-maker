import os
from unittest.mock import patch

import pytest

from app.core.llm import get_llm


def test_get_llm_default():
    # Test default (ollama)
    with patch.dict(os.environ, {}, clear=True):
        # We assume if no env vars, it defaults to ollama
        with patch("beeai_framework.backend.chat.ChatModel.from_name") as mock_from_name:
            get_llm()
            # Expect call with ollama:llama3.1 (default)
            mock_from_name.assert_called_with("ollama:llama3.1")


def test_get_llm_watsonx():
    with patch.dict(os.environ, {"LLM_PROVIDER": "watsonx", "LLM_MODEL": "granite"}, clear=True):
        with patch("beeai_framework.backend.chat.ChatModel.from_name") as mock_from_name:
            get_llm()
            mock_from_name.assert_called_with("watsonx:granite")


def test_get_llm_openai():
    with patch.dict(os.environ, {"LLM_PROVIDER": "openai", "LLM_MODEL": "gpt-4"}, clear=True):
        with patch("beeai_framework.backend.chat.ChatModel.from_name") as mock_from_name:
            get_llm()
            mock_from_name.assert_called_with("openai:gpt-4")


def test_get_llm_invalid_provider():
    from app.core.llm import LLMError

    with patch.dict(os.environ, {"LLM_PROVIDER": "unknown"}, clear=True):
        with pytest.raises(LLMError) as exc:
            get_llm()
        assert "Failed to initialize LLM" in str(exc.value)


def test_get_llm_provider_case_insensitive():
    with patch.dict(os.environ, {"LLM_PROVIDER": "OLLAMA"}, clear=True):
        with patch("beeai_framework.backend.chat.ChatModel.from_name") as mock_from_name:
            get_llm()
            mock_from_name.assert_called_with("ollama:llama3.1")
