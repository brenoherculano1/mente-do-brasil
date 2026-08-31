"""Deterministic descriptive additions for ManagerBrief and territorial report V2."""

from reportlab.platypus import PageBreak, Paragraph, Spacer, Table, TableStyle

from api.schemas.manager import InvestigationQuestion, ManagerBrief
from api.services.advanced import CHANGES, CURRENT, flows, timeline
from api.services.financing import get_financing


def enrich(db, brief: ManagerBrief) -> ManagerBrief:
    if brief.release.release_id != CURRENT:
        return brief
    code = brief.region.health_region_code
    temporal = timeline(db, code)
    change = db.row(
        'SELECT "values" FROM analytics.health_region_changes '
        "WHERE change_version=%s AND health_region_code=%s AND from_year=2022 AND to_year=2024",
        (CHANGES, code),
    )["values"]
    financing = get_financing(db, code=code).model_dump(mode="json")
    flow = flows(db, code, "origin", 8)
    extra = []
    rules = [
        (
            "CHANGE_NEED",
            "Change",
            change["NEED_POSITION_UP"] or change["NEED_COMPONENT_POSITION_UP"],
            "Essa mudança de posição relativa ocorreu nos dois componentes do Need ou ficou concentrada em um deles?",
        ),
        (
            "CHANGE_CAPACITY",
            "Change",
            change["CAPACITY_POSITION_DOWN"] or change["CAPACITY_COMPONENT_POSITION_DOWN"],
            "Quais componentes da capacidade registrada explicam a maior parte da mudança de posição relativa?",
        ),
        (
            "FINANCING_CONTEXT",
            "Financing",
            True,
            "Como o contexto geral de financiamento da saúde desta região se relaciona com a organização local da rede?",
        ),
        (
            "FLOW_OUTSIDE",
            "Flow",
            (flow["summary"]["outflow_share"] or 0) >= 0.20,
            "Quais referências assistenciais, serviços disponíveis ou pactuações regionais ajudam a explicar as internações de residentes realizadas fora da própria região?",
        ),
        (
            "FLOW_STATE",
            "Flow",
            (flow["summary"]["cross_state_outflow_share"] or 0) >= 0.10,
            "Que trajetórias de referência podem explicar internações de residentes realizadas em outro estado?",
        ),
    ]
    for index, (rule, category, matched, question) in enumerate(rules):
        if matched:
            extra.append(
                InvestigationQuestion(
                    rule_id=rule,
                    version="MDB_INVESTIGATION_GUIDE_2.0",
                    category=category,
                    question=question,
                    rationale="Contexto descritivo para a agenda de investigação.",
                    priority=25 + index,
                    claim_limit="Não constitui inferência causal, prescrição ou limiar clínico.",
                )
            )
    existing = [
        q.model_copy(update={"version": "MDB_INVESTIGATION_GUIDE_2.0"})
        for q in brief.investigation_questions
    ]
    questions = sorted([*existing, *extra], key=lambda q: (q.priority, q.rule_id))[:8]
    versions = brief.versions.model_copy(
        update={
            "manager_mode_version": "MDB_MANAGER_MODE_2.0",
            "manager_brief_version": "MDB_MANAGER_BRIEF_2.0",
            "investigation_guide_version": "MDB_INVESTIGATION_GUIDE_2.0",
            "report_version": "MDB_TERRITORIAL_REPORT_2.0",
        }
    )
    return brief.model_copy(
        update={
            "versions": versions,
            "temporal_summary": temporal,
            "change_summary": change,
            "financing_context": financing,
            "hospital_flow_summary": flow,
            "investigation_questions": questions,
            "method_references": ["SIM", "SIH/SUS", "CNES", "POPSVS", "SIOPS", CURRENT],
        }
    )


def add_sections(story, styles, brief):
    def paragraph(text):
        story.append(Paragraph(text, styles["body"]))

    def table(rows):
        result = Table(
            [[Paragraph(str(cell), styles["small"]) for cell in row] for row in rows],
            repeatRows=1,
            hAlign="LEFT",
        )
        result.setStyle(
            TableStyle(
                [("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]
            )
        )
        story.append(result)
        story.append(Spacer(1, 15))

    def number(value):
        return (
            "Indisponível"
            if value is None
            else f"{value:,.3f}".replace(",", "_").replace(".", ",").replace("_", ".")
        )

    story.append(Paragraph("Evolução territorial / O que mudou?", styles["h2"]))
    paragraph(
        "Need utiliza janelas móveis de três anos. Capacity utiliza registros de dezembro. São três pontos observados, sem suavização ou inferência causal."
    )
    table(
        [
            ["Âncora", "Need", "Capacity", "Mismatch", "Janela de Need"],
            *[
                [
                    r["year"],
                    number(r["need_score"]),
                    number(r["capacity_score"]),
                    number(r["mismatch_score"]),
                    f"{r['need_window_start']}-{r['need_window_end']}",
                ]
                for r in brief.temporal_summary["anchors"]
            ],
        ]
    )
    change = brief.change_summary
    paragraph(
        f"Entre 2022 e 2024: {change['matched_change_families']} famílias de mudança relativa atendidas."
    )
    paragraph(
        f"Delta Need: {number(change['delta_need_score'])}; Capacity: {number(change['delta_capacity_score'])}; Mismatch: {number(change['delta_mismatch_score'])}."
    )
    story.append(PageBreak())
    story.append(Paragraph("Contexto de financiamento da saúde", styles["h2"]))
    paragraph(
        "Esta medida descreve o financiamento geral da saúde e não corresponde a gasto específico em saúde mental."
    )
    table(
        [
            ["Ano", "Total em saúde (R$)", "R$/habitante", "Municípios"],
            *[
                [
                    r["year"],
                    number(r["total_health_expenditure_brl"]),
                    number(r["health_expenditure_per_capita_brl"]),
                    f"{r['municipalities_observed']}/{r['municipalities_expected']}",
                ]
                for r in brief.financing_context["records"]
            ],
        ]
    )
    paragraph(
        "Valores em reais correntes do respectivo exercício; comparações entre anos não representam variação real descontada da inflação. Dados parciais não são zero. SIOPS: PASS_WITH_LIMITATIONS."
    )
    story.append(PageBreak())
    story.append(Paragraph("Fluxos de internações psiquiátricas", styles["h2"]))
    paragraph(
        "Os dados representam internações/AIHs, não pacientes únicos. Janela 2022-2024. Origem: município de residência; destino: município do estabelecimento."
    )
    flow = brief.hospital_flow_summary
    s = flow["summary"]
    table(
        [
            ["Medida", "Valor"],
            ["AIHs de residentes", s["total_admissions"]],
            ["Proporção na própria região", number(s["within_region_share"])],
            ["Proporção fora da região", number(s["outflow_share"])],
            ["Proporção fora da UF", number(s["cross_state_outflow_share"])],
        ]
    )
    table(
        [
            ["Destino", "AIHs"],
            *[
                [
                    r["health_region_name"],
                    r["admissions"] if r["admissions"] is not None else "Indisponível (supressão)",
                ]
                for r in flow["connections"][:3]
            ],
        ]
    )
    paragraph(
        "Contribuições com menos de cinco internações não são divulgadas. Pares regionais com contribuições suprimidas não recebem totais exatos na tabela."
    )
