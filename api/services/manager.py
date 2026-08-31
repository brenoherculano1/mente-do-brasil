"""Manager Workbench composition and territorial PDF reports."""

from __future__ import annotations

import hashlib
import io
import json
import re
import unicodedata
from functools import lru_cache
from typing import Any

from fastapi import Response
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from api.db import Database
from api.errors import api_error
from api.schemas.common import Metric
from api.schemas.intelligence import (
    DECOMPOSITION_VERSION,
    INTELLIGENCE_VERSION,
    PEER_METHOD_VERSION,
    RADAR_RULESET_VERSION,
    DecompositionItem,
    PeerBenchmark,
    RadarSignals,
)
from api.schemas.manager import (
    INVESTIGATION_GUIDE_VERSION,
    MANAGER_BRIEF_VERSION,
    MANAGER_MODE_VERSION,
    REPORT_GENERATOR_VERSION,
    TERRITORIAL_REPORT_VERSION,
    CompareRegion,
    InvestigationQuestion,
    ManagerBrief,
    ManagerCompareResponse,
    ManagerMetricValue,
    ManagerPeerSummary,
    ManagerRegionIdentity,
    ManagerSpatialContext,
    ManagerVersions,
)
from api.services.health_regions import ensure_release_exists, release_from_row
from api.services.intelligence import (
    DECOMPOSITION_FIELDS,
    SUBSIGNAL_TEXT,
    TRIGGER_TEXT,
    peer_method_payload,
)

DISPLAY_METRICS = [
    Metric.need_score,
    Metric.capacity_score,
    Metric.mismatch_score,
    Metric.suicide_asmr,
    Metric.psychiatric_admission_rate,
    Metric.caps_rate,
    Metric.mental_health_beds_sus_rate,
    Metric.psychiatrist_fte_rate,
]

METRIC_LABELS = {
    Metric.need_score: ("Need", "score 0-1"),
    Metric.capacity_score: ("Capacity", "score 0-1"),
    Metric.mismatch_score: ("Mismatch", "score relativo"),
    Metric.suicide_asmr: ("Suicídio", "ASMR"),
    Metric.psychiatric_admission_rate: ("Internações psiquiátricas", "taxa"),
    Metric.caps_rate: ("CAPS", "taxa"),
    Metric.mental_health_beds_sus_rate: ("Leitos SUS", "taxa"),
    Metric.psychiatrist_fte_rate: ("Psiquiatras FTE", "taxa"),
}

INDICATOR_COLUMN_MAP = {
    Metric.need_score: ("need_score", None),
    Metric.capacity_score: ("capacity_score", None),
    Metric.mismatch_score: ("mismatch_score", None),
    Metric.suicide_asmr: ("suicide_asmr", "suicide_percentile"),
    Metric.psychiatric_admission_rate: (
        "psychiatric_admission_rate",
        "psychiatric_admission_percentile",
    ),
    Metric.caps_rate: ("caps_rate", "caps_percentile"),
    Metric.mental_health_beds_sus_rate: ("mental_health_beds_sus_rate", "beds_percentile"),
    Metric.psychiatrist_fte_rate: ("psychiatrist_fte_rate", "psychiatrist_fte_percentile"),
}

