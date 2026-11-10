import gradio as gr

from hotel_rag.pipeline import chat_turn

SEP = "\n\n---\n*Sources : "


def to_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
    if isinstance(content, dict):
        return content.get("text", "")
    return str(content)


def respond(message, history):
    clean = [{"role": m["role"], "content": to_text(m["content"]).split(SEP)[0]} for m in history]
    answer = chat_turn(to_text(message), clean)
    sources = ", ".join(dict.fromkeys(h.title for h in answer.hits))
    return f"{answer.text}{SEP}{sources}*"


demo = gr.ChatInterface(
    fn=respond,
    title="Assistant de l'Hôtel Le Belvédère",
    description="Posez vos questions sur l'hôtel (horaires, spa, tarifs, restaurant...).",
    examples=["A quelle heure commence le check-in ?", "Y a-t-il un spa ?", "Le wifi est-il gratuit ?"],
)

if __name__ == "__main__":
    demo.launch()