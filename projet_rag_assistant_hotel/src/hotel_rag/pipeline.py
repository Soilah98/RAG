
import logging
import time

from dataclasses import dataclass

from . import config
from .generation import (
    FALLBACK,
    build_system_prompt,
    condense_question,
)
from .llm import chat
from .store import Hit, search
from .observability import langfuse


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Answer:
    text: str
    standalone_question: str
    hits: list[Hit]
    refused: bool = False

    @property
    def declined(self) -> bool:
        return self.refused or self.text.strip() == FALLBACK


def chat_turn(
    question: str,
    history: list[dict],
    top_k: int = config.TOP_K,
    threshold: float | None = None,
) -> Answer:

    pipeline_start = time.perf_counter()

    threshold = (
        config.SIMILARITY_THRESHOLD
        if threshold is None
        else threshold
    )

    logger.info(
        "pipeline_started",
        extra={"event": "pipeline_started"},
    )

    # 1. Condensation de la question
    condensation_start = time.perf_counter()

    try:
        standalone = condense_question(question, history)

    except Exception:
        logger.exception(
            "question_condensation_failed",
            extra={"event": "question_condensation_failed"},
        )
        raise

    condensation_duration = (
        time.perf_counter() - condensation_start
    ) * 1000

    logger.info(
        "question_condensation_completed",
        extra={
            "event": "question_condensation_completed",
            "duration_ms": round(condensation_duration, 2),
        },
    )

    # 2. Recherche documentaire (Retrieval)
    retrieval_start = time.perf_counter()

    try:
        hits = search(standalone, top_k=top_k)

    except Exception:
        logger.exception(
            "retrieval_failed",
            extra={"event": "retrieval_failed"},
        )
        raise

    retrieval_duration = (
        time.perf_counter() - retrieval_start
    ) * 1000

    best_similarity = (
        round(hits[0].similarity, 3)
        if hits
        else None
    )

    logger.info(
        "rag_retrieval_completed",
        extra={
            "event": "rag_retrieval_completed",
            "hits_count": len(hits),
            "best_similarity": best_similarity,
            "threshold": threshold,
            "top_k": top_k,
            "duration_ms": round(retrieval_duration, 2),
        },
    )

    # 3. Vérification du seuil de similarité
    if not hits or hits[0].similarity < threshold:

        logger.warning(
            "retrieval_threshold_not_reached",
            extra={
                "event": "retrieval_threshold_not_reached",
                "refused": True,
                "best_similarity": best_similarity,
                "threshold": threshold,
            },
        )

        total_duration = (
            time.perf_counter() - pipeline_start
        ) * 1000

        logger.info(
            "pipeline_completed",
            extra={
                "event": "pipeline_completed",
                "duration_ms": round(total_duration, 2),
                "refused": True,
            },
        )

        return Answer(
            FALLBACK,
            standalone,
            hits,
            refused=True,
        )

    # 4. Construction du contexte RAG
    context = "\n\n".join(hit.text for hit in hits)

    messages = [
        {
            "role": "system",
            "content": build_system_prompt(context),
        }
    ]

    messages += history[-2 * config.MAX_TURNS:]

    messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    # 5. Génération de la réponse par le LLM
    llm_start = time.perf_counter()

    logger.info(
        "llm_generation_started",
        extra={"event": "llm_generation_started"},
    )

    try:
        answer = chat(messages)

    except Exception:
        logger.exception(
            "llm_generation_failed",
            extra={"event": "llm_generation_failed"},
        )
        raise

    llm_duration = (
        time.perf_counter() - llm_start
    ) * 1000

    logger.info(
        "llm_generation_completed",
        extra={
            "event": "llm_generation_completed",
            "duration_ms": round(llm_duration, 2),
            "answer_length": len(answer),
        },
    )

    # 6. Fin du pipeline
    total_duration = (
        time.perf_counter() - pipeline_start
    ) * 1000

    logger.info(
        "pipeline_completed",
        extra={
            "event": "pipeline_completed",
            "duration_ms": round(total_duration, 2),
            "refused": False,
        },
    )

    return Answer(
        answer,
        standalone,
        hits,
        refused=False,
    )