INVESTIGATION_RULES = [
    {
        "id": "BASE_LOCAL_CONFIRMATION",
        "condition": "always",
        "question": "Qual aspecto deste retrato territorial é confirmado pela experiência local?",
        "category": "Base",
        "rationale": "Toda leitura territorial exige confronto com conhecimento local.",
        "priority": 900,
    },
    {
        "id": "BASE_FLOWS_REGISTRY",
        "condition": "always",
        "question": (
            "Qual aspecto pode estar sendo influenciado por fluxo entre regiões, "
            "cadastro ou organização da rede?"
        ),
        "category": "Base",
        "rationale": "Indicadores regionais podem refletir organização territorial e registros.",
        "priority": 910,
    },
    {
        "id": "BASE_LOCAL_DATA",
        "condition": "always",
        "question": (
            "Quais dados locais seriam necessários para interpretar estes sinais "
            "com mais segurança?"
        ),
        "category": "Base",
        "rationale": "O produto organiza sinais públicos e não substitui investigação local.",
        "priority": 920,
    },
    {
        "id": "NEED_HIGH_COMPONENTS",
        "condition": "need_high",
        "question": (
            "Os dois componentes do Need estão em faixas relativamente altas ou o "
            "sinal está concentrado em apenas um deles?"
        ),
        "category": "Radar",
        "rationale": "NEED_HIGH foi acionado no Radar.",
        "priority": 100,
    },
    {
        "id": "NEED_HIGH_RECORDS",
        "condition": "need_high",
        "question": (
            "Esse padrão se mantém quando a equipe local compara os períodos e "
            "registros que originam os indicadores?"
        ),
        "category": "Radar",
        "rationale": "NEED_HIGH requer leitura cautelosa da origem dos registros.",
        "priority": 110,
    },
    {
        "id": "CAPACITY_LOW_COMPONENTS",
        "condition": "capacity_low",
        "question": (
            "Quais componentes da capacidade registrada estão mais distantes da "
            "posição relativa nacional?"
        ),
        "category": "Capacity",
        "rationale": "CAPACITY_LOW foi acionado no Radar.",
        "priority": 120,
    },
    {
        "id": "CAPACITY_LOW_ORGANIZATION",
        "condition": "capacity_low",
        "question": (
            "Existe organização regional, referência intermunicipal ou "
            "característica de cadastro que ajude a interpretar essa capacidade "
            "registrada?"
        ),
        "category": "Capacity",
        "rationale": "Capacidade registrada pode depender de organização regional.",
        "priority": 130,
    },
    {
        "id": "MISMATCH_POSITIVE_DECOMPOSITION",
        "condition": "mismatch_marked_positive",
        "question": (
            "O desalinhamento é formado principalmente por posições de Need acima "
            "do P50, Capacity abaixo do P50 ou pela combinação dos dois?"
        ),
        "category": "Radar",
        "rationale": "MISMATCH_MARKED_POSITIVE foi acionado e pode ser decomposto.",
        "priority": 140,
    },
    {
        "id": "CAPS_LOW_DISTRIBUTION",
        "condition": "caps_low",
        "question": "Como a oferta registrada de CAPS se distribui dentro da Região de Saúde?",
        "category": "Capacity",
        "rationale": "CAPS está em faixa relativamente baixa.",
        "priority": 150,
    },
    {
        "id": "BEDS_LOW_FLOWS",
        "condition": "beds_low",
        "question": (
            "Como a rede organiza internações de saúde mental em hospital geral "
            "dentro e fora da região?"
        ),
        "category": "Capacity",
        "rationale": "Leitos SUS estão em faixa relativamente baixa.",
        "priority": 160,
    },
    {
        "id": "ZERO_BEDS_REGISTRY",
        "condition": "zero_registered_beds",
        "question": (
            "Zero leitos registrados neste recorte reflete ausência de cadastro "
            "local, referenciamento para outras regiões ou outra organização "
            "assistencial?"
        ),
        "category": "Quality",
        "rationale": "O release registra zero leitos SUS de saúde mental.",
        "priority": 80,
    },
    {
        "id": "PSYCHIATRIST_FTE_LOW_DISTRIBUTION",
        "condition": "psychiatrist_fte_low",
        "question": (
            "Como a carga horária de psiquiatria registrada no SUS está "
            "distribuída entre os serviços e municípios da região?"
        ),
        "category": "Capacity",
        "rationale": "Psiquiatras FTE no SUS estão em faixa relativamente baixa.",
        "priority": 170,
    },
    {
        "id": "SPATIAL_HH_CONTEXT",
        "condition": "spatial_hh_mismatch",
        "question": (
            "Que fatores territoriais ou de organização regional podem ajudar a "
            "entender por que valores relativamente altos de Mismatch também "
            "aparecem em regiões vizinhas?"
        ),
        "category": "Spatial",
        "rationale": "SPATIAL_HH_MISMATCH foi acionado.",
        "priority": 180,
    },
    {
        "id": "SMALL_SUICIDE_COUNT_STABILITY",
        "condition": "small_suicide_count",
        "question": (
            "Esse componente é estável o suficiente para sustentar interpretações "
            "locais mais detalhadas?"
        ),
        "category": "Quality",
        "rationale": "SMALL_SUICIDE_COUNT exige cautela na leitura do componente de suicídio.",
        "priority": 90,
    },
]

