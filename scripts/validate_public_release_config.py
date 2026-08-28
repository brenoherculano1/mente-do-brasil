"""Validate application-side public release configuration."""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
TRUE_VALUES = {"1", "true", "yes", "on"}


def load_local_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key, value)


def env_true(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in TRUE_VALUES


def valid_https_origin(value: str | None) -> bool:
    if not value:
        return False
    parsed = urlparse(value)
    return (
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and not parsed.username
        and not parsed.password
        and parsed.path in {"", "/"}
        and not parsed.params
        and not parsed.query
        and not parsed.fragment
    )


def file_exists(path: str) -> bool:
    return (ROOT / path).exists()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public", action="store_true", help="validate future public mode")
    args = parser.parse_args()
    load_local_env()

    indexing = env_true("MDB_PUBLIC_INDEXING_ENABLED")
    contact = os.environ.get("MDB_PUBLIC_CONTACT_EMAIL", "").strip()
    security = os.environ.get("MDB_PUBLIC_SECURITY_EMAIL", "").strip() or contact
    site_url = os.environ.get("MDB_PUBLIC_SITE_URL", "").strip()
    failures: list[str] = []

    if not args.public:
        if indexing:
            failures.append("prelaunch_requires_indexing_disabled")
        status = "PASS_PRE_RELEASE" if not failures else "FAIL_PRE_RELEASE"
    else:
        checks = {
            "indexing_enabled": indexing,
            "site_url_https_origin": valid_https_origin(site_url),
            "contact_email": bool(EMAIL.fullmatch(contact)),
            "security_email": bool(EMAIL.fullmatch(security)),
            "privacy_notice": file_exists("metadata/legal/privacy_notice.yaml"),
            "robots": file_exists("web/app/robots.ts"),
            "sitemap": file_exists("web/app/sitemap.ts"),
            "healthz": file_exists("web/app/healthz/route.ts"),
            "readyz": file_exists("web/app/readyz/route.ts"),
            "security_txt": file_exists("web/app/.well-known/security.txt/route.ts"),
            "observability_doc": file_exists("docs/operations/observability.md"),
            "recovery_runbook": file_exists("docs/operations/recovery_runbook.md"),
            "backup_script": file_exists("scripts/backup_serving_db.sh"),
            "restore_script": file_exists("scripts/restore_serving_db.sh"),
            "rebuild_script": file_exists("scripts/rebuild_serving_db.sh"),
        }
        failures.extend(name for name, passed in checks.items() if not passed)
        status = "APPLICATION_PUBLIC_CONFIG_READY" if not failures else "FAIL_PUBLIC_CONFIG"

    print(f"status={status}")
    print(f"public_mode={args.public}")
    print(f"indexing_enabled={indexing}")
    print(f"site_url_valid={valid_https_origin(site_url)}")
    print(f"contact_email_configured={bool(EMAIL.fullmatch(contact))}")
    print(f"security_email_resolved={bool(EMAIL.fullmatch(security))}")
    print(f"failures={','.join(failures) if failures else 'none'}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
