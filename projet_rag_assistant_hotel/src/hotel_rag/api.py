
from typing import Literal
import logging
import time
import uuid

from fastapi import FastAPI, HTTPException
from openai import OpenAIError
from pydantic import BaseModel, Field

from .pipeline import chat_turn
from .store import count
from .logging_config import setup_logging, request_id_var


# ============================================================
# LOGGING
# ============================================================

setup_logging()

logger = logging.getLogger(__name__)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(title="Hotel RAG API", version="0.1.0")


# ============================================================
# MIDDLEWARE : TRAÇABILITÉ HTTP
# ============================================================

@app.middleware("http")
async def log_requests(request, call_next):

    request_id = str(uuid.uuid4())
    token = request_id_var.set(request_id)

    start = time.perf_counter()

    logger.info(
        "request_received",
        extra={"event": "request_received"}
    )

    try:
        response = await call_next(request)

        duration = (time.perf_counter() - start) * 1000

        logger.info(
            "request_completed",
            extra={
                "event": "request_completed",
                "duration_ms": round(duration, 2),
                "status_code": response.status_code,
            }
        )

        response.headers["X-Request-ID"] = request_id

        return response

    except Exception:
        logger.exception(
            "request_failed",
            extra={"event": "request_failed"}
        )
        raise

    finally:
        request_id_var.reset(token)


# ============================================================
# MODELS PYDANTIC
# ============================================================

class Message(BaseModel):
    role: Literal["user", "assistant"]
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


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {"status": "ok", "index_size": count()}


# ============================================================
# CHAT ENDPOINT
# ============================================================

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):

    history = [m.model_dump() for m in req.history]

    logger.info(
        "chat_started",
        extra={
            "event": "chat_started",
            "question_length": len(req.question),
        }
    )

    try:
        answer = chat_turn(req.question, history)

    except RuntimeError as exc:
        logger.exception(
            "rag_index_error",
            extra={"event": "rag_index_error"}
        )
        raise HTTPException(
            status_code=503,
            detail=str(exc)
        ) from exc

    except OpenAIError as exc:
        logger.exception(
            "llm_provider_error",
            extra={"event": "llm_provider_error"}
        )
        raise HTTPException(
            status_code=502,
            detail="Erreur du fournisseur LLM"
        ) from exc

    sources = [] if answer.declined else [
        Source(
            title=h.title,
            source=h.source,
            similarity=round(h.similarity, 3)
        )
        for h in answer.hits
    ]

    return ChatResponse(
        answer=answer.text,
        standalone_question=answer.standalone_question,
        refused=answer.declined,
        sources=sources,
    )