CLAIM_LIMIT = (
    "Pergunta investigativa; não assume causalidade, insuficiência assistencial "
    "ou recomendação automática de recursos."
)


def get_manager_brief(db: Database, release_id: str, code: str) -> ManagerBrief:
    ensure_release_exists(db, release_id)
    row = manager_row(db, release_id, code)
    benchmarks = peer_benchmarks(db, release_id, code)
    brief_without_hash = build_manager_brief(row, benchmarks, report_content_sha256="")
    from api.services.manager_advanced import enrich

    brief_without_hash = enrich(db, brief_without_hash)
    content_hash = manager_brief_hash(brief_without_hash)
    return brief_without_hash.model_copy(update={"report_content_sha256": content_hash})


def compare_manager_regions(
    db: Database, release_id: str, codes: list[str]
) -> ManagerCompareResponse:
    ensure_release_exists(db, release_id)
    normalized = [code.strip() for code in codes if code.strip()]
    if len(normalized) < 2 or len(normalized) > 4:
        raise api_error(422, "INVALID_COMPARE_CODES", "Compare requires 2 to 4 region codes.")
    if any(not re.fullmatch(r"\d{5}", code) for code in normalized):
        raise api_error(422, "INVALID_COMPARE_CODES", "All region codes must have five digits.")
    if len(set(normalized)) != len(normalized):
        raise api_error(422, "DUPLICATE_COMPARE_CODES", "Compare does not accept duplicates.")
    regions = []
    release = None
    versions = None
    for code in normalized:
        row = manager_row(db, release_id, code)
        release = release_from_row(row)
        versions = manager_versions()
        regions.append(
            CompareRegion(
                identity=identity_from_row(row),
                need_score=row["need_score"],
                capacity_score=row["capacity_score"],
                mismatch_score=row["mismatch_score"],
                indicators=indicator_values(row),
                radar_signals=radar_signals_from_row(row),
                matched_signal_families=row["matched_signal_families"],
                quality_cautions=quality_cautions(row),
                lisa_context=spatial_context(row),
            )
        )
    return ManagerCompareResponse(
        release=release,
        versions=versions or manager_versions(),
        requested_codes=normalized,
        metric_options=DISPLAY_METRICS,
        regions=regions,
    )


def manager_row(db: Database, release_id: str, code: str) -> dict:
    row = db.row(
        """
        SELECT p.*, i.intelligence_version, i.radar_ruleset_version,
               i.decomposition_version, i.peer_method_version,
               i.need_high, i.capacity_low, i.mismatch_marked_positive,
               i.capacity_component_low, i.spatial_hh_mismatch, i.caps_low,
               i.beds_low, i.psychiatrist_fte_low, i.zero_registered_beds,
               i.matched_signal_families, i.suicide_contribution,
               i.admissions_contribution, i.caps_contribution, i.beds_contribution,
               i.psychiatrist_contribution, i.decomposition_sum
        FROM serving.health_region_profile p
        JOIN analytics.health_region_intelligence i
          ON i.release_id = p.release_id
         AND i.health_region_code = p.health_region_code
         AND i.intelligence_version = %s
        WHERE p.release_id = %s AND p.health_region_code = %s
        """,
        (
            "MDB_TERRITORIAL_INTELLIGENCE_1.1"
            if release_id == "MDB_ANALYTICAL_2024_2"
            else INTELLIGENCE_VERSION,
            release_id,
            code,
        ),
    )
    if not row:
        raise api_error(404, "HEALTH_REGION_NOT_FOUND", "Health Region not found.")
    return row


