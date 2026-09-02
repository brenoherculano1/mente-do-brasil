"""Queries for the explicitly allowlisted public disclosure views."""

from __future__ import annotations

import base64
import json
from typing import Any

from api.db import Database

OPEN_DATA_RELEASE = "MDB_OPEN_DATA_2024_1"
ANALYTICAL_RELEASE = "MDB_ANALYTICAL_2024_2"
API_VERSION = "MDB_PUBLIC_API_V1"


def envelope(data: Any, **metadata: Any) -> dict[str, Any]:
    return {
        "meta": {
            "api_version": API_VERSION,
            "open_data_release": OPEN_DATA_RELEASE,
            "analytical_release": ANALYTICAL_RELEASE,
            **metadata,
        },
        "data": data,
    }


def encode_cursor(offset: int) -> str:
    payload = json.dumps({"offset": offset}, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(payload).decode().rstrip("=")


def decode_cursor(cursor: str | None) -> int:
    if cursor is None:
        return 0
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        value = json.loads(base64.urlsafe_b64decode(padded))
        offset = value["offset"]
        if type(offset) is not int or offset < 0:
            raise ValueError
        return offset
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid pagination cursor.") from exc


def page(db: Database, sql: str, params: tuple, limit: int, offset: int) -> dict[str, Any]:
    rows = db.rows(f"{sql} LIMIT %s OFFSET %s", (*params, limit + 1, offset))
    has_more = len(rows) > limit
    data = rows[:limit]
    return envelope(
        data,
        pagination={
            "limit": limit,
            "count": len(data),
            "next_cursor": encode_cursor(offset + limit) if has_more else None,
        },
    )
