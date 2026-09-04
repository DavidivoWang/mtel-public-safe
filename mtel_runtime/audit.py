from __future__ import annotations

import json
import logging
from typing import Any

LOGGER = logging.getLogger("mtel_runtime")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "event": getattr(record, "mtel_event", record.getMessage()),
        }
        payload.update(getattr(record, "mtel_fields", {}))
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def configure_logging(level: str = "WARNING") -> None:
    LOGGER.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    LOGGER.addHandler(handler)
    LOGGER.setLevel(getattr(logging, level.upper(), logging.WARNING))
    LOGGER.propagate = False


def emit(event: str, **fields: Any) -> None:
    if LOGGER.isEnabledFor(logging.INFO):
        LOGGER.info(event, extra={"mtel_event": event, "mtel_fields": fields})
