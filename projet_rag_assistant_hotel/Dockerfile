FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# 1. Dépendances : couche mise en cache tant que pyproject.toml et uv.lock ne changent pas
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --extra ui --no-install-project

# 2. Code
COPY README.md ./
COPY src ./src
COPY scripts ./scripts
COPY streamlit_app.py ./
RUN uv sync --locked --no-dev --extra ui

# Utilisateur non-root ; .chroma/ lui appartient (le volume nommé hérite de ces droits)
RUN useradd --create-home app && mkdir -p /app/.chroma && chown app /app/.chroma
USER app

EXPOSE 8000 8501
CMD ["uvicorn", "hotel_rag.api:app", "--host", "0.0.0.0", "--port", "8000"]