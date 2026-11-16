from typing import Literal

from fastapi import FastAPI, HTTPException
from openai import OpenAIError
from pydantic import BaseModel, Field

from .pipeline import chat_turn
from .store import count

app = FastAPI(title="Hotel RAG API", version="0.1.0")


class Message(BaseModel):
    role: Literal["user", "assistant"]      # pas de "system" : un client ne peut pas injecter de consigne
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    history: list[Message] = Field(default_factory=list, max_length=20)


class Source(BaseModel):
    title: str
    source: str
    similarity: float


class ChatResponse(BaseModel):
    answer: str
    standalone_question: str
    refused: bool
    sources: list[Source]


@app.get("/health")
def health():
    return {"status": "ok", "index_size": count()}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):      # `def` et non `async def` : le pipeline est bloquant (appels OpenAI)
    history = [m.model_dump() for m in req.history]
    try:
        answer = chat_turn(req.question, history)
    except RuntimeError as exc:                   # levée par store.search : index introuvable
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except OpenAIError as exc:
        raise HTTPException(status_code=502, detail="Erreur du fournisseur LLM") from exc

    sources = [] if answer.declined else [
        Source(title=h.title, source=h.source, similarity=round(h.similarity, 3))
        for h in answer.hits
    ]
    return ChatResponse(
        answer=answer.text,
        standalone_question=answer.standalone_question,
        refused=answer.declined,
        sources=sources,
    )