"""Vendor-neutral operational logging and request correlation."""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any

SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._:-]{8,80}$")
RAW_IP_VALUE = re.compile(
    r"^(?:(?:\d{1,3}\.){3}\d{1,3}|(?:[a-f0-9]{1,4}:){2,}[a-f0-9]{1,4})$",
    re.I,
)
SENSITIVE_KEY = re.compile(
    "authorization|cookie|password|token|secret|database_url|dsn|ip|"
    "x-forwarded-for|x-real-ip",
    re.I,
)

logger = logging.getLogger("mente_do_brasil")


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def request_id_from_value(value: str | None) -> str:
    if value and SAFE_REQUEST_ID.fullmatch(value.strip()) and not RAW_IP_VALUE.search(value):
        return value.strip()
    return str(uuid.uuid4())


def sanitize_log_fields(fields: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in fields.items():
        if SENSITIVE_KEY.search(key):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, str) and RAW_IP_VALUE.search(value):
            sanitized[key] = "[REDACTED]"
        else:
            sanitized[key] = value
    return sanitized


def operational_log(event: str, **fields: Any) -> None:
    payload = sanitize_log_fields(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": fields.pop("level", "info"),
            "service": "mente-do-brasil-api",
            "event": event,
            **fields,
        }
    )
    logger.info(json.dumps(payload, ensure_ascii=False, sort_keys=True))
