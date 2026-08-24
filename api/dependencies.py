"""FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from .config import Settings
from .db import Database


def settings_dependency(request: Request) -> Settings:
    return request.app.state.settings


def database_dependency(request: Request) -> Database:
    return Database(request.app.state.pool)


SettingsDep = Annotated[Settings, Depends(settings_dependency)]
DatabaseDep = Annotated[Database, Depends(database_dependency)]
