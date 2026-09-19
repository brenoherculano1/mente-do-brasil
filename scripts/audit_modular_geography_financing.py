"""Inspect territorial candidates and all SIOPS rows; never approve an undated crosswalk."""

import json
import zipfile
from pathlib import Path

import pandas as pd

from scripts.acquire_phase3_sources import sha256, write_json

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/annual_2025"
AUDIT = ROOT / "audit_results/modular_2025"


def geography():
    old = pd.read_parquet(
        ROOT / "data/canonical/MDB_ANALYTICAL_2024_1/municipality_health_region_crosswalk.parquet"
    )
    old["municipality"] = old.municipality_code_datasus6.astype(str)
    with zipfile.ZipFile(RAW / "macroregiao_current.zip") as archive:
        member = next(n for n in archive.namelist() if n.lower().endswith(".csv"))
        current = pd.read_csv(archive.open(member), sep=";", dtype=str)
    current = current.rename(
        columns={
            "cod_municipio": "municipality",
            "cod_regiao_de_saude": "health_region_code",
            "regiao_de_saude": "health_region_name",
        }
    )
    merged = old[["municipality", "health_region_code", "health_region_name"]].merge(
        current[["municipality", "health_region_code", "health_region_name"]],
        on="municipality",
        how="outer",
        suffixes=("_2024", "_current"),
        indicator=True,
    )
    changed = merged.loc[
        merged._merge.ne("both")
        | merged.health_region_code_2024.ne(merged.health_region_code_current)
    ]
    changed.to_csv(AUDIT / "current_vs_2024_assignments_NOT_2025_LINEAGE.csv", index=False)
    base = RAW / "BASE_DE_DADOS_CNES_202512.ZIP"
    with zipfile.ZipFile(base) as archive:
        municipalities = pd.read_csv(
            archive.open("tbMunicipio202512.csv"), sep=";", dtype=str, encoding="latin1"
        )
        establishments = pd.read_csv(
            archive.open("tbEstabelecimento202512.csv"),
            sep=";",
            dtype=str,
            encoding="latin1",
            usecols=["CO_UNIDADE", "CO_REGIAO_SAUDE"],
        )
    establishments["municipality"] = establishments.CO_UNIDADE.str[:6]
    result = {
        "status": "UNDER_VALIDATION",
        "regional_publication_allowed": False,
        "reason": "NO_VALIDATED_NATIONAL_DEC2025_CROSSWALK",
        "current_resource_url": "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/dbgeral/macroregiao_de_saude_csv.zip",
        "current_resource_sha256": sha256(RAW / "macroregiao_current.zip"),
        "current_rows": len(current),
        "current_regions": current.health_region_code.nunique(),
        "current_duplicate_municipalities": int(current.municipality.duplicated().sum()),
        "current_vs_locked_added_municipalities": sorted(
            set(current.municipality) - set(old.municipality)
        ),
        "current_vs_locked_removed_municipalities": sorted(
            set(old.municipality) - set(current.municipality)
        ),
        "current_vs_locked_changed_assignments": int(
            (
                merged._merge.eq("both")
                & merged.health_region_code_2024.ne(merged.health_region_code_current)
            ).sum()
        ),
        "current_has_no_historical_effective_date": True,
        "dec2025_base_url": "ftp://ftp.datasus.gov.br/cnes/BASE_DE_DADOS_CNES_202512.ZIP",
        "dec2025_base_sha256": sha256(base),
        "tbMunicipio_rows": len(municipalities),
        "tbMunicipio_fields": list(municipalities.columns),
        "tbMunicipio_has_health_region_field": False,
        "establishment_rows": len(establishments),
        "establishment_region_blank": int(establishments.CO_REGIAO_SAUDE.isna().sum()),
        "municipalities_with_multiple_establishment_region_labels": int(
            establishments.groupby("municipality").CO_REGIAO_SAUDE.nunique().gt(1).sum()
        ),
        "rejected_inference": (
            "Establishment region labels are incomplete/nonstandard and not a municipal "
            "crosswalk; do not normalize them into national IDs"
        ),
        "display_geometry": "2024 geometry untouched; no 2025 scientific/display geometry approved",
        "lineage_2024_2025": None,
    }
    write_json(AUDIT / "geography_qc.json", result)
    print(json.dumps(result), flush=True)


def financing():
    path = RAW / "SIOPS_municipal_2025_B6.zip.part"
    rows = missing = negative = unhomologated = 0
    municipalities, years, phases, codes = set(), set(), set(), set()
    with zipfile.ZipFile(path) as archive:
        member = next(n for n in archive.namelist() if n.lower().endswith(".csv"))
        for chunk in pd.read_csv(
            archive.open(member), sep=";", dtype=str, encoding="utf-8-sig", chunksize=150000
        ):
            rows += len(chunk)
            municipalities.update(chunk["Cód.Município"].dropna())
            years.update(chunk.Ano.dropna())
            phases.update(chunk.Fase.dropna())
            codes.update(chunk.Codigo.dropna())
            values = pd.to_numeric(chunk.Valor, errors="coerce")
            missing += int(values.isna().sum())
            negative += int(values.lt(0).sum())
            unhomologated += int(chunk.Data_Homologacao.isna().sum())
    write_json(
        AUDIT / "siops_qc.json",
        {
            "status": "UNDER_VALIDATION",
            "publication_allowed": False,
            "url": "https://portalfns.saude.gov.br/idg_download/siops-despesas-por-fonte-subfuncao-natureza-municipais-2025-6o-bimestre/",
            "sha256": sha256(path),
            "rows_read": rows,
            "municipalities": len(municipalities),
            "municipality_codes": sorted(municipalities),
            "years": sorted(years),
            "phases": sorted(phases),
            "account_codes": sorted(codes),
            "missing_or_nonnumeric_values": missing,
            "negative_values_require_interpretation": negative,
            "rows_without_homologation_date": unhomologated,
            "reason": (
                "Detailed account hierarchy cannot be summed across parent/child accounts "
                "or expenditure phases. Existing group17 report-total semantics not yet "
                "reconciled; historical geography also pending."
            ),
            "is_mental_health_specific": False,
            "coverage_scope": (
                "Every CSV row parsed; duplicate accounting grain and official report "
                "reconciliation still pending"
            ),
        },
    )
    print(
        f"SIOPS: {rows} rows, {len(municipalities)} municipalities inspected; not published",
        flush=True,
    )


if __name__ == "__main__":
    AUDIT.mkdir(parents=True, exist_ok=True)
    geography()
    financing()
