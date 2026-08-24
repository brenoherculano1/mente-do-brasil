"""API error contract."""

from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def error_payload(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def api_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail=error_payload(code, message))


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload("INTERNAL_ERROR", "Request failed."),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    for error in exc.errors():
        if "metric" in error.get("loc", ()):
            return JSONResponse(
                status_code=422,
                content=error_payload("INVALID_METRIC", "Invalid map metric."),
            )
    return JSONResponse(
        status_code=422,
        content=error_payload("VALIDATION_ERROR", "Invalid request parameters."),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=error_payload("INTERNAL_ERROR", "Internal server error."),
    )
