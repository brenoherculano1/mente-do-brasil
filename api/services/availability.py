"""Source-year availability is independent of analytical release publication."""

from typing import Literal

from pydantic import BaseModel

Status = Literal["AVAILABLE", "UNAVAILABLE", "PROVISIONAL_NOT_PUBLIC", "UNDER_VALIDATION"]


class IndicatorAvailability(BaseModel):
    indicator_id: str
    label: str
    reference_year: int
    period: str
    status: Status
    source: str
    source_status: Status
    last_updated: str
    release_id: str | None
    available_publicly: bool
    reason_unavailable: str | None
    latest_available_year: int | None
    dependencies: list[str]


GEOGRAPHY_REASON = (
    "O vínculo dos municípios com as Regiões de Saúde em 2025 ainda está em validação. "
    "Os valores regionais serão apresentados após essa conferência e a validação da própria fonte."
)
SIM_REASON = (
    "Os dados consolidados de mortalidade por suicídio de 2025 ainda não estão disponíveis. "
    "A prévia do SIM não é usada nesta camada."
)
DEPENDENCY_REASON = (
    "Este indicador depende de dados consolidados de mortalidade por suicídio de 2025, "
    "ainda não disponíveis. Os componentes ausentes não são estimados nem substituídos."
)

# Population and territorial linkage apply to every regional rate. Spatial
# reproduction is deliberately NOT a dependency of deterministic capacity inputs.
DEFINITIONS = [
    ("caps_count", "CAPS registrados", "CNES", "2025-12", ["geography"]),
    (
        "caps_rate",
        "CAPS por 100 mil habitantes",
        "CNES; POPSVS",
        "2025-12",
        ["caps_count", "population"],
    ),
    ("beds_sus_count", "Leitos SUS de saúde mental", "CNES", "2025-12", ["geography"]),
    (
        "beds_sus_rate",
        "Leitos SUS por 100 mil habitantes",
        "CNES; POPSVS",
        "2025-12",
        ["beds_sus_count", "population"],
    ),
    (
        "psychiatrist_fte",
        "Jornadas equivalentes de psiquiatras",
        "CNES PF",
        "2025-12",
        ["geography", "workforce_qc"],
    ),
    (
        "psychiatrist_fte_rate",
        "Jornadas equivalentes por 100 mil habitantes",
        "CNES PF; POPSVS",
        "2025-12",
        ["psychiatrist_fte", "population"],
    ),
    (
        "psychiatric_admissions",
        "Internações psiquiátricas registradas",
        "SIH",
        "2025",
        ["geography", "sih_qc"],
    ),
    (
        "psychiatric_admissions_rate",
        "Internações por 100 mil habitantes",
        "SIH; POPSVS",
        "2025",
        ["psychiatric_admissions", "population"],
    ),
    (
        "pooled_psychiatric_admissions",
        "Internações no período agrupado",
        "SIH; POPSVS",
        "2023–2025",
        ["geography", "pooled_denominators", "sih_qc"],
    ),
    (
        "suicide_deaths",
        "Óbitos por suicídio",
        "SIM",
        "2023–2025",
        ["consolidated_sim", "geography"],
    ),
    (
        "suicide_asmr",
        "Mortalidade padronizada por suicídio",
        "SIM; POPSVS",
        "2023–2025",
        ["consolidated_sim", "population", "geography"],
    ),
    ("population", "População", "POPSVS", "2025", ["geography", "denominator_qc"]),
    (
        "financing",
        "Recursos gerais da saúde",
        "SIOPS",
        "2025",
        ["geography", "accounting_reconciliation"],
    ),
    (
        "need_score",
        "Necessidade em saúde mental",
        "SIM; SIH",
        "2023–2025",
        ["suicide_asmr", "pooled_psychiatric_admissions"],
    ),
    (
        "capacity_score",
        "Estrutura registrada",
        "CNES; POPSVS",
        "2025-12",
        ["caps_rate", "beds_sus_rate", "psychiatrist_fte_rate"],
    ),
    (
        "mismatch_score",
        "Diferença necessidade-capacidade",
        "SIM; SIH; CNES; POPSVS",
        "2023–2025 / 2025-12",
        ["need_score", "capacity_score"],
    ),
    (
        "moran",
        "Associação espacial global",
        "Análise espacial",
        "2025",
        ["mismatch_score", "spatial_reproduction"],
    ),
    (
        "lisa",
        "Associação espacial local",
        "Análise espacial",
        "2025",
        ["mismatch_score", "spatial_reproduction"],
    ),
    (
        "radar",
        "Conjunto completo de sinais",
        "SIM; SIH; CNES",
        "2025",
        ["need_score", "capacity_score", "mismatch_score", "lisa"],
    ),
    (
        "radar_capacity_signals",
        "Sinais de estrutura registrada",
        "CNES; POPSVS",
        "2025-12",
        ["capacity_score", "caps_rate", "beds_sus_rate", "psychiatrist_fte_rate"],
    ),
    ("hospital_flows", "Fluxos de internações", "SIH", "2025", ["geography", "sih_qc"]),
]


def availability_2025() -> list[IndicatorAvailability]:
    indicators = []
    for identifier, label, source, period, dependencies in DEFINITIONS:
        sim = identifier in {"suicide_deaths", "suicide_asmr"}
        dependent = identifier in {"need_score", "mismatch_score", "moran", "lisa", "radar"}
        reason = SIM_REASON if sim else DEPENDENCY_REASON if dependent else GEOGRAPHY_REASON
        if identifier == "financing":
            reason += (
                " Também falta reconciliar as contas e a cobertura do SIOPS, "
                "sem somar rubricas sobrepostas. Esta camada não mede gasto específico "
                "em saúde mental."
            )
        if identifier.startswith("psychiatrist_fte"):
            reason += " A carga horária e possíveis duplicações também estão em revisão."
        indicators.append(
            IndicatorAvailability(
                indicator_id=identifier,
                label=label,
                reference_year=2025,
                period=period,
                status="UNAVAILABLE" if sim or dependent else "UNDER_VALIDATION",
                source=source,
                source_status="PROVISIONAL_NOT_PUBLIC" if sim else "UNDER_VALIDATION",
                last_updated="2026-09-14",
                release_id=None,
                available_publicly=False,
                reason_unavailable=reason,
                latest_available_year=2024,
                dependencies=dependencies,
            )
        )
    return indicators


def unavailable_observations_2025():
    # No implicit fallback to an older release, interpolation, or null -> zero.
    return [{**item.model_dump(), "value": None} for item in availability_2025()]