def build_manager_brief(
    row: dict, benchmarks: list[PeerBenchmark], report_content_sha256: str
) -> ManagerBrief:
    decomposition = decomposition_items(row)
    questions = investigation_questions(row)
    return ManagerBrief(
        release=release_from_row(row),
        versions=manager_versions(row),
        region=identity_from_row(row),
        need_score=row["need_score"],
        capacity_score=row["capacity_score"],
        mismatch_score=row["mismatch_score"],
        radar_signals=radar_signals_from_row(row),
        matched_signal_families=row["matched_signal_families"],
        radar_triggers=[text for key, text in TRIGGER_TEXT.items() if row[key]],
        radar_subsignals=[text for key, text in SUBSIGNAL_TEXT.items() if row[key]],
        deterministic_summary=manager_summary(row, decomposition),
        decomposition=decomposition,
        peer_summary=peer_summary(benchmarks),
        spatial_context=spatial_context(row),
        quality_cautions=quality_cautions(row),
        indicators=indicator_values(row),
        investigation_questions=questions,
        method_references=[
            "SIM",
            "SIH/SUS",
            "CNES",
            "IBGE/geografia",
            "MDB_ANALYTICAL_2024_1",
        ],
        report_content_sha256=report_content_sha256,
    )


def manager_versions(row: dict | None = None) -> ManagerVersions:
    return ManagerVersions(
        intelligence_version=(row or {}).get("intelligence_version", INTELLIGENCE_VERSION),
        radar_ruleset_version=(row or {}).get("radar_ruleset_version", RADAR_RULESET_VERSION),
        decomposition_version=(row or {}).get("decomposition_version", DECOMPOSITION_VERSION),
        peer_method_version=(row or {}).get("peer_method_version", PEER_METHOD_VERSION),
    )


def identity_from_row(row: dict) -> ManagerRegionIdentity:
    return ManagerRegionIdentity(
        health_region_code=row["health_region_code"],
        health_region_name=row["health_region_name"],
        uf=row["uf"],
        population=row["population"],
        municipality_count=row["municipality_count"],
    )


def radar_signals_from_row(row: dict) -> RadarSignals:
    return RadarSignals(
        need_high=row["need_high"],
        capacity_low=row["capacity_low"],
        mismatch_marked_positive=row["mismatch_marked_positive"],
        capacity_component_low=row["capacity_component_low"],
        spatial_hh_mismatch=row["spatial_hh_mismatch"],
        caps_low=row["caps_low"],
        beds_low=row["beds_low"],
        psychiatrist_fte_low=row["psychiatrist_fte_low"],
        zero_registered_beds=row["zero_registered_beds"],
        matched_signal_families=row["matched_signal_families"],
    )


def decomposition_items(row: dict) -> list[DecompositionItem]:
    items = []
    for contribution_field, label, percentile_field in DECOMPOSITION_FIELDS:
        caution = None
        if (
            contribution_field == "suicide_contribution"
            and "SMALL_SUICIDE_COUNT" in row["data_quality_flags"]
        ):
            caution = "Pouco número de óbitos no período agregado; interprete com cautela."
        items.append(
            DecompositionItem(
                component=contribution_field.replace("_contribution", ""),
                label=label,
                source_percentile=row[percentile_field],
                contribution=row[contribution_field],
                caution=caution,
            )
        )
    return items


