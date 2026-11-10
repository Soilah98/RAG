from dataclasses import dataclass
from functools import lru_cache

import chromadb

from . import config
from .ingestion import Section
from .llm import embed


@dataclass(frozen=True)
class Hit:
    title: str
    source: str
    text: str
    distance: float

    @property
    def similarity(self) -> float:
        return 1 - self.distance      # distance cosinus -> similarité


@lru_cache(maxsize=1)
def _client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(path=str(config.CHROMA_DIR))


def build_index(sections: list[Section]) -> int:
    """(Re)construit l'index depuis zéro."""
    client = _client()
    try:
        client.delete_collection(config.COLLECTION)
    except Exception:
        pass  # la collection n'existait pas encore
    collection = client.create_collection(config.COLLECTION, metadata={"hnsw:space": "cosine"})
    documents = [s.markdown for s in sections]
    collection.add(
        ids=[str(i) for i in range(len(sections))],
        embeddings=embed(documents),
        documents=documents,
        metadatas=[{"title": s.title, "source": s.source} for s in sections],
    )
    return len(sections)


def search(question: str, top_k: int = config.TOP_K) -> list[Hit]:
    try:
        collection = _client().get_collection(config.COLLECTION)
    except Exception as exc:
        raise RuntimeError("Index introuvable : lance d'abord `python scripts/ingest.py`") from exc

    res = collection.query(query_embeddings=embed([question]), n_results=min(top_k, collection.count()))
    return [
        Hit(title=m["title"], source=m["source"], text=doc, distance=dist)
        for m, doc, dist in zip(res["metadatas"][0], res["documents"][0], res["distances"][0])
    ]