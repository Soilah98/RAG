
import logging
import time

from functools import lru_cache
from openai import OpenAI
from . import config


logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    """Retourne un client OpenAI réutilisable."""
    return OpenAI()


def embed(texts: list[str]) -> list[list[float]]:
    """
    Génère un embedding par texte en un seul appel API.
    """

    start = time.perf_counter()

    try:
        response = get_client().embeddings.create(
            model=config.EMBEDDING_MODEL,
            input=texts,
        )

        duration_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "embedding_completed",
            extra={
                "event": "embedding_completed",
                "duration_ms": round(duration_ms, 2),
                "texts_count": len(texts),
                "tokens_used": response.usage.total_tokens,
            },
        )

        return [item.embedding for item in response.data]

    except Exception:
        logger.exception(
            "embedding_failed",
            extra={"event": "embedding_failed"},
        )
        raise


def chat(messages: list[dict], max_tokens: int = 200) -> str:
    """
    Génère une réponse avec le modèle LLM.
    """

    start = time.perf_counter()

    try:
        response = get_client().chat.completions.create(
            model=config.LLM_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0,
        )

        duration_ms = (time.perf_counter() - start) * 1000

        usage = response.usage

        prompt_tokens = usage.prompt_tokens if usage else None
        completion_tokens = usage.completion_tokens if usage else None
        total_tokens = usage.total_tokens if usage else None

        answer = response.choices[0].message.content or ""

        logger.info(
            "llm_api_call_completed",
            extra={
                "event": "llm_api_call_completed",
                "duration_ms": round(duration_ms, 2),
                "model": config.LLM_MODEL,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "answer_length": len(answer),
            },
        )

        return answer

    except Exception:
        logger.exception(
            "llm_api_call_failed",
            extra={"event": "llm_api_call_failed"},
        )
        raise
