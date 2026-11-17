
import json
import logging
import sys
import contextvars

from datetime import datetime, timezone


# Identifiant unique associé à chaque requête HTTP
request_id_var = contextvars.ContextVar(
    "request_id",
    default=None
)


class RequestIdFilter(logging.Filter):
    """Ajoute le request_id à chaque événement de log."""

    def filter(self, record):
        record.request_id = request_id_var.get()
        return True


class JSONFormatter(logging.Formatter):
    """Transforme les logs Python en JSON."""

    def format(self, record):

        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": getattr(
                record,
                "event",
                record.getMessage()
            ),
        }

        fields = [
            "request_id",
            "duration_ms",
            "question_length",
            "hits_count",
            "best_similarity",
            "threshold",
            "top_k",
            "answer_length",
            "refused",
            "status_code",
            "model",
            "texts_count",
            "tokens_used",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "documents_count",
            "best_distance",
        ]

        for field in fields:
            value = getattr(record, field, None)

            if value is not None:
                log_data[field] = value

        if record.exc_info:
            log_data["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(
            log_data,
            ensure_ascii=False,
            default=str
        )


def setup_logging():
    """Configure le logging global de l'application."""

    handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(JSONFormatter())
    handler.addFilter(RequestIdFilter())

    root_logger = logging.getLogger()

    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
