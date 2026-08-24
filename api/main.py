from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings
from api.db import Database, create_pool
from api.errors import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from api.routers.health import router as health_router
from api.routers.health_regions import router as health_regions_router
from api.routers.indicators import router as indicators_router
from api.routers.releases import router as releases_router
from api.services.health_regions import ready_check


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    pool = create_pool(settings)
    pool.open(wait=True)
    with pool.connection() as connection:
        read_only = connection.execute("SHOW default_transaction_read_only").fetchone()[
            "default_transaction_read_only"
        ]
        if read_only != "on":
            raise RuntimeError("API database pool is not read-only.")
    ready_check(Database(pool), settings.default_release_id)
    app.state.settings = settings
    app.state.pool = pool
    try:
        yield
    finally:
        pool.close()


app = FastAPI(
    title="Mente do Brasil API",
    version="0.1.0",
    description=(
        "Internal read-only API for the Mente do Brasil territorial mental-health "
        "data platform."
    ),
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(health_router)
app.include_router(releases_router)
app.include_router(indicators_router)
app.include_router(health_regions_router)
