from hotel_rag.generation import build_system_prompt, condense_question
from hotel_rag.ingestion import Section


def test_section_markdown():
    assert Section("a.pdf", "Piscine", "Ouverte de 8h à 20h.").markdown == "## Piscine\n\nOuverte de 8h à 20h."


def test_condense_without_history_returns_question():
    assert condense_question("Y a-t-il un spa ?", []) == "Y a-t-il un spa ?"


def test_system_prompt_contains_context():
    assert "## Piscine" in build_system_prompt("## Piscine\n\nOuverte.")