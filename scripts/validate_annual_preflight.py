"""Fail-closed annual preparation check; does not publish or mutate a release."""

import argparse
import csv
import json
from pathlib import Path

REQUIRED = {"SIM", "SIH", "CNES", "POPSVS", "health-region crosswalk", "IBGE display geometry"}


def blockers(rows, reproduction):
    failures = []
    names = [r["SOURCE"] for r in rows]
    if len(names) != len(set(names)):
        failures.append("DUPLICATE_SOURCE_ROWS")
    for source in sorted(REQUIRED):
        records = [r for r in rows if r["SOURCE"] == source]
        if len(records) != 1:
            failures.append(f"MISSING_OR_DUPLICATE_SOURCE:{source}")
            continue
        row = records[0]
        if (
            row["COMPLETENESS"] != "COMPLETE_ENOUGH_FOR_OFFICIAL_RELEASE"
            or row["SCHEMA_COMPATIBLE"] != "YES"
            or row["OFFICIAL_RELEASE_READY"] != "YES"
        ):
            failures.append(f"SOURCE_NOT_VALIDATED:{source}")
    if (
        reproduction.get("status") != "PASS"
        or reproduction.get("byte_identical") is not True
        or reproduction.get("protected_changed") != []
    ):
        failures.append("2024_EXACT_REPRODUCTION_REQUIRED")
    return failures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--reproduction", type=Path, required=True)
    args = parser.parse_args()
    with args.matrix.open() as handle:
        rows = list(csv.DictReader(handle))
    failures = blockers(rows, json.loads(args.reproduction.read_text()))
    print(
        json.dumps(
            {
                "status": "BLOCKED_FOR_2025_OFFICIAL_RELEASE"
                if failures
                else "PREFLIGHT_ONLY_PASSED",
                "blockers": failures,
                "publication_authorized": False,
            },
            indent=2,
        )
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
