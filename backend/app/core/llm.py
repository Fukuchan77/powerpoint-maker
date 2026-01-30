import os

from beeai_framework.backend.chat import ChatModel


def get_llm() -> ChatModel:
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    model_name = os.getenv("LLM_MODEL", "llama3.1")

    if provider == "ollama":
        # Assumes Ollama is running locally on default port if not specified
        return ChatModel.from_name(f"ollama:{model_name}")
    elif provider == "watsonx":
        return ChatModel.from_name(f"watsonx:{model_name}")
    elif provider == "openai":
        return ChatModel.from_name(f"openai:{model_name}")
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")
