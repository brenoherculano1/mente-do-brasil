"""Structural data-quality checks for Mente do Brasil tables.

These checks intentionally validate structure and semantics only. They do not download,
recalculate, or alter scientific results.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable, Mapping, Sequence

from .constants import EXPECTED_HEALTH_REGION_COUNT, EXPECTED_MUNICIPALITY_COUNT, VALID_UFS


class MissingKind(StrEnum):
    NA = "NA"
    NOT_AVAILABLE = "not_available"
    NOT_APPLICABLE = "not_applicable"
    SUPPRESSED = "suppressed"


class QualityFlag(StrEnum):
    SMALL_SUICIDE_COUNT = "SMALL_SUICIDE_COUNT"
    EXTREME_PSYCHIATRIST_HOURS = "EXTREME_PSYCHIATRIST_HOURS"
    ZERO_REGISTERED_BEDS = "ZERO_REGISTERED_BEDS"
    SOURCE_INCOMPLETE = "SOURCE_INCOMPLETE"
    GEOGRAPHY_CROSSWALK_WARNING = "GEOGRAPHY_CROSSWALK_WARNING"
    PROVISIONAL_SOURCE = "PROVISIONAL_SOURCE"


@dataclass(frozen=True)
class ValidationIssue:
    rule: str
    message: str


def _is_missing(value: object) -> bool:
    return value is None or value in {kind.value for kind in MissingKind}


def _require(condition: bool, rule: str, message: str, issues: list[ValidationIssue]) -> None:
    if not condition:
        issues.append(ValidationIssue(rule=rule, message=message))


def validate_geography_crosswalk(
    rows: Sequence[Mapping[str, object]],
    *,
    expected_municipality_count: int = EXPECTED_MUNICIPALITY_COUNT,
    expected_health_region_count: int = EXPECTED_HEALTH_REGION_COUNT,
) -> list[ValidationIssue]:
    """Validate municipality-to-health-region crosswalk structure."""

    issues: list[ValidationIssue] = []
    municipality_codes = [row.get("municipality_code") for row in rows]
    region_codes = [row.get("health_region_code") for row in rows]
    ufs = [row.get("uf") for row in rows]

    _require(
        len(set(municipality_codes)) == expected_municipality_count,
        "municipality_count",
        f"Expected {expected_municipality_count} unique municipalities.",
        issues,
    )
    _require(
        len(set(region_codes)) == expected_health_region_count,
        "health_region_count",
        f"Expected {expected_health_region_count} unique health regions.",
        issues,
    )
    _require(
        len(municipality_codes) == len(set(municipality_codes)),
        "one_region_per_municipality",
        "Each municipality must appear exactly once in the crosswalk.",
        issues,
    )
    _require(
        all(not _is_missing(code) for code in region_codes),
        "health_region_code_not_null",
        "health_region_code cannot be null or semantic missing.",
        issues,
    )
    invalid_ufs = sorted({uf for uf in ufs if uf not in VALID_UFS})
    _require(
        not invalid_ufs,
        "valid_uf",
        f"Invalid UF values found: {invalid_ufs}",
        issues,
    )
    return issues


def validate_health_region_table(
    rows: Sequence[Mapping[str, object]],
    *,
    expected_health_region_count: int = EXPECTED_HEALTH_REGION_COUNT,
) -> list[ValidationIssue]:
    """Validate aggregate health-region metric table structure."""

    issues: list[ValidationIssue] = []
    region_codes = [row.get("health_region_code") for row in rows]
    duplicated = [code for code, n in Counter(region_codes).items() if n > 1]

    _require(
        len(region_codes) == expected_health_region_count,
        "health_region_row_count",
        f"Expected {expected_health_region_count} health-region rows.",
        issues,
    )
    _require(
        len(set(region_codes)) == len(region_codes) and not duplicated,
        "health_region_code_unique",
        f"health_region_code must be unique. Duplicates: {duplicated}",
        issues,
    )
    _require(
        all(not _is_missing(code) for code in region_codes),
        "health_region_code_not_null",
        "health_region_code cannot be null or semantic missing.",
        issues,
    )

    nonnegative_fields = [
        "population",
        "caps_count",
        "mental_health_beds_sus",
        "psychiatrist_fte",
    ]
    bounded_0_1_fields = [
        "suicide_asmr_percentile",
        "psychiatric_admission_rate_percentile",
        "caps_rate_percentile",
        "mental_health_beds_sus_rate_percentile",
        "psychiatrist_fte_rate_percentile",
        "need_score",
        "capacity_score",
    ]

    for row in rows:
        for field in nonnegative_fields:
            value = row.get(field)
            if not _is_missing(value):
                _require(float(value) >= 0, f"{field}_nonnegative", f"{field} cannot be negative.", issues)
        for field in bounded_0_1_fields:
            value = row.get(field)
            if not _is_missing(value):
                _require(0 <= float(value) <= 1, f"{field}_bounded", f"{field} must be in [0, 1].", issues)
        mismatch = row.get("mismatch_score")
        if not _is_missing(mismatch):
            _require(
                -1 <= float(mismatch) <= 1,
                "mismatch_score_bounded",
                "mismatch_score must be in [-1, 1].",
                issues,
            )
    return issues


def detect_silent_join_loss(
    left_keys: Iterable[object],
    joined_keys: Iterable[object],
    *,
    key_name: str,
) -> list[ValidationIssue]:
    """Detect keys lost after a join without treating missing as zero."""

    left = set(left_keys)
    joined = set(joined_keys)
    lost = sorted(left - joined)
    if lost:
        return [
            ValidationIssue(
                rule="no_silent_join_loss",
                message=f"{len(lost)} {key_name} values were lost during join: {lost[:10]}",
            )
        ]
    return []


def percentile_rank(values: Sequence[object]) -> list[float | str | None]:
    """Return percentile ranks in [0, 1], preserving semantic missing values."""

    observed = sorted(float(value) for value in values if not _is_missing(value))
    if not observed:
        return [value if _is_missing(value) else None for value in values]

    denom = max(len(observed) - 1, 1)
    ranks: list[float | str | None] = []
    for value in values:
        if _is_missing(value):
            ranks.append(value)  # preserve NA/not_available/not_applicable/suppressed
            continue
        less = sum(1 for observed_value in observed if observed_value < float(value))
        equal = sum(1 for observed_value in observed if observed_value == float(value))
        average_position = less + (equal - 1) / 2
        ranks.append(average_position / denom)
    return ranks
