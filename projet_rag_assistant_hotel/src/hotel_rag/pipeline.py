from dataclasses import dataclass

from . import config
from .generation import FALLBACK, build_system_prompt, condense_question
from .llm import chat
from .llm import chat
from .store import Hit, search


@dataclass(frozen=True)
class Answer:
    text: str
    standalone_question: str
    hits: list[Hit]
    refused: bool = False      # True : seuil non atteint, le LLM n'a pas été appelé


def chat_turn(
    question: str,
    history: list[dict],
    top_k: int = config.TOP_K,
    threshold: float | None = None,
) -> Answer:
    """history : liste de {"role": "user"|"assistant", "content": str}."""
    threshold = config.SIMILARITY_THRESHOLD if threshold is None else threshold

    standalone = condense_question(question, history)
    hits = search(standalone, top_k=top_k)

    if not hits or hits[0].similarity < threshold:     # hits[0] = meilleur résultat
        return Answer(FALLBACK, standalone, hits, refused=True)

    context = "\n\n".join(h.text for h in hits)
    messages = [{"role": "system", "content": build_system_prompt(context)}]
    messages += history[-2 * config.MAX_TURNS:]
    messages.append({"role": "user", "content": question})
    return Answer(chat(messages), standalone, hits)