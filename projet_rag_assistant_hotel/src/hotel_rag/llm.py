from functools import lru_cache

from openai import OpenAI

from . import config


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    return OpenAI()  # lit OPENAI_API_KEY dans l'environnement (.env chargé par config)


def embed(texts: list[str]) -> list[list[float]]:
    """Un vecteur (normalisé, norme 1) par texte, en un seul appel API."""
    response = get_client().embeddings.create(model=config.EMBEDDING_MODEL, input=texts)
    return [d.embedding for d in response.data]


def chat(messages: list[dict], max_tokens: int = 200) -> str:
    response = get_client().chat.completions.create(
        model=config.LLM_MODEL,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0,
    )
    return response.choices[0].message.content