"""Acquire and inspect 2025 sources without creating a scientific release.

All person/link identifiers stay in private raw/cache paths. Regional publication
requires a separate approved geography, denominator and indicator QC gate.
"""

from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from scripts import acquire_phase3_sources as acquisition
from scripts.validate_phase3_source_gate import read_dbc, selected_dbf

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/annual_2025"
CACHE = ROOT / "data/staging/annual_2025"
AUDIT = ROOT / "audit_results/modular_2025"
UFS = "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split()


def plan():
    items = []
    for family in ["ST", "LT", "PF", "SIH", "population"]:
        periods = range(1, 13) if family == "SIH" else [12]
        for uf in UFS if family != "population" else ["BR"]:
            for month in periods:
                name = f"{family}{uf}25{month:02}.dbc"
                directory = f"CNES/200508_/Dados/{family}/"
                dataset = "CNES"
                if family == "SIH":
                    name, directory, dataset = (
                        f"RD{uf}25{month:02}.dbc",
                        "SIHSUS/200801_/Dados/",
                        "SIH",
                    )
                elif family == "population":
                    name, directory, dataset = "POPSBR25.zip", "IBGE/POPSVS/", "population"
                items.append(
                    {
                        "dataset": dataset,
                        "family": family,
                        "period": "2025",
                        "competence": f"2025-{month:02}",
                        "uf": uf,
                        "original_filename": name,
                        "official_url": acquisition.FTP + directory + name,
                    }
                )
    return items


