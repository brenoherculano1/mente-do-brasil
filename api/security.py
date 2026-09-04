"""Server-to-server authentication helpers."""

from __future__ import annotations

import secrets


def has_valid_internal_token(supplied_token: str | None, configured_token: str | None) -> bool:
    if configured_token is None:
        return True
    return supplied_token is not None and secrets.compare_digest(supplied_token, configured_token)