def indicator_values(row: dict) -> list[ManagerMetricValue]:
    values = []
    for metric in DISPLAY_METRICS:
        value_column, percentile_column = INDICATOR_COLUMN_MAP[metric]
        label, unit = METRIC_LABELS[metric]
        values.append(
            ManagerMetricValue(
                metric_id=metric,
                label=label,
                value=row[value_column],
                percentile=row[percentile_column] if percentile_column else None,
                unit=unit,
            )
        )
    return values


def peer_benchmarks(db: Database, release_id: str, code: str) -> list[PeerBenchmark]:
    rows = db.rows(
        """
        SELECT metric_id, target_value, peer_n_observed, peer_median, peer_q1, peer_q3,
               peer_min, peer_max, relative_to_peer_iqr, insufficient_reason
        FROM analytics.health_region_peer_benchmarks
        WHERE release_id = %s
          AND peer_method_version = %s
          AND health_region_code = %s
          AND metric_id IN ('mismatch_score', 'need_score', 'capacity_score')
        ORDER BY CASE metric_id
          WHEN 'mismatch_score' THEN 1
          WHEN 'need_score' THEN 2
          WHEN 'capacity_score' THEN 3
          ELSE 4
        END
        """,
        (release_id, PEER_METHOD_VERSION, code),
    )
    return [PeerBenchmark(**row) for row in rows]


def peer_summary(benchmarks: list[PeerBenchmark]) -> ManagerPeerSummary:
    return ManagerPeerSummary(
        method_version=PEER_METHOD_VERSION,
        peer_count=10,
        default_metric=Metric.mismatch_score,
        selected_benchmarks=benchmarks,
    )


def spatial_context(row: dict) -> ManagerSpatialContext:
    cluster = row["lisa_cluster"] if row["lisa_significant"] else None
    if row["spatial_hh_mismatch"]:
        description = (
            "Mismatch relativamente alto em contexto local de valores também altos; "
            "interpretação espacial descritiva."
        )
    elif cluster:
        description = f"LISA significativo: {cluster}."
    else:
        description = "Sem LISA significativo neste release."
    return ManagerSpatialContext(
        lisa_significant=row["lisa_significant"],
        lisa_cluster=cluster,
        lisa_local_i=row["lisa_local_i"],
        lisa_p=row["lisa_p"],
        description=description,
    )


def quality_cautions(row: dict) -> list[str]:
    cautions = []
    flags = set(row["data_quality_flags"])
    if "SMALL_SUICIDE_COUNT" in flags:
        cautions.append(
            "O pequeno número de óbitos no período agregado exige cautela na "
            "interpretação do componente de mortalidade por suicídio."
        )
    if row["zero_registered_beds"]:
        cautions.append(
            "Zero leitos registrados neste recorte deve ser interpretado junto à "
            "organização regional, referências intermunicipais e cadastro."
        )
    return cautions


def investigation_questions(row: dict) -> list[InvestigationQuestion]:
    conditions = {
        "always": True,
        "need_high": row["need_high"],
        "capacity_low": row["capacity_low"],
        "mismatch_marked_positive": row["mismatch_marked_positive"],
        "caps_low": row["caps_low"],
        "beds_low": row["beds_low"],
        "zero_registered_beds": row["zero_registered_beds"],
        "psychiatrist_fte_low": row["psychiatrist_fte_low"],
        "spatial_hh_mismatch": row["spatial_hh_mismatch"],
        "small_suicide_count": "SMALL_SUICIDE_COUNT" in row["data_quality_flags"],
    }
    selected = [
        rule for rule in INVESTIGATION_RULES if conditions.get(str(rule["condition"]), False)
    ]
    selected.sort(key=lambda rule: (int(rule["priority"]), str(rule["id"])))
    return [
        InvestigationQuestion(
            rule_id=str(rule["id"]),
            category=rule["category"],
            question=str(rule["question"]),
            rationale=str(rule["rationale"]),
            priority=int(rule["priority"]),
            claim_limit=CLAIM_LIMIT,
        )
        for rule in selected[:8]
    ]


def manager_summary(row: dict, decomposition: list[DecompositionItem]) -> str:
    ordered = sorted(
        decomposition,
        key=lambda item: (
            -abs(item.contribution),
            ["suicide", "admissions", "caps", "beds", "psychiatrist"].index(item.component),
        ),
    )
    top = " e ".join(item.label for item in ordered[:2])
    families = row["matched_signal_families"]
    if families == 0:
        opening = "Nenhum dos cinco critérios predefinidos do Radar foi acionado neste release."
    else:
        opening = f"A região aciona {families} das 5 famílias de sinais do Radar."
    return (
        f"{opening} O Mismatch é {format_signed(row['mismatch_score'])}. "
        f"As maiores contribuições algébricas vêm de {top}. "
        "A leitura funciona como sinal para investigação territorial, sem prescrição automática."
    )


def manager_brief_hash(brief: ManagerBrief) -> str:
    payload = brief.model_dump(mode="json")
    payload["report_content_sha256"] = ""
    encoded = json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def manager_methods_payload() -> dict[str, Any]:
    return {
        "manager_mode_version": MANAGER_MODE_VERSION,
        "report_version": TERRITORIAL_REPORT_VERSION,
        "investigation_guide_version": INVESTIGATION_GUIDE_VERSION,
        "manager_brief_version": MANAGER_BRIEF_VERSION,
        "scope": "Camada de composição descritiva sobre releases locked.",
        "no_new_scientific_model": True,
        "no_ranking": True,
        "no_resource_recommendation": True,
        "questions": {
            "count": len(INVESTIGATION_RULES),
            "max_display": 8,
            "deterministic": True,
        },
        "peers": peer_method_payload(),
    }


def generate_report_pdf(brief: ManagerBrief) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.35 * cm,
        leftMargin=1.35 * cm,
        topMargin=1.45 * cm,
        bottomMargin=1.55 * cm,
        title=f"Relatório Territorial - {brief.region.health_region_code}",
        author="Mente do Brasil",
    )
    styles = report_styles()
    story: list[Any] = []
    add_cover(story, styles, brief)
    story.append(PageBreak())
    add_attention(story, styles, brief)
    story.append(PageBreak())
    add_indicators(story, styles, brief)
    story.append(PageBreak())
    add_peers_spatial(story, styles, brief)
    story.append(PageBreak())
    if brief.temporal_summary is not None:
        from api.services.manager_advanced import add_sections

        add_sections(story, styles, brief)
        story.append(PageBreak())
    add_questions(story, styles, brief)
    doc.build(story, onFirstPage=footer(brief), onLaterPages=footer(brief))
    return buffer.getvalue()


@lru_cache(maxsize=512)
def cached_report_pdf(cache_key: str, brief_json: str) -> bytes:
    brief = ManagerBrief.model_validate_json(brief_json)
    return generate_report_pdf(brief)


def report_response(brief: ManagerBrief) -> Response:
    brief_json = brief.model_dump_json()
    cache_key = ":".join(
        [
            brief.release.release_id,
            brief.region.health_region_code,
            brief.versions.report_version,
            brief.report_content_sha256,
        ]
    )
    pdf = cached_report_pdf(cache_key, brief_json)
    filename = report_filename(brief)
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Cache-Control": "public, max-age=60, s-maxage=900, stale-while-revalidate=3600",
        "ETag": f'"{brief.report_content_sha256[:32]}-{REPORT_GENERATOR_VERSION}"',
        "X-Robots-Tag": "noindex",
    }
    return Response(content=pdf, media_type="application/pdf", headers=headers)


def report_filename(brief: ManagerBrief) -> str:
    slug = unicodedata.normalize("NFKD", brief.region.health_region_name)
    slug = slug.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")[:60]
    return (
        f"mente-do-brasil_relatorio_{brief.region.health_region_code}_{slug}_"
        f"{brief.release.release_id}.pdf"
    )


