"""Capture all report pages for human visual inspection; never infer visual PASS."""

import hashlib
import json
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/phase3_closure_qc_2026-08-31/pdf_final"


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    results = []
    for code in ["12001", "53001", "35011", "29001", "41001"]:
        url = f"http://127.0.0.1:8101/api/v1/health-regions/{code}/report.pdf"
        with urllib.request.urlopen(url, timeout=60) as response:
            payload = response.read()
            headers = dict(response.headers)
        with urllib.request.urlopen(url, timeout=60) as response:
            assert payload == response.read()
        path = DEST / f"report_{code}.pdf"
        path.write_bytes(payload)
        text = subprocess.check_output(["pdftotext", str(path), "-"]).decode()
        for required in [
            "MDB_ANALYTICAL_2024_2",
            "MDB_TERRITORIAL_REPORT_2.0",
            "SIOPS",
            "pacientes",
        ]:
            assert required in text, (code, required)
        assert "127.0.0.1" not in text
        assert "MDB_REPORTLAB_GENERATOR_1.1" in headers["etag"]
        bbox = ET.fromstring(subprocess.check_output(["pdftotext", "-bbox", str(path), "-"]))
        pages = bbox.findall(".//{*}page")
        outside = []
        for index, page in enumerate(pages, 1):
            for word in page.findall(".//{*}word"):
                if (
                    float(word.attrib["xMin"]) < 30
                    or float(word.attrib["xMax"]) > float(page.attrib["width"]) - 30
                ):
                    outside.append({"page": index, "text": word.text})
        subprocess.run(
            ["pdftoppm", "-scale-to", "1100", "-png", str(path), str(path.with_suffix(""))],
            check=True,
        )
        for start in [1, 5]:
            sheet = Image.new("RGB", (1120, 1600), "#c8c8c8")
            draw = ImageDraw.Draw(sheet)
            for position, number in enumerate(range(start, start + 4)):
                im = Image.open(DEST / f"report_{code}-{number}.png").convert("RGB")
                im.thumbnail((550, 770))
                x, y = (position % 2) * 560, (position // 2) * 800
                sheet.paste(im, (x + 5, y + 25))
                draw.text((x + 10, y + 5), f"{code} / page {number}", fill="black")
            sheet.save(DEST / f"contact_{code}_{start}.jpg", quality=92)
        results.append(
            {
                "code": code,
                "pages": len(pages),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "repeat_same_sha": True,
                "words_outside_safe_page_bounds": outside,
                "headers": headers,
                "visual_status": "REQUIRES_INSPECTION",
            }
        )
    (ROOT / "audit_results/phase3_closure/pdf_final_structural.json").write_text(
        json.dumps(results, indent=2) + "\n"
    )
    print([(r["code"], r["pages"], len(r["words_outside_safe_page_bounds"])) for r in results])


if __name__ == "__main__":
    main()
