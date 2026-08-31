# Financing Field Ledger

Updated: 2026-08-31. Historical first gate preserved in commit `ead5ec6`.

Status: SOURCES_ACQUIRED_SCHEMA_INVENTORIED; AGGREGATION_RECONCILIATION_PENDING.

Source: SIOPS / Ministerio da Saude / Fundo Nacional de Saude.
Official [download catalog](https://portalfns.saude.gov.br/siops/siops-downloads/).
Original annual sixth-bimestre municipal ZIP URLs, redirects and hashes are in `metadata/provenance/phase3_source_manifest.csv`. No private mirror is authoritative.

## Observed columns

| Column | Observed meaning / treatment |
| --- | --- |
| Ano | Reporting exercise, 2022/2023/2024; four-digit text |
| Cod_IBGE | UF code in these files, not the municipal identifier |
| Estado | State name |
| Cod.Municipio (source header: Cód.Município) | Six-digit municipal IBGE code without check digit; preserve leading zeros |
| Municipio (source header: Município) | Municipality name |
| UF | Two-letter UF |
| Fonte | Funding-source category; nine distinct labels |
| Subfuncao | Functional subcategory; eight labels including Demais Subfuncoes |
| Codigo | Hierarchical expenditure-nature code, e.g. 3.0.00.00.00.00 |
| Descricao | Expenditure-nature label |
| Fase | Seven different budget/expenditure stages; never combine them |
| Valor | Decimal amount with dot and two fractional digits; parsed as exact integer cents |
| Data_Transmissao | Transmission timestamp |
| Data_Homologacao | Homologation timestamp |

Exact original column spellings, distinct values, row counts, missingness and CSV hashes are preserved in `metadata/provenance/phase3_siops_schema_inventory.json`. The files use UTF-8 BOM and semicolon delimiters. No stage has been approved as the product headline metric.

## Aggregation audit

Nature codes include parents and children. Adding all lines double counts. A diagnostic selects only `3.0.00.00.00.00` (current expenditures) and `4.0.00.00.00.00` (capital expenditures), separately by stage. This remains a candidate total until source/subfunction partitioning, intra-budget treatment and external reconciliation are proven. It is not a validated financing indicator.

The full 2024 inventory surfaced extreme source values, including BRL 382,587,171,024,568.00 in a liquidated root row for municipality 316620, and BRL 4,719,547,615,230.72 in a paid root row for 250760. Original rows are preserved. Do not cap, delete, impute or choose another stage merely to avoid these observations.

The official municipal indicator form was retrieved from `http://siops.datasus.gov.br/relindicadoresmun2.php?escmun=3`. The current API discovery attempt at `https://siops-consulta-publica-api.saude.gov.br/v2/api-docs` returned a connection reset. The HTML consultation remains reachable. National and selected-municipality numerical reconciliation were not completed because a separate temporal scientific hard stop was demonstrated; this is not evidence that SIOPS cannot be reconciled.

Municipal coverage is 5,567 / 5,568 / 5,567 in 2022 / 2023 / 2024. Missing municipalities are not zeros. The municipal files alone do not settle the separate DF treatment. No structural 439 x 3 financing dataset was released.

## Claim boundary

General public-health financing context only. Required product disclaimer, if subsequently implemented:

"Esta camada descreve o contexto geral de financiamento da saúde e não mede gasto específico em saúde mental."

RAPS_SPECIFIC_TRANSFER_LAYER = NOT_IMPLEMENTED_SOURCE_NOT_DEFENSIBLE. No RAPS-specific expenditure claim or automatic recommendation was added.
