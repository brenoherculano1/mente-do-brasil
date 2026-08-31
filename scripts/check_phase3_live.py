"""Record read-only current-release API, security, and source-inventory evidence."""

import hashlib
import json
import urllib.error
import urllib.request

from scripts.audit_phase3_recovery import AUDIT, CURRENT, ROOT, connect, container_settings, save


def request(base, path, headers=None, method="GET"):
    req = urllib.request.Request(base + path, headers=headers or {}, method=method)
    try:
        response = urllib.request.urlopen(req, timeout=60)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        body = response.read()
        return (
            response.status,
            {key.lower(): value for key, value in response.headers.items()},
            body,
        )


def main():
    upstream, frontend = "http://127.0.0.1:8101", "http://127.0.0.1:3000"
    paths = [
        "/api/v1/health-regions/12001/timeline",
        "/api/v1/changes/health-regions?min_change_families=0",
        "/api/v1/financing/health-regions?year=2024",
        "/api/v1/health-regions/53001/financing",
        "/api/v1/health-regions/12001/flows",
        "/api/v1/manager/health-regions/12001",
        "/api/v1/health-regions/12001/report.pdf",
    ]
    results = []
    for path in paths:
        a, b = request(upstream, path), request(frontend, path)
        results.append(
            {
                "path": path,
                "upstream": a[0],
                "same_origin": b[0],
                "same_bytes": a[2] == b[2],
                "headers": b[1],
            }
        )
        assert a[0] == b[0] == 200 and a[2] == b[2], path
    security = {}
    for path, expected in [
        ("/docs", 404),
        ("/redoc", 404),
        ("/openapi.json", 404),
        ("/api/v1/map/health-regions?include_geometry=true&geometry_profile=full", 403),
        ("/api/v1/states/AC%27%20OR%20%271%27%3D%271", 422),
    ]:
        observed = request(upstream, path)[0]
        security[path] = observed
        assert observed == expected
    for origin, expected in [("http://127.0.0.1:3000", 200), ("https://untrusted.invalid", 400)]:
        result = request(
            upstream,
            paths[0],
            {"Origin": origin, "Access-Control-Request-Method": "GET"},
            "OPTIONS",
        )
        security[f"cors_{origin}"] = result[0]
        assert result[0] == expected
    status, headers, body = request(frontend, "/")
    security["homepage"] = {"status": status, "headers": headers}
    assert status == 200
    assert "default-src 'self'" in headers.get("content-security-policy", "")
    assert b'name="robots" content="noindex' in body
    security["homepage"]["robots_meta_noindex"] = True
    # A blocked full-geometry request exercises ingress throttling without a heavy query.
    rate_statuses = []
    for _ in range(40):
        status, headers, _ = request(
            frontend, "/api/v1/map/health-regions?include_geometry=true&geometry_profile=full"
        )
        rate_statuses.append(status)
        if status == 429:
            assert headers.get("retry-after")
            break
    security["rate_limit"] = rate_statuses
    assert 429 in rate_statuses
    save("api_security_live.json", {"apis": results, "security": security, "status": "PASS"})
    with connect(container_settings()) as conn:
        data = {}
        data["changes_distribution"] = conn.execute(
            "SELECT from_year,to_year,matched_change_families,count(*) "
            "FROM analytics.health_region_changes GROUP BY 1,2,3 ORDER BY 1,2,3"
        ).fetchall()
        data["financing_coverage"] = conn.execute(
            "SELECT headline_available,count(*) FROM analytics.health_region_financing GROUP BY 1"
        ).fetchall()
        data["flows"] = conn.execute(
            "SELECT count(*),count(*) FILTER (WHERE suppressed), "
            "count(*) FILTER (WHERE admissions < 5),count(*) FILTER "
            "(WHERE suppressed AND admissions IS NOT NULL) FROM analytics.hospitalization_flows"
        ).fetchone()
        data["temporal_2024_max_abs_diff_vs_serving"] = conn.execute(
            "SELECT max(abs((t.values->>'need_score')::float8-m.need_score)), "
            "max(abs((t.values->>'capacity_score')::float8-m.capacity_score)), "
            "max(abs((t.values->>'mismatch_score')::float8-m.mismatch_score)) "
            "FROM analytics.health_region_temporal t JOIN analytics.health_region_metrics m "
            "ON t.health_region_code=m.health_region_code AND m.release_id=%s WHERE t.year=2024",
            (CURRENT,),
        ).fetchone()
        data["qualification"] = "Serving consistency only; not independent source recomputation."
        save("advanced_live_checks.json", data)
    inventory = []
    protected = json.loads((ROOT / "audit_results/phase3_protected_hashes.json").read_text())[
        "files"
    ]
    for item in protected:
        path = ROOT / item["path"]
        observed = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
        inventory.append(
            {
                "path": item["path"],
                "expected_sha256": item["expected"],
                "observed_sha256": observed,
                "status": "PASS" if observed == item["expected"] else "MISSING_OR_MISMATCH",
            }
        )
    for _, files in json.loads((AUDIT / "advanced_source_hash_registry.json").read_text()):
        for stem, digest in files.items():
            relative = f"data/product_intelligence/{CURRENT}/{stem}.parquet"
            path = ROOT / relative
            observed = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
            inventory.append(
                {
                    "path": relative,
                    "expected_sha256": digest,
                    "observed_sha256": observed,
                    "status": "PASS" if digest == observed else "MISSING_OR_MISMATCH",
                }
            )
    for relative in [
        "data/raw/siops_official/MDB_SIOPS_SNAPSHOT_20260831_1.jsonl",
        "data/raw/imported/MDB_VALIDATED_IMPORT_BUNDLE_2026-08-24/mdb_import_bundle/geography/health_regions_LOCKED.gpkg",
    ]:
        inventory.append({"path": relative, "exists": (ROOT / relative).exists()})
    save("source_inventory.json", inventory)
    print("API/security PASS; advanced DB consistency and source inventory recorded")


if __name__ == "__main__":
    main()