def process(item):
    acquisition.RAW = RAW
    receipt = acquisition.download(item)
    path = ROOT / receipt["local_path"]
    family, name = item["family"], item["original_filename"]
    out = CACHE / (name + ".parquet")
    qc_path = AUDIT / (name + ".qc.json")
    if out.exists() and qc_path.exists():
        previous = json.loads(qc_path.read_text())
        if previous["input_sha256"] != receipt["sha256"] or previous[
            "output_sha256"
        ] != acquisition.sha256(out):
            raise ValueError("Immutable source/cache hash mismatch")
        return previous
    qc = {
        "file": name,
        "family": family,
        "uf": item["uf"],
        "input_sha256": receipt["sha256"],
        "source": item["official_url"],
        "retrieved_at": receipt["retrieved_at"],
        "schema": receipt["schema"],
        "publication_status": "UNDER_VALIDATION",
        "geography_validated": False,
    }
    if family == "population":
        with tempfile.TemporaryDirectory(prefix="mdb-pop-2025-") as directory:
            with zipfile.ZipFile(path) as archive:
                members = [n for n in archive.namelist() if n.lower().endswith(".dbf")]
                if len(members) != 1:
                    raise ValueError("Ambiguous population DBF")
                dbf = Path(directory) / "population.dbf"
                dbf.write_bytes(archive.read(members[0]))
            fields = {f["name"].upper(): f["name"] for f in receipt["schema"]["fields"]}
            wanted = ["COD_MUN", "ANO", "SEXO", "IDADE", "POP"]
            data = selected_dbf(dbf, [fields[c] for c in wanted])
            data.columns = wanted
        if data.duplicated(["COD_MUN", "ANO", "SEXO", "IDADE"]).any():
            raise ValueError("Duplicate population keys")
        if set(data.ANO) != {"2025"} or set(data.IDADE.astype(int)) != set(range(81)):
            raise ValueError("Population year/age definition differs")
        data["municipality"] = data.COD_MUN.str[:6]
        data["band"] = np.minimum(data.IDADE.astype(int) // 5, 16)
        data["population"] = data.POP.astype("int64")
        if data.population.lt(0).any():
            raise ValueError("Negative population")
        qc.update(
            decoded_rows=len(data),
            sex_codes=sorted(data.SEXO.unique().tolist()),
            municipality_cell_counts=data.groupby("municipality").size().value_counts().to_dict(),
            municipality_code_lengths=sorted(data.COD_MUN.str.len().unique().tolist()),
            schema_case_normalized=True,
        )
        result = data.groupby(["municipality", "band"], as_index=False).population.sum()
        qc.update(
            municipalities=int(result.municipality.nunique()),
            age_bands=sorted(map(int, result.band.unique())),
            total_population=int(result.population.sum()),
            nonpositive_cells=int(result.population.le(0).sum()),
            duplicate_municipality_band=int(result.duplicated(["municipality", "band"]).sum()),
        )
    else:
        with path.open("rb") as stream:
            schema = acquisition.schema_header(stream)
        fields = {f["name"] for f in schema["fields"]}
        columns = {
            "ST": ["CNES", "CODUFMUN", "TP_UNID"],
            "LT": ["CNES", "CODUFMUN", "TP_UNID", "CODLEITO", "QT_SUS"],
            "PF": ["CNES", "CODUFMUN", "CBO", "PROF_SUS", "HORA_AMB", "HORAHOSP", "HORAOUTR"],
            "SIH": [
                "MUNIC_RES",
                "MUNIC_MOV",
                "CNES",
                "DIAG_PRINC",
                "N_AIH",
                "ANO_CMPT",
                "MES_CMPT",
            ],
        }[family]
        if family == "PF":
            columns += [
                c
                for c in [
                    "CNS_PROF",
                    "CPF_PROF",
                    "NOMEPROF",
                    "VINCULAC",
                    "VINCUL_C",
                    "VINCUL_A",
                    "VINCUL_N",
                ]
                if c in fields
            ]
        data = read_dbc(path, columns)
        qc["decoded_rows"] = len(data)
        if family == "SIH":
            if set(data.ANO_CMPT) != {"2025"} or set(data.MES_CMPT.astype(int)) != {
                int(item["competence"][-2:])
            }:
                raise ValueError(f"Unexpected SIH processing competence: {name}")
            code = data.DIAG_PRINC.str[:3]
            selected = data.loc[code.between("F00", "F09") | code.between("F20", "F99")].copy()
            qc.update(
                selected_rows=len(selected),
                duplicate_aih=int(selected.N_AIH.duplicated().sum()),
                duplicate_selected_rows=int(selected.duplicated().sum()),
                excluded_f10_f19=int(code.between("F10", "F19").sum()),
            )
            result = (
                selected.groupby(["MUNIC_RES", "MUNIC_MOV"], dropna=False)
                .size()
                .rename("admissions")
                .reset_index()
            )
            result = result.rename(
                columns={"MUNIC_RES": "municipality", "MUNIC_MOV": "destination"}
            )
        elif family == "ST":
            selected = data.loc[data.TP_UNID.eq("70")].copy()
            qc.update(
                selected_rows=len(selected),
                duplicate_cnes=int(selected.CNES.duplicated().sum()),
                multiple_municipalities_per_cnes=int(
                    selected.groupby("CNES").CODUFMUN.nunique().gt(1).sum()
                ),
            )
            result = selected.drop_duplicates(["CNES", "CODUFMUN"]).rename(
                columns={"CODUFMUN": "municipality"}
            )
        elif family == "LT":
            selected = data.loc[data.TP_UNID.eq("05") & data.CODLEITO.eq("87")].copy()
            qc.update(
                selected_rows=len(selected),
                duplicate_selected_rows=int(selected.duplicated().sum()),
                blank_beds=int(selected.QT_SUS.eq("").sum()),
            )
            selected["beds"] = pd.to_numeric(selected.QT_SUS, errors="raise")
            if not np.isfinite(selected.beds).all() or selected.beds.lt(0).any():
                raise ValueError("Invalid bed count")
            result = selected.rename(columns={"CODUFMUN": "municipality"})[
                ["municipality", "CNES", "beds"]
            ]
        else:
            selected = data.loc[data.CBO.eq("225133") & data.PROF_SUS.eq("1")].copy()
            hour_columns = ["HORA_AMB", "HORAHOSP", "HORAOUTR"]
            qc.update(
                selected_rows=len(selected),
                blank_hours=int(selected[hour_columns].eq("").sum().sum()),
            )
            for c in [
                "CNS_PROF",
                "CPF_PROF",
                "NOMEPROF",
                "VINCULAC",
                "VINCUL_C",
                "VINCUL_A",
                "VINCUL_N",
            ]:
                if c not in selected:
                    selected[c] = ""
            selected["person"] = selected.CNS_PROF.mask(selected.CNS_PROF.eq(""), selected.CPF_PROF)
            selected["person"] = selected.person.mask(selected.person.eq(""), selected.NOMEPROF)
            if selected.person.eq("").any():
                raise ValueError("Missing professional identity")
            hours = selected[hour_columns].replace("", "0").apply(pd.to_numeric, errors="raise")
            if not np.isfinite(hours).all().all() or hours.lt(0).any().any():
                raise ValueError("Invalid registered hours")
            selected["hours"] = hours.sum(axis=1)
            linkage = ["VINCULAC", "VINCUL_C", "VINCUL_A", "VINCUL_N"]
            key = ["CNES", "person", "CBO", "PROF_SUS", "hours", *linkage]
            exact_key = ["CNES", "CODUFMUN", "person", "CBO", "PROF_SUS", *hour_columns, *linkage]
            qc["locked_key_duplicates"] = int(selected.duplicated(key).sum())
            qc["exact_link_duplicates"] = int(selected.duplicated(exact_key).sum())
            qc["key_collision_requires_review"] = (
                qc["locked_key_duplicates"] != qc["exact_link_duplicates"]
            )
            selected = selected.drop_duplicates(exact_key)
            totals = selected.groupby("person").hours.sum()
            qc.update(
                unique_professionals=len(totals),
                multi_establishment_professionals=int(
                    selected.groupby("person").CNES.nunique().gt(1).sum()
                ),
                individual_hours_over_168=int(totals.gt(168).sum()),
                link_hours_over_168=int(selected.hours.gt(168).sum()),
                individual_hour_quantiles={
                    str(k): float(v)
                    for k, v in totals.quantile([0, 0.01, 0.05, 0.5, 0.95, 0.99, 1]).items()
                },
                total_registered_weekly_hours=float(selected.hours.sum()),
                cap_applied=False,
                sus_hours_interpretation=(
                    "Hours attached to SUS-linked registrations; "
                    "not independently verified SUS-exclusive time"
                ),
            )
            # Private cache retains person keys only for cross-UF plausibility QC; never exported.
            result = selected.rename(columns={"CODUFMUN": "municipality"})[
                ["municipality", "CNES", "person", "hours", *linkage]
            ]
        qc["municipalities"] = int(result.municipality.nunique())
    out.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(out, index=False)
    qc["output_sha256"] = acquisition.sha256(out)
    acquisition.write_json(qc_path, qc)
    return qc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--family", choices=["ST", "LT", "PF", "SIH", "population", "all"], default="all"
    )
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    AUDIT.mkdir(parents=True, exist_ok=True)
    items = [i for i in plan() if args.family in {"all", i["family"]}]
    acquisition.write_json(AUDIT / f"acquisition_plan_{args.family}.json", items)
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        for index, result in enumerate(executor.map(process, items), 1):
            print(
                f"{index}/{len(items)} {result['file']}: decoded and QC recorded; not published",
                flush=True,
            )


if __name__ == "__main__":
    main()
