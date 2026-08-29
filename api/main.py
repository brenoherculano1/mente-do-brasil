from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from api.config import get_settings
from api.db import Database, create_pool
from api.errors import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from api.observability import configure_logging, operational_log, request_id_from_value
from api.routers.health import router as health_router
from api.routers.health_regions import router as health_regions_router
from api.routers.indicators import router as indicators_router
from api.routers.intelligence import router as intelligence_router
from api.routers.manager import router as manager_router
from api.routers.releases import router as releases_router
from api.services.health_regions import ready_check


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    operational_log("startup", status="starting", release_id=settings.default_release_id)
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
    operational_log("startup", status="ready", release_id=settings.default_release_id)
    try:
        yield
    finally:
        pool.close()
        operational_log("shutdown", status="complete", release_id=settings.default_release_id)


settings = get_settings()
configure_logging()
app = FastAPI(
    title="Mente do Brasil API",
    version="0.1.0",
    description=(
        "Internal read-only API for the Mente do Brasil territorial mental-health data platform."
    ),
    lifespan=lifespan,
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_docs else None,
    openapi_url="/openapi.json" if settings.enable_docs else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1024)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(health_router)
app.include_router(releases_router)
app.include_router(indicators_router)
app.include_router(health_regions_router)
app.include_router(intelligence_router)
app.include_router(manager_router)


@app.middleware("http")
async def request_id_middleware(request, call_next):
    request_id = request_id_from_value(request.headers.get("x-request-id"))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
