from hotel_rag import pipeline
from hotel_rag.generation import FALLBACK
from hotel_rag.store import Hit


def _hit(similarity: float) -> Hit:
    return Hit("Piscine", "a.pdf", "## Piscine\n\nOuverte.", 1 - similarity)


def _patch(monkeypatch, similarity, chat_fn):
    monkeypatch.setattr(pipeline, "condense_question", lambda q, h: q)
    monkeypatch.setattr(pipeline, "search", lambda q, top_k: [_hit(similarity)])
    monkeypatch.setattr(pipeline, "chat", chat_fn)


def test_below_threshold_skips_llm(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("le LLM ne doit pas être appelé")

    _patch(monkeypatch, 0.10, boom)
    answer = pipeline.chat_turn("Quel temps demain ?", [], threshold=0.30)
    assert answer.refused and answer.text == FALLBACK


def test_above_threshold_calls_llm(monkeypatch):
    _patch(monkeypatch, 0.50, lambda messages, **kw: "Ouverte de 8h à 20h.")
    answer = pipeline.chat_turn("La piscine ouvre quand ?", [], threshold=0.30)
    assert not answer.refused and answer.text == "Ouverte de 8h à 20h."


def test_threshold_zero_never_refuses(monkeypatch):
    _patch(monkeypatch, 0.01, lambda messages, **kw: "ok")
    assert not pipeline.chat_turn("?", [], threshold=0.0).refused