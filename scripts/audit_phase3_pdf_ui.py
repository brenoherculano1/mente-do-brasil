"""Record a narrow live PDF and production UI regression gate."""

import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = "http://127.0.0.1:3000/api/v1/health-regions/12001/report.pdf"


def fetch() -> tuple[bytes, str]:
    with urllib.request.urlopen(URL, timeout=60) as response:
        return response.read(), response.headers.get_content_type()


first, first_type = fetch()
second, second_type = fetch()
temporary = Path("/tmp/mdb_phase3_report_spot_check.pdf")
temporary.write_bytes(first)
pdfinfo = subprocess.run(
    ["pdfinfo", str(temporary)], check=True, capture_output=True, text=True
).stdout
pages = int(
    next(
        line.split(":", 1)[1].strip() for line in pdfinfo.splitlines() if line.startswith("Pages:")
    )
)
screenshots = sorted((ROOT / "docs/phase3_closure_qc_2026-08-31").glob("*.png"))
result = {
    "status": "PASS_WITH_REGRESSION_SCOPE",
    "qualification": (
        "Live deterministic PDF and production E2E screenshot inventory; prior editorial PDF QA "
        "remains authoritative because no report layout or visual code changed."
    ),
    "pdf": {
        "status": "PASS",
        "content_types": [first_type, second_type],
        "bytes": len(first),
        "pages": pages,
        "sha256": hashlib.sha256(first).hexdigest(),
        "repeat_sha256": hashlib.sha256(second).hexdigest(),
        "deterministic": first == second,
        "valid_header": first.startswith(b"%PDF-"),
    },
    "ui": {
        "status": "PASS",
        "production_e2e_evidence": "audit_results/phase3_production_e2e_final.txt",
        "screenshot_count": len(screenshots),
        "screenshots_nonempty": all(path.stat().st_size > 0 for path in screenshots),
    },
}
if not all(
    [
        result["pdf"]["deterministic"],
        result["pdf"]["valid_header"],
        pages > 0,
        first_type == second_type == "application/pdf",
        screenshots,
        result["ui"]["screenshots_nonempty"],
    ]
):
    raise RuntimeError(json.dumps(result, indent=2))
(ROOT / "audit_results/phase3_ui_pdf_regression_final.json").write_text(
    json.dumps(result, indent=2) + "\n"
)
print("PDF/UI regression PASS_WITH_REGRESSION_SCOPE")
