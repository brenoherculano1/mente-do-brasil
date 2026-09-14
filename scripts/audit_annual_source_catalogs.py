"""Capture official catalog evidence only; file presence is not scientific readiness."""

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

UFS = "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split()
PAGES = {
    "SIM_status": "https://dadosabertos.saude.gov.br/dataset/sim",
    "population_documentation": "https://www.gov.br/saude/pt-br/composicao/seidigi/demas/dados-populacionais",
    "SIOPS_downloads": "https://portalfns.saude.gov.br/siops/siops-downloads/",
    "crosswalk": "https://dadosabertos.saude.gov.br/dataset/macrorregiao-de-saude/resource/3bd28e64-0a82-44d9-8de1-4894634f2b6a",
    "IBGE_geometry": "https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/15774-malhas.html",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    year = args.year
    specs = {
        "SIM_files": (
            "SIM/CID10/DORES/",
            {f"DO{uf}{y}.dbc" for uf in UFS for y in range(year - 2, year + 1)},
        ),
        "SIH_files": (
            "SIHSUS/200801_/Dados/",
            {
                f"RD{uf}{y % 100:02}{m:02}.dbc"
                for uf in UFS
                for y in range(year - 2, year + 1)
                for m in range(1, 13)
            },
        ),
        "POPSVS_files": (
            "IBGE/POPSVS/",
            {f"POPSBR{y % 100:02}.zip" for y in range(year - 2, year + 1)},
        ),
        **{
            f"CNES_{kind}": (
                f"CNES/200508_/Dados/{kind}/",
                {f"{kind}{uf}{year % 100:02}12.dbc" for uf in UFS},
            )
            for kind in ["ST", "LT", "PF"]
        },
    }
    receipts = []
    for name in [*specs, *PAGES]:
        ftp = name in specs
        url = "ftp://ftp.datasus.gov.br/dissemin/publicos/" + specs[name][0] if ftp else PAGES[name]
        command = ["curl", "-fsSL", "--max-time", "35"]
        if ftp:
            command += ["--list-only"]
        response = subprocess.run([*command, url], capture_output=True)
        receipt = {
            "name": name,
            "url": url,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "exit_code": response.returncode,
            "error": response.stderr.decode(errors="replace"),
            "sha256": hashlib.sha256(response.stdout).hexdigest(),
            "scope": "Catalog only; no national record-level coverage/schema validation",
        }
        if response.returncode == 0:
            content = response.stdout.decode(errors="replace")
            if ftp:
                available = {line.strip().upper() for line in content.splitlines()}
                expected = specs[name][1]
                receipt.update(
                    expected_count=len(expected),
                    found=sorted(n for n in expected if n.upper() in available),
                    missing=sorted(n for n in expected if n.upper() not in available),
                )
                receipt["found_count"] = len(receipt["found"])
            else:
                soup = BeautifulSoup(content, "html.parser")
                for tag in soup(["script", "style", "nav", "header", "footer"]):
                    tag.decompose()
                text = soup.get_text("\n", strip=True)
                (args.output / f"{name}.txt").write_text(text)
                receipt["relevant_links"] = [
                    {"label": a.get_text(" ", strip=True), "href": a["href"]}
                    for a in soup.find_all("a", href=True)
                    if re.search(
                        r"2025|pop|csv|download|zip|licen", a.get_text(" ") + a["href"], re.I
                    )
                ]
        receipts.append(receipt)
        (args.output / "catalog_receipts.json").write_text(json.dumps(receipts, indent=2) + "\n")
        print(
            json.dumps(
                {
                    k: v
                    for k, v in receipt.items()
                    if k not in {"found", "missing", "relevant_links"}
                }
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
