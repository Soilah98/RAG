
import logging
import time

from dataclasses import dataclass
from functools import lru_cache

import chromadb

from . import config
from .ingestion import Section
from .llm import embed


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Hit:
    title: str
    source: str
    text: str
    distance: float

    @property
    def similarity(self) -> float:
        return 1 - self.distance


@lru_cache(maxsize=1)
def _client() -> chromadb.ClientAPI:
    """Retourne le client ChromaDB persistant."""
    return chromadb.PersistentClient(
        path=str(config.CHROMA_DIR)
    )


def build_index(sections: list[Section]) -> int:
    """Reconstruit l'index ChromaDB depuis zéro."""

    start = time.perf_counter()

    logger.info(
        "index_build_started",
        extra={
            "event": "index_build_started",
            "documents_count": len(sections),
        },
    )

    try:
        client = _client()

        # Suppression de l'ancienne collection
        try:
            client.delete_collection(config.COLLECTION)
        except Exception:
            pass  # Collection inexistante ou non disponible

        # Création de la nouvelle collection
        collection = client.create_collection(
            config.COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )

        # Préparation des documents
        documents = [section.markdown for section in sections]

        # Génération des embeddings et indexation
        embeddings = embed(documents)

        collection.add(
            ids=[str(i) for i in range(len(sections))],
            embeddings=embeddings,
            documents=documents,
            metadatas=[
                {
                    "title": section.title,
                    "source": section.source,
                }
                for section in sections
            ],
        )

        duration_ms = (
            time.perf_counter() - start
        ) * 1000

        logger.info(
            "index_build_completed",
            extra={
                "event": "index_build_completed",
                "documents_count": len(sections),
                "duration_ms": round(duration_ms, 2),
            },
        )

        return len(sections)

    except Exception:
        logger.exception(
            "index_build_failed",
            extra={"event": "index_build_failed"},
        )
        raise


def search(
    question: str,
    top_k: int = config.TOP_K,
) -> list[Hit]:
    """Recherche les chunks les plus pertinents dans ChromaDB."""

    start = time.perf_counter()

    try:
        collection = _client().get_collection(
            config.COLLECTION
        )

    except Exception as exc:
        logger.exception(
            "index_retrieval_failed",
            extra={"event": "index_retrieval_failed"},
        )

        raise RuntimeError(
            "Index introuvable : lance d'abord `python scripts/ingest.py`"
        ) from exc

    try:
        documents_count = collection.count()

        # Aucun document dans la collection
        if documents_count == 0:
            duration_ms = (
                time.perf_counter() - start
            ) * 1000

            logger.warning(
                "retrieval_empty_index",
                extra={
                    "event": "retrieval_empty_index",
                    "documents_count": 0,
                    "hits_count": 0,
                    "duration_ms": round(duration_ms, 2),
                },
            )

            return []

        # Nombre de résultats à récupérer
        results_count = min(top_k, documents_count)

        # Vectorisation de la question
        query_embedding = embed([question])

        # Recherche vectorielle
        res = collection.query(
            query_embeddings=query_embedding,
            n_results=results_count,
        )

        # Transformation des résultats en objets Hit
        hits = [
            Hit(
                title=metadata["title"],
                source=metadata["source"],
                text=document,
                distance=distance,
            )
            for metadata, document, distance in zip(
                res["metadatas"][0],
                res["documents"][0],
                res["distances"][0],
            )
        ]

        best_similarity = (
            round(hits[0].similarity, 3)
            if hits
            else None
        )

        best_distance = (
            round(hits[0].distance, 3)
            if hits
            else None
        )

        duration_ms = (
            time.perf_counter() - start
        ) * 1000

        logger.info(
            "vector_search_completed",
            extra={
                "event": "vector_search_completed",
                "documents_count": documents_count,
                "hits_count": len(hits),
                "top_k": results_count,
                "best_similarity": best_similarity,
                "best_distance": best_distance,
                "duration_ms": round(duration_ms, 2),
            },
        )

        return hits

    except Exception:
        logger.exception(
            "retrieval_failed",
            extra={"event": "retrieval_failed"},
        )
        raise


def count() -> int:
    """Retourne le nombre de documents indexés."""

    try:
        collection = _client().get_collection(
            config.COLLECTION
        )

        documents_count = collection.count()

        logger.info(
            "index_health_checked",
            extra={
                "event": "index_health_checked",
                "documents_count": documents_count,
            },
        )

        return documents_count

    except Exception:
        logger.warning(
            "index_health_unavailable",
            extra={"event": "index_health_unavailable"},
        )
        return 0