def report_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#1f302d"),
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#243632"),
            spaceBefore=8,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=12.2,
            textColor=colors.HexColor("#243632"),
        ),
        "small": ParagraphStyle(
            "small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=colors.HexColor("#50635f"),
        ),
    }


def add_cover(story: list[Any], styles: dict[str, ParagraphStyle], brief: ManagerBrief) -> None:
    story.append(Paragraph("Relatório Territorial", styles["title"]))
    story.append(Paragraph(brief.region.health_region_name, styles["h2"]))
    story.append(
        Paragraph(f"{brief.region.uf} · código {brief.region.health_region_code}", styles["body"])
    )
    story.append(Spacer(1, 0.35 * cm))
    story.append(Paragraph("Inteligência territorial em saúde mental no Brasil.", styles["body"]))
    rows = [
        ["População", format_int(brief.region.population)],
        ["Municípios", str(brief.region.municipality_count)],
        ["Release analítico", brief.release.release_id],
        ["Intelligence version", brief.versions.intelligence_version],
        ["Need", format_num(brief.need_score)],
        ["Capacity", format_num(brief.capacity_score)],
        ["Mismatch", format_signed(brief.mismatch_score)],
        ["Radar", f"{brief.matched_signal_families}/5 famílias"],
    ]
    story.append(simple_table(rows))
    story.append(Spacer(1, 0.25 * cm))
    story.append(
        Paragraph(
            "Sinal de desalinhamento territorial relativo entre necessidade medida "
            "e capacidade registrada.",
            styles["body"],
        )
    )


def add_attention(story: list[Any], styles: dict[str, ParagraphStyle], brief: ManagerBrief) -> None:
    story.append(Paragraph("Por que chamou atenção", styles["h2"]))
    story.append(Paragraph(brief.deterministic_summary, styles["body"]))
    if brief.radar_triggers:
        story.append(simple_table([["Radar", item] for item in brief.radar_triggers]))
    if brief.radar_subsignals:
        story.append(simple_table([["Sub-sinal", item] for item in brief.radar_subsignals]))
    if brief.quality_cautions:
        story.append(Paragraph("Cautelas", styles["h2"]))
        for caution in brief.quality_cautions:
            story.append(Paragraph(caution, styles["small"]))
    story.append(Paragraph("Decomposição do Mismatch", styles["h2"]))
    rows = [
        [item.label, percentile(item.source_percentile), format_signed(item.contribution)]
        for item in brief.decomposition
    ]
    story.append(simple_table([["Componente", "Percentil", "Contribuição algébrica"], *rows]))


def add_indicators(
    story: list[Any], styles: dict[str, ParagraphStyle], brief: ManagerBrief
) -> None:
    story.append(Paragraph("Need e Capacity", styles["h2"]))
    rows = [["Indicador", "Valor", "Percentil"]]
    for item in brief.indicators:
        if item.metric_id in {Metric.need_score, Metric.capacity_score, Metric.mismatch_score}:
            continue
        rows.append([item.label, format_num(item.value), percentile(item.percentile)])
    story.append(simple_table(rows))
    story.append(
        Paragraph(
            "Os indicadores são públicos e organizados para investigação territorial. "
            "Não constituem inferência clínica.",
            styles["small"],
        )
    )


def add_peers_spatial(
    story: list[Any], styles: dict[str, ParagraphStyle], brief: ManagerBrief
) -> None:
    story.append(Paragraph("Peers estruturais e contexto espacial", styles["h2"]))
    story.append(
        Paragraph(
            "Comparação com 10 Regiões de Saúde estruturalmente semelhantes segundo "
            "população, densidade populacional e número de municípios.",
            styles["body"],
        )
    )
    story.append(
        simple_table(
            [["Método de peers", brief.peer_summary.method_version], ["Métrica padrão", "Mismatch"]]
        )
    )
    if brief.peer_summary.selected_benchmarks:
        rows = [["Métrica", "Região", "Mediana dos peers", "IQR dos peers"]]
        for benchmark in brief.peer_summary.selected_benchmarks:
            label, _unit = METRIC_LABELS.get(benchmark.metric_id, (str(benchmark.metric_id), ""))
            rows.append(
                [
                    label,
                    format_num(benchmark.target_value),
                    format_num(benchmark.peer_median),
                    f"{format_num(benchmark.peer_q1)} - {format_num(benchmark.peer_q3)}",
                ]
            )
        story.append(Spacer(1, 0.18 * cm))
        story.append(compact_table(rows, [4.1 * cm, 3.2 * cm, 4.1 * cm, 4.8 * cm]))
    story.append(Paragraph("Contexto espacial", styles["h2"]))
    story.append(Paragraph(brief.spatial_context.description, styles["body"]))


def add_questions(story: list[Any], styles: dict[str, ParagraphStyle], brief: ManagerBrief) -> None:
    story.append(Paragraph("Perguntas para investigação", styles["h2"]))
    for index, question in enumerate(brief.investigation_questions, start=1):
        story.append(Paragraph(f"{index}. {question.question}", styles["body"]))
        story.append(
            Paragraph(f"Origem: {question.category}. {question.rationale}", styles["small"])
        )
    story.append(Paragraph("Limitações e leitura correta", styles["h2"]))
    story.append(
        Paragraph(
            "Este relatório organiza indicadores públicos e sinais territoriais para "
            "apoiar investigação. Não constitui avaliação direta de acesso, "
            "qualidade, necessidade não atendida ou recomendação automática de "
            "recursos.",
            styles["body"],
        )
    )
    story.append(Paragraph("Fontes e versões", styles["h2"]))
    story.append(
        Paragraph(
            "Fontes: SIM; SIH/SUS; CNES; IBGE/geografia. "
            f"{brief.release.release_id}; {brief.versions.report_version}; "
            f"{brief.versions.investigation_guide_version}; conteúdo {brief.report_content_sha256}.",
            styles["small"],
        )
    )
    story.append(
        Paragraph(
            "Citação sugerida: Mente do Brasil. Relatório Territorial — "
            f"{brief.region.health_region_name}. Release {brief.release.release_id}. "
            f"{brief.versions.report_version}.",
            styles["small"],
        )
    )


def simple_table(rows: list[list[Any]]) -> Table:
    table = Table(rows, hAlign="LEFT", colWidths=[5.2 * cm, 11.0 * cm])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.2),
                ("LEADING", (0, 0), (-1, -1), 10.5),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#243632")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef1ed")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#c9d1cc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def compact_table(rows: list[list[Any]], col_widths: list[float]) -> Table:
    table = Table(rows, hAlign="LEFT", colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.8),
                ("LEADING", (0, 0), (-1, -1), 9.6),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#243632")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef1ed")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#c9d1cc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def footer(brief: ManagerBrief):
    def draw(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#50635f"))
        max_pages = 8 if brief.temporal_summary else 5
        text = (
            f"Mente do Brasil · {brief.release.release_id} · "
            f"{brief.versions.report_version} · página {doc.page}/{max_pages}"
        )
        canvas.drawString(1.35 * cm, 0.75 * cm, text)
        canvas.restoreState()

    return draw


def format_num(value: float | int | None) -> str:
    if value is None:
        return "Não disponível"
    return f"{float(value):.2f}".replace(".", ",")


def format_signed(value: float | int | None) -> str:
    if value is None:
        return "Não disponível"
    number = float(value)
    sign = "+" if number > 0 else ""
    return f"{sign}{number:.2f}".replace(".", ",")


def format_int(value: int | None) -> str:
    if value is None:
        return "Não disponível"
    return f"{value:,}".replace(",", ".")


def percentile(value: float | None) -> str:
    if value is None:
        return "Não disponível"
    return f"P{round(value * 100)}"


def approximate_text_width(text: str, font_size: float = 8.2) -> float:
    return stringWidth(text, "Helvetica", font_size)
