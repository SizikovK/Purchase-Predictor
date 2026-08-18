from typing import Literal

from langchain_core.language_models.chat_models import BaseChatModel
import logging
from pydantic import SecretStr

logger = logging.getLogger(__name__)

def create_llm(
    provider: Literal["openai", "ollama"],
    api_key: SecretStr,
    base_url: str,
    model: str,
    temperature: float,
) -> BaseChatModel:
    logger.info("Загрузка модели: %s -- %s,", model, base_url)
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(api_key=api_key, base_url=base_url, model=model, temperature=temperature)
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(base_url=base_url, model=model, temperature=temperature)

    logger.error("Загрузка модели: Ошибка")
    raise ValueError(f"Unsupported LLM provider: {provider}")
