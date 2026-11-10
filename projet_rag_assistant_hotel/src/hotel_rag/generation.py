from .llm import chat

ROLE = (
    "Tu es l'assistant virtuel de l'Hôtel Le Belvédère, au bord du lac d'Annecy.\n"
    "Voici la documentation officielle de l'hôtel :"
)

FALLBACK = "Je ne sais pas, je vous invite à contacter la réception."

CONSIGNE = (
    "Réponds en une ou deux phrases, uniquement à partir des informations "
    "de la documentation ci-dessus. Si l'information ne s'y trouve pas, réponds exactement : "
    f'"{FALLBACK}"'
)


def build_system_prompt(context: str) -> str:
    return f"{ROLE}\n\n{context}\n\n{CONSIGNE}"


def condense_question(question: str, history: list[dict], max_turns: int = 3) -> str:
    """Réécrit une question de suivi en question autonome (pour la recherche uniquement)."""
    if not history:
        return question
    recent = history[-2 * max_turns:]
    transcript = "\n".join(
        f"{'Client' if m['role'] == 'user' else 'Assistant'} : {m['content']}" for m in recent
    )
    prompt = (
        "Voici une conversation entre un client et l'assistant d'un hôtel, puis une nouvelle question du client.\n"
        "Réécris la nouvelle question pour qu'elle soit compréhensible seule, sans la conversation, "
        "en une phrase et dans la même langue. Si elle l'est déjà, recopie-la telle quelle. "
        "Réponds uniquement par la question.\n\n"
        f"Conversation :\n{transcript}\n\nNouvelle question : {question}"
    )
    return chat([{"role": "user", "content": prompt}], max_tokens=80).strip()