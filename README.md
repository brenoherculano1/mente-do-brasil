# Mente do Brasil

**Inteligência territorial em saúde mental no Brasil.**

Mente do Brasil é um projeto de dados públicos que organiza indicadores de necessidade,
capacidade assistencial e desigualdade territorial nas 439 Regiões de Saúde brasileiras.
O produto combina uma camada analítica reproduzível, PostgreSQL/PostGIS, uma API FastAPI
somente leitura e uma aplicação Next.js orientada à exploração territorial.

> **Status: cloud preview / pre-release.** O código e os artefatos locais estão validados,
> mas o site ainda não constitui lançamento público oficial. `public_release_status` permanece
> `NOT_RELEASED`, sem domínio de produção e sem garantia de disponibilidade.

## Base científica

A unidade de análise é a Região de Saúde. A matriz Need × Capacity é uma tipologia ecológica
exploratória, não um ranking e não uma medida individual de acesso ou necessidade clínica.
O release analítico corrente é `MDB_ANALYTICAL_2024_2`, com método `MDB_METHOD_1.1` e
geografia `BR_HEALTH_REGIONS_END2024_V1`.

Resultados espaciais bloqueados:

- Moran global: `0.5256454566660947`;
- pseudo-p: `0.0001`;
- LISA significativo: `136` (`HH=60`, `LL=65`, `HL=5`, `LH=6`);
- `SMALL_SUICIDE_COUNT=7` e `ZERO_REGISTERED_BEDS=275`.

As definições, pressupostos, validações e limitações estão em
[`docs/methodology_page_2026-08-25.md`](docs/methodology_page_2026-08-25.md) e nos
metadados versionados.

## Fontes

Os indicadores derivados usam fontes oficiais do Ministério da Saúde/DATASUS (SIM,
SIH/SUS, CNES e POPSVS), SIOPS, referências populacionais do IBGE e a população-padrão
da OMS empregada na padronização por idade. Arquivos brutos, registros individuais,
backups e dumps não fazem parte do repositório público.

A geometria de exibição deriva da Malha Municipal Digital 2023 do IBGE, agregada para
Regiões de Saúde. A autorização técnica cobre somente a exibição derivada com atribuição;
a malha bruta e downloads de geometria permanecem excluídos.

## Open Data e API

`MDB_OPEN_DATA_2024_1` é o pacote imutável de agregados públicos. Seu ZIP possui
`914294` bytes e SHA-256
`2b3b1fc749bfd71181115c2cd9467bf26cb1572bd0c0e9687dabccffab3775bc`.
O contrato da API pública está em [`docs/api_v1_contract.md`](docs/api_v1_contract.md).
Durante o preview, os endpoints são técnicos e não representam um SLA de produção.

## Limitações

- Desenho ecológico: não permite inferência individual ou causal.
- Capacidade registrada não equivale automaticamente a acesso efetivo ou qualidade.
- Internações refletem uso do sistema e oferta, além de necessidade.
- Contagens pequenas e fluxos hospitalares recebem controles explícitos de divulgação.
- O preview gratuito pode ser pausado pelos provedores e não possui SLA.

## Execução local

```bash
uv sync --frozen --extra geo --extra dev
docker compose up -d
uv run python scripts/load_serving_database_release.py --release MDB_ANALYTICAL_2024_2
uv run python scripts/provision_api_db_role.py
uv run uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd web
npm ci
npm test
npm run dev
```

## Citação

Use [`CITATION.cff`](CITATION.cff) e a atribuição detalhada em
[`docs/open_data_attribution.md`](docs/open_data_attribution.md). Cite também as fontes
oficiais indicadas na documentação do release.

## Licenças

O código-fonte não é disponibilizado sob licença open source: **todos os direitos
reservados; nenhuma licença de uso do código é concedida**. A disponibilização pública
do repositório não concede direitos de reutilização do software, marca ou identidade.

A licença CC BY 4.0 aplica-se somente ao conteúdo derivado/licenciável identificado em
[`LICENSE_DATA.md`](web/public/releases/MDB_OPEN_DATA_2024_1/LICENSE_DATA.md), sujeita aos
direitos e termos das fontes terceiras.
Ela não se estende automaticamente ao código, à marca, às fontes brutas ou à geometria
fora do escopo expressamente documentado.
