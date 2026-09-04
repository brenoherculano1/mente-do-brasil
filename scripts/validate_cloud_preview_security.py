#!/usr/bin/env python3
"""Low-volume external security and privacy checks for the protected cloud preview."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

from scripts.validate_open_data_release import validate as validate_open_data

WEB_PATHS = (
    "/",
    "/radar",
    "/gestor",
    "/mudancas",
    "/financiamento",
    "/fluxos",
    "/dados",
    "/dados-abertos",
    "/desenvolvedores",
    "/governanca",
    "/metodologia",
    "/sobre",
    "/estado/AC",
    "/regiao/12001",
)
API_PATHS = (
    "/api/public/v1/releases",
    "/api/public/v1/health-regions?limit=500",
    "/api/public/v1/health-regions/12001/timeline",
    "/api/public/v1/changes?from_year=2022&to_year=2024&uf=AC",
    "/api/public/v1/financing?year=2024&uf=AC",
    "/api/public/v1/health-regions/12001/flows",
    "/api/public/v1/health-regions/12001/peers",
    "/api/public/v1/municipalities/1200013/health-region",
    "/api/public/v1/metadata/indicators",
    "/api/public/v1/metadata/methodology",
    "/api/public/v1/openapi.json",
)
PII_FIELDS = {"cpf", "cns", "patient_name", "name_patient", "address", "email", "phone"}
RAW_FIELDS = {"suicide_deaths", "patient_id", "raw_source", "source_row"}
SECRET_PATTERNS = {
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_token": re.compile(rb"\b(?:ghp|gho|ghu|ghs|github_pat)_[A-Za-z0-9_]{20,}\b"),
    "supabase_secret": re.compile(rb"\bsb_secret_[A-Za-z0-9_-]{20,}\b"),
    "database_url": re.compile(rb"postgres(?:ql)?://[^\s\"']+", re.I),
    "internal_token": re.compile(rb"X-MDB-Internal-Token[^A-Za-z0-9]+[A-Za-z0-9_-]{24,}", re.I),
}
ASSET = re.compile(rb"(?:src|href)=[\"']([^\"']+\.(?:js|css)(?:\?[^\"']*)?)[\"']")


def fetch(url: str, headers: dict[str, str], method: str = "GET") -> tuple[int, dict, bytes]:
    request = urllib.request.Request(url, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            headers = {key.lower(): value for key, value in response.headers.items()}
            return response.status, headers, response.read()
    except urllib.error.HTTPError as error:
        headers = {key.lower(): value for key, value in error.headers.items()}
        return error.code, headers, error.read()


def field_names(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(field_names(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(field_names(item) for item in value), set())
    return set()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--web-url", required=True)
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    web, api = args.web_url.rstrip("/"), args.api_url.rstrip("/")
    web_bypass = os.environ["MDB_STAGING_BYPASS_SECRET"]
    api_bypass = os.environ["MDB_API_VERCEL_BYPASS_SECRET"]
    web_headers = {"x-vercel-protection-bypass": web_bypass}
    direct_headers = {"x-vercel-protection-bypass": api_bypass}
    failures: list[str] = []
    scanned: dict[str, bytes] = {}
    public_fields: set[str] = set()

    for path in WEB_PATHS:
        status, _, body = fetch(web + path, web_headers)
        if status != 200:
            failures.append(f"route {path} returned {status}")
        if path == "/" and (
            b"Release: <!-- -->MDB_ANALYTICAL_2024_2" not in body
            and b"Release: MDB_ANALYTICAL_2024_2" not in body
        ):
            failures.append("home footer does not expose the active analytical release")
        scanned[f"page:{path}"] = body

    assets = {
        match.decode()
        for body in scanned.values()
        for match in ASSET.findall(body)
        if match.startswith(b"/")
    }
    for path in sorted(assets):
        status, _, body = fetch(web + path, web_headers)
        if status != 200:
            failures.append(f"asset {path} returned {status}")
        scanned[f"asset:{path}"] = body

    for path in API_PATHS:
        status, headers, body = fetch(web + path, web_headers)
        if status != 200:
            failures.append(f"public API {path} returned {status}")
            continue
        if headers.get("access-control-allow-credentials"):
            failures.append(f"credentialed CORS enabled at {path}")
        try:
            public_fields |= {field.lower() for field in field_names(json.loads(body))}
        except json.JSONDecodeError:
            failures.append(f"non-JSON API response at {path}")
        scanned[f"api:{path}"] = body

    for path in ("/health", "/ready", "/docs", "/redoc", "/openapi.json", "/api/v1/releases"):
        status, _, body = fetch(api + path, direct_headers)
        if status not in {401, 403, 404}:
            failures.append(f"direct backend {path} returned {status}")
        if b"release_id" in body or b"database" in body.lower():
            failures.append(f"direct backend leaked application data at {path}")

    hostile = (
        ("/api/public/v1/health-regions?uf=AC%27%20OR%20%271%27%3D%271", {400, 422}),
        ("/api/public/v1/health-regions?cursor=../../.env", {400}),
        ("/api/public/v1/health-regions/12001%2F..%2F.env", {400, 404, 422}),
    )
    for path, expected in hostile:
        status, _, body = fetch(web + path, web_headers)
        if status not in expected or any(
            marker in body.lower() for marker in (b"traceback", b"postgres", b"psycopg")
        ):
            failures.append(f"unsafe hostile-input response at {path}: {status}")

    for method in ("POST", "PUT", "PATCH", "DELETE"):
        status, _, _ = fetch(web + "/api/public/v1/releases", web_headers, method)
        if status != 405:
            failures.append(f"{method} returned {status}, expected 405")

    cors_headers = {**web_headers, "Origin": "https://untrusted.example"}
    status, headers, _ = fetch(web + "/api/public/v1/releases", cors_headers)
    if status != 200 or headers.get("access-control-allow-origin") != "*":
        failures.append("public CORS contract failed")
    if headers.get("access-control-allow-credentials"):
        failures.append("credentialed CORS enabled")
    if headers.get("ratelimit-limit") != "120":
        failures.append("external rate-limit headers missing")

    secret_hits = sorted(
        {
            label
            for body in scanned.values()
            for label, pattern in SECRET_PATTERNS.items()
            if pattern.search(body)
        }
    )
    if secret_hits:
        failures.append("browser/API secret patterns found")
    pii = sorted(public_fields & PII_FIELDS)
    raw = sorted(public_fields & RAW_FIELDS)
    if pii or raw:
        failures.append("forbidden public fields found")

    open_data = validate_open_data()
    result = {
        "status": "PASS" if not failures else "FAIL",
        "web_url": web,
        "api_url": api,
        "failures": failures,
        "routes_scanned": len(WEB_PATHS),
        "assets_scanned": len(assets),
        "api_contracts_scanned": len(API_PATHS),
        "scanned_bytes_sha256": hashlib.sha256(
            b"".join(scanned[key] for key in sorted(scanned))
        ).hexdigest(),
        "direct_backend": "DENIED"
        if not any("direct backend" in item for item in failures)
        else "FAIL",
        "fastapi_docs": "DENIED"
        if not any("/docs" in item or "/openapi.json" in item for item in failures)
        else "FAIL",
        "sql_injection_and_error_sanitization": "PASS"
        if not any("hostile-input" in item for item in failures)
        else "FAIL",
        "unsupported_methods": "DENIED"
        if not any("expected 405" in item for item in failures)
        else "FAIL",
        "cors": "PASS" if not any("CORS contract" in item for item in failures) else "FAIL",
        "credentialed_cors": "DENIED"
        if not any("credentialed CORS" in item for item in failures)
        else "FAIL",
        "rate_limit": "PASS_WITH_PER_INSTANCE_LIMITATION"
        if not any("rate-limit" in item for item in failures)
        else "FAIL",
        "secret_leak_count": len(secret_hits),
        "pii_field_count": len(pii),
        "raw_field_count": len(raw),
        "public_exact_flow_below_5": open_data["public_exact_flow_below_5"],
        "raw_source_leaks": open_data["raw_source_leaks"],
        "open_data_privacy": open_data["status"],
        "note": (
            "Rate limiting is per warm serverless instance; headers and deterministic logic "
            "are validated without a burst probe."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
