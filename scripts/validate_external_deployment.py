#!/usr/bin/env python3
"""Low-volume external QA for a Mente do Brasil web/API deployment pair."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import time
import urllib.error
import urllib.request

EXPECTED_ZIP_SHA = "2b3b1fc749bfd71181115c2cd9467bf26cb1572bd0c0e9687dabccffab3775bc"
EXPECTED_ZIP_BYTES = 914_294
WEB_PATHS = [
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
    "/privacidade",
    "/contato",
    "/estado/AC",
    "/regiao/12001",
]
PUBLIC_API_PATHS = [
    "/api/public/v1/releases",
    "/api/public/v1/releases/MDB_OPEN_DATA_2024_1",
    "/api/public/v1/health-regions?limit=1",
    "/api/public/v1/health-regions/12001",
    "/api/public/v1/health-regions/12001/timeline",
    "/api/public/v1/changes?from_year=2022&to_year=2024&uf=AC",
    "/api/public/v1/financing?year=2024&uf=AC",
    "/api/public/v1/health-regions/12001/financing",
    "/api/public/v1/health-regions/12001/flows",
    "/api/public/v1/health-regions/12001/peers",
    "/api/public/v1/municipalities/1200013/health-region",
    "/api/public/v1/metadata/indicators",
    "/api/public/v1/metadata/methodology",
    "/api/public/v1/openapi.json",
]


def request(url: str, method: str = "GET", headers: dict[str, str] | None = None):
    started = time.perf_counter()
    req = urllib.request.Request(url, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            body = response.read()
            response_headers = {key.lower(): value for key, value in response.headers.items()}
            return response.status, response_headers, body, time.perf_counter() - started
    except urllib.error.HTTPError as error:
        response_headers = {key.lower(): value for key, value in error.headers.items()}
        return error.code, response_headers, error.read(), time.perf_counter() - started


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(len(ordered) * fraction))]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--web-url", required=True)
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--performance", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    web = args.web_url.rstrip("/")
    api = args.api_url.rstrip("/")
    bypass = os.environ.get("MDB_STAGING_BYPASS_SECRET")
    web_headers = {"x-vercel-protection-bypass": bypass} if bypass else {}
    failures: list[str] = []
    checks: dict[str, object] = {}

    for path in WEB_PATHS + ["/healthz", "/readyz"] + PUBLIC_API_PATHS:
        status, _, _, _ = request(web + path, headers=web_headers)
        if status != 200:
            failures.append(f"web {path}: HTTP {status}")

    for path in ["/health", "/ready", "/docs", "/redoc", "/openapi.json", "/api/v1/releases"]:
        status, _, body, _ = request(api + path)
        if status not in {401, 403, 404}:
            failures.append(f"direct API {path}: HTTP {status}")
        if b"release_id" in body or b"database" in body:
            failures.append(f"direct API {path}: application data leaked")

    download_path = "/downloads/MDB_OPEN_DATA_2024_1/MDB_OPEN_DATA_2024_1.zip"
    status, headers, archive, _ = request(web + download_path, headers=web_headers)
    archive_sha = hashlib.sha256(archive).hexdigest()
    if status != 200 or len(archive) != EXPECTED_ZIP_BYTES or archive_sha != EXPECTED_ZIP_SHA:
        failures.append("live immutable ZIP identity mismatch")
    checks["open_data_zip"] = {
        "status": status,
        "bytes": len(archive),
        "sha256": archive_sha,
        "etag": headers.get("etag"),
    }

    cors_headers = {**web_headers, "Origin": "https://untrusted.example"}
    status, headers, _, _ = request(web + "/api/public/v1/releases", headers=cors_headers)
    if status != 200 or headers.get("access-control-allow-origin") != "*":
        failures.append("public CORS contract failed")
    if headers.get("access-control-allow-credentials"):
        failures.append("credentialed public CORS was enabled")

    status, _, _, _ = request(web + "/api/public/v1/releases", method="POST", headers=web_headers)
    if status != 405:
        failures.append(f"public API POST returned {status}, expected 405")
    status, _, _, _ = request(
        web + "/downloads/MDB_OPEN_DATA_2024_1/..%2F.env", headers=web_headers
    )
    if status not in {400, 404}:
        failures.append(f"download traversal returned {status}")

    if args.performance:
        latencies = []
        for _ in range(30):
            status, _, _, elapsed = request(
                web + "/api/public/v1/releases", headers=web_headers
            )
            if status != 200:
                failures.append(f"performance probe returned {status}")
                break
            latencies.append(elapsed * 1000)
            time.sleep(0.1)
        if latencies:
            checks["latency_ms"] = {
                "requests": len(latencies),
                "median": round(statistics.median(latencies), 2),
                "p95": round(percentile(latencies, 0.95), 2),
                "max": round(max(latencies), 2),
            }

    result = {
        "status": "PASS" if not failures else "FAIL",
        "web_url": web,
        "api_url": api,
        "checks": checks,
        "failures": failures,
        "request_profile": "sequential_low_volume",
    }
    serialized = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(serialized + "\n")
    print(serialized)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
