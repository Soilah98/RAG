import os
import uuid

import httpx
import streamlit as st

# ============================================================
# CONFIGURATION
# ============================================================

API_URL = os.getenv("API_URL", "http://localhost:8001")
API_KEY = os.getenv("API_KEY", "")                    # si l'API exige X-API-Key
SHOW_SCORES = os.getenv("SHOW_SCORES", "1") == "1"    # "0" pour masquer les scores aux clients

MAX_HISTORY = 10            # doit rester <= 2 * MAX_TURNS de l'API, sinon elle répond 422
MAX_QUESTION_CHARS = 1000   # limite de l'API
DEFAULT_TITLE = "Conversation vide"

st.set_page_config(
    page_title="Le Belvédère | Assistant",
    page_icon="🏨",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

/* Global */
.stApp {
    background-color: #FAF9F6;
    color: #302A24;
}

.block-container {
    max-width: 900px;
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Hide Streamlit branding */
#MainMenu, footer {
    visibility: hidden;
}

/* Main header */
.hotel-brand {
    text-align: center;
    padding: 20px 0 35px 0;
}

.hotel-brand .eyebrow {
    color: #947958;
    font-size: 11px;
    letter-spacing: 4px;
    font-weight: 600;
    margin-bottom: 12px;
}

.hotel-brand h1 {
    color: #302A24;
    font-family: Georgia, serif;
    font-size: 38px;
    font-weight: 500;
    margin-bottom: 10px;
}

.hotel-brand p {
    color: #82796F;
    font-size: 15px;
}

/* Welcome section */
.welcome-card {
    background: #F1EADF;
    border: 1px solid #E8DFD1;
    border-radius: 18px;
    padding: 28px;
    margin: 20px 0;
}

.welcome-card h2 {
    font-family: Georgia, serif;
    color: #302A24;
    font-size: 25px;
    font-weight: 500;
}

.welcome-card p {
    color: #74695C;
    font-size: 14px;
    line-height: 1.7;
}

/* Suggestions */
div.stButton > button {
    border: 1px solid #E6DED2;
    background: #FFFFFF;
    color: #514536;
    border-radius: 12px;
    min-height: 55px;
    transition: all 0.2s ease;
}

div.stButton > button:hover {
    border-color: #947958;
    background: #F4EFE7;
    color: #302A24;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    border-radius: 16px;
    padding: 14px;
    border: 1px solid #ECE7DF;
    background: #FFFFFF;
}

/* Chat input */
[data-testid="stChatInput"] {
    border: 1px solid #DCD3C7;
    border-radius: 15px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #F1EADF;
    border-right: 1px solid #E5DCCE;
}

.sidebar-brand {
    font-family: Georgia, serif;
    font-size: 22px;
    color: #302A24;
    margin-bottom: 4px;
}

.sidebar-subtitle {
    color: #897B69;
    font-size: 11px;
    letter-spacing: 2px;
}

/* Small text */
.muted-text {
    color: #8A8177;
    font-size: 12px;
}

hr {
    border-color: #E7DFD4;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================

def create_conversation():
    return {
        "id": str(uuid.uuid4()),
        "title": DEFAULT_TITLE,
        "messages": [],
    }


if "conversations" not in st.session_state:
    first_conversation = create_conversation()
    st.session_state.conversations = [first_conversation]
    st.session_state.active_conversation = first_conversation["id"]

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

if "last_error" not in st.session_state:
    st.session_state.last_error = None      # {"question": ..., "message": ...}


def get_active_conversation():
    for conversation in st.session_state.conversations:
        if conversation["id"] == st.session_state.active_conversation:
            return conversation

    conversation = create_conversation()
    st.session_state.conversations.append(conversation)
    st.session_state.active_conversation = conversation["id"]
    return conversation


# ============================================================
# API
# ============================================================

def error_message(exc):
    """Message affichable au client : jamais le détail technique."""
    if isinstance(exc, httpx.TimeoutException):
        return "La recherche prend trop de temps. Veuillez réessayer."

    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        if status == 422:
            return (
                "Votre message est invalide ou trop long "
                f"(maximum {MAX_QUESTION_CHARS} caractères)."
            )
        if status == 401:
            return "Accès refusé par le serveur : clé d'API manquante ou invalide."
        if status == 503:
            return (
                "L'assistant n'est pas encore prêt "
                "(documentation en cours d'indexation). Réessayez dans un instant."
            )
        if status in (502, 504):
            return (
                "Le service de réponse est momentanément indisponible. "
                "Réessayez dans un instant."
            )
        return "Une erreur est survenue lors du traitement de votre demande."

    if isinstance(exc, (ValueError, KeyError)):      # réponse 200 mais illisible ou incomplète
        return "L'assistant a renvoyé une réponse inattendue. Veuillez réessayer."

    return (
        "Impossible de contacter l'assistant. "
        "Vérifiez que le serveur API est démarré."
    )


def ask_api(question, history):
    response = httpx.post(
        f"{API_URL}/chat",
        json={"question": question, "history": history},
        headers={"X-API-Key": API_KEY} if API_KEY else None,
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data["answer"], data.get("sources", [])


def render_sources(sources):
    if not sources:
        return

    with st.expander(f"📚 Documents consultés ({len(sources)})"):
        for source in sources:
            st.markdown(f"**{source['title']}**")
            st.caption(f"Document : {source['source']}")

            if SHOW_SCORES and source.get("similarity") is not None:
                st.caption(f"Score de similarité : {source['similarity']:.3f}")


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("""
        <div class="sidebar-brand">LE BELVÉDÈRE</div>
        <div class="sidebar-subtitle">HOTEL & SPA</div>
    """, unsafe_allow_html=True)

    st.divider()

    if st.button(
        "＋ Nouvelle conversation",
        use_container_width=True,
        type="primary",
    ):
        # Inutile d'empiler des conversations vides
        if get_active_conversation()["messages"]:
            conversation = create_conversation()
            st.session_state.conversations.insert(0, conversation)
            st.session_state.active_conversation = conversation["id"]
        st.session_state.last_error = None
        st.rerun()

    st.markdown("##### Vos conversations")

    for conversation in st.session_state.conversations:

        label = conversation["title"]

        if conversation["id"] == st.session_state.active_conversation:
            label = "● " + label

        if st.button(
            label,
            key=f"conversation_{conversation['id']}",
            use_container_width=True,
        ):
            st.session_state.active_conversation = conversation["id"]
            st.session_state.last_error = None
            st.rerun()

    st.divider()

    st.markdown(
        '<p class="muted-text">Assistant hôtelier intelligent'
        '<br>Propulsé par RAG & IA</p>',
        unsafe_allow_html=True,
    )


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown("""
<div class="hotel-brand">
    <div class="eyebrow">HOTEL & SPA</div>
    <h1>Le Belvédère</h1>
    <p>Votre concierge personnel, disponible à tout moment.</p>
</div>
""", unsafe_allow_html=True)


conversation = get_active_conversation()
messages = conversation["messages"]


# ============================================================
# DISPLAY CONVERSATION HISTORY
# ============================================================

for message in messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        render_sources(message.get("sources", []))


# ============================================================
# QUESTION : suggestion cliquée, relance après erreur, ou saisie
# (lue AVANT l'écran d'accueil, pour pouvoir le masquer pendant la requête)
# ============================================================

question = st.session_state.pending_question

if question:
    st.session_state.pending_question = None
else:
    question = st.chat_input(
        "Posez votre question sur l'hôtel...",
        max_chars=MAX_QUESTION_CHARS,
    )


# ============================================================
# WELCOME SCREEN & SUGGESTED QUESTIONS
# ============================================================

if not messages and not question:

    st.markdown("""
    <div class="welcome-card">
        <h2>Bienvenue au Belvédère</h2>
        <p>
            Nous sommes ravis de vous accueillir.
            Comment pouvons-nous rendre votre séjour
            encore plus agréable ?
            Posez-moi vos questions sur nos chambres,
            notre restaurant, notre spa et nos services.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("##### Que souhaitez-vous savoir ?")

    suggestions = [
        ("🕒  Horaires", "Quels sont les horaires des services de l'hôtel ?"),
        ("♨️  Spa & bien-être", "Quels sont les tarifs et horaires du spa ?"),
        ("🍽️  Restaurant", "Quels sont les horaires et les menus du restaurant ?"),
        ("🛏️  Chambres", "Quels types de chambres proposez-vous et à quels tarifs ?"),
    ]

    col1, col2 = st.columns(2)

    for index, (label, suggestion) in enumerate(suggestions):

        target_col = col1 if index % 2 == 0 else col2

        with target_col:
            if st.button(
                label,
                key=f"suggestion_{index}",
                use_container_width=True,
            ):
                st.session_state.pending_question = suggestion
                st.rerun()


# ============================================================
#  on garde la question et on propose de la relancer
# ============================================================

if st.session_state.last_error and not question:

    error = st.session_state.last_error

    st.error(error["message"])
    st.caption(f"Votre question : {error['question'][:120]}")

    if st.button("↻ Réessayer", key="retry"):
        st.session_state.pending_question = error["question"]
        st.session_state.last_error = None
        st.rerun()


# ============================================================
# RAG REQUEST
# ============================================================

if question:

    st.session_state.last_error = None

    with st.chat_message("user"):
        st.markdown(question)

    history = [
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in messages
    ][-MAX_HISTORY:]

    with st.chat_message("assistant"):

        with st.spinner("Recherche dans la documentation de l'hôtel..."):

            try:
                answer, sources = ask_api(question, history)

            except (httpx.HTTPError, ValueError, KeyError) as exc:
                st.session_state.last_error = {
                    "question": question,
                    "message": error_message(exc),
                }
                st.rerun()

    # Échange réussi : on l'enregistre, puis on relance pour l'afficher via l'historique
    messages.extend([
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer, "sources": sources},
    ])

    # Titre de la conversation = début de la première question
    if conversation["title"] == DEFAULT_TITLE:
        conversation["title"] = question[:35]
        if len(question) > 35:
            conversation["title"] += "..."

    st.rerun()