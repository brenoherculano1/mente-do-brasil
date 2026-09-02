"""API error contract."""

from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.observability import operational_log


def public_problem(request: Request, status: int, title: str, detail: str, code: str):
    return JSONResponse(
        status_code=status,
        media_type="application/problem+json",
        content={
            "type": f"https://mentedobrasil.com.br/problems/{code.lower()}",
            "title": title,
            "status": status,
            "detail": detail,
            "instance": request.url.path,
            "code": code,
        },
    )


def error_payload(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def api_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail=error_payload(code, message))


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if request.url.path.startswith("/api/public/v1/"):
        return public_problem(
            request,
            exc.status_code,
            "Request failed",
            "Public API request failed.",
            "REQUEST_FAILED",
        )
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload("INTERNAL_ERROR", "Request failed."),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    if request.url.path.startswith("/api/public/v1/"):
        return public_problem(
            request,
            422,
            "Invalid request",
            "One or more request parameters are invalid.",
            "VALIDATION_ERROR",
        )
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
    operational_log(
        "unexpected_exception",
        level="error",
        request_id=getattr(request.state, "request_id", None),
        error_code=type(exc).__name__,
    )
    if request.url.path.startswith("/api/public/v1/"):
        return public_problem(
            request,
            500,
            "Internal server error",
            "The request could not be completed.",
            "INTERNAL_ERROR",
        )
    return JSONResponse(
        status_code=500,
        content=error_payload("INTERNAL_ERROR", "Internal server error."),
    )
