"use client";

import { useState } from "react";
import {
  METHOD_IDENTIFIERS,
  MANUSCRIPT_PUBLIC_STATUS,
  METHODOLOGY_LOCKS,
  METHODOLOGY_NAV,
  RATE_DENOMINATORS,
} from "@/lib/methodology";

const sourceRows = [
  ["Need", "Mortalidade por suicídio", "SIM", "2022-2024"],
  ["Need", "Internações psiquiátricas", "SIH/SUS", "2022-2024"],
  ["Capacity", "CAPS", "CNES", "Dez/2024"],
  ["Capacity", "Leitos de saúde mental SUS", "CNES", "Dez/2024"],
  ["Capacity", "Psiquiatras FTE SUS", "CNES", "Dez/2024"],
  ["Geografia/população", "Região de Saúde e denominadores", "DATASUS + IBGE", "referência 2024"],
];

export function MethodologyPage() {
  const [navOpen, setNavOpen] = useState(false);
  return (
    <div className="methodology-shell page-shell">
      <section className="intro methodology-hero" aria-labelledby="methodology-title">
        <p className="eyebrow">Como medimos</p>
        <h1 id="methodology-title">Metodologia</h1>
        <p>
          Como o Mente do Brasil transforma dados públicos de diferentes sistemas em
          indicadores comparáveis para as 439 Regiões de Saúde do país.
        </p>
        <div className="metadata-strip" aria-label="Identificadores metodológicos">
          <VersionPill label="Método" value={METHOD_IDENTIFIERS.method} />
          <VersionPill label="Release analítico" value={METHOD_IDENTIFIERS.release} />
          <VersionPill label="Geografia" value={METHOD_IDENTIFIERS.geography} />
        </div>
      </section>

      <div className="methodology-layout">
        <aside className="methodology-sidebar" aria-label="Índice da metodologia">
          <MethodologyNav />
        </aside>

        <div className="mobile-page-nav">
          <button
            className="text-button disclosure-button"
            type="button"
            aria-expanded={navOpen}
            aria-controls="mobile-methodology-nav"
            onClick={() => setNavOpen((current) => !current)}
          >
            Nesta página
          </button>
          {navOpen && (
            <div id="mobile-methodology-nav" className="mobile-page-nav-list">
              <MethodologyNav onNavigate={() => setNavOpen(false)} />
            </div>
          )}
        </div>

        <article className="methodology-content">
          <Section id="overview" eyebrow="Visão geral" title="Entenda em 1 minuto">
            <div className="method-flow" aria-label="Fluxo metodológico resumido">
              {[
                ["Dados públicos", "SIM + SIH/SUS + CNES + geografia"],
                ["439 Regiões de Saúde", "Unidade territorial do release"],
                ["Need", "2 itens"],
                ["Capacity", "3 itens"],
                ["Mismatch", "Need - Capacity"],
                ["Contexto espacial", "Moran + LISA"],
              ].map(([title, text], index) => (
                <div className="method-flow-step" key={title}>
                  <span>{index + 1}</span>
                  <strong>{title}</strong>
                  <p>{text}</p>
                </div>
              ))}
            </div>

            <div className="method-card-grid">
              <MethodCard
                title="Need"
                text="Posição relativa da região em dois indicadores de necessidade medida: mortalidade por suicídio e internações psiquiátricas registradas no SUS."
              />
              <MethodCard
                title="Capacity"
                text="Posição relativa da região em três componentes de capacidade pública registrada: CAPS, leitos SUS de saúde mental em hospital geral e psiquiatras FTE no SUS."
              />
              <div className="method-card">
                <h3>Mismatch</h3>
                <Formula>Mismatch = Need - Capacity</Formula>
                <p>
                  Um valor positivo indica que a posição relativa da região nos
                  indicadores de necessidade medida é superior à sua posição relativa
                  em capacidade registrada.
                </p>
                <p className="small-text">
                  Isso é um sinal territorial para investigação, e não uma medida
                  direta de déficit, acesso, qualidade ou necessidade não atendida.
                </p>
              </div>
            </div>
          </Section>

          <Section id="geography" title="Regiões de Saúde">
            <p>
              A unidade analítica do Mente do Brasil neste release é a Região de
              Saúde. O Brasil está representado por 439 Regiões de Saúde, formadas a
              partir da associação dos 5.570 municípios utilizados no denominador
              populacional de 2024.
            </p>
            <div className="method-card-grid compact">
              <MethodCard title="Região de Saúde" text="Unidade principal de análise." />
              <MethodCard
                title="Estado"
                text="Usado como contexto e agregação, não como unidade principal deste release."
              />
              <MethodCard
                title="Município"
                text="Usado para origem dos dados, composição territorial e identificação da Região de Saúde; não representa uma análise municipal completa nesta versão."
              />
            </div>
            <details className="method-details">
              <summary>Como a geografia foi construída</summary>
              <ul>
                <li>Crosswalk primário: DATASUS TAB_POP HR CNV.</li>
                <li>População de referência: DATASUS 2024.</li>
                <li>Geometria municipal compatível: IBGE.</li>
                <li>Dissolve por Região de Saúde, com CRS fonte EPSG:4674.</li>
                <li>Referência geográfica: configuração de fim de 2024.</li>
                <li>
                  O Distrito Federal foi tratado conforme o crosswalk travado de
                  município para Região de Saúde.
                </li>
              </ul>
              <p className="small-text">
                A referência de 31 de dezembro de 2024 é uma referência
                analítica/geográfica e não deve ser interpretada como a data literal
                em que cada arquivo oficial foi baixado.
              </p>
            </details>
          </Section>

          <Section id="sources" title="Fontes e períodos">
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Domínio</th>
                    <th>Indicador</th>
                    <th>Fonte</th>
                    <th>Período</th>
                  </tr>
                </thead>
                <tbody>
                  {sourceRows.map(([domain, indicator, source, period]) => (
                    <tr key={`${domain}-${indicator}`}>
                      <td>{domain}</td>
                      <td>{indicator}</td>
                      <td>{source}</td>
                      <td>{period}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="small-text">
              URLs históricas só são apresentadas quando preservadas no provenance.
              Para CNES, o provenance local preserva competência, sistema, arquivo e
              hash, mas não reconstrói URLs ausentes.
            </p>
          </Section>

          <Section id="need" title="Necessidade medida">
            <p>
              O Need Score combina dois indicadores distintos. Ele não representa
              prevalência de transtornos mentais nem pretende medir sozinho toda a
              necessidade de cuidado em saúde mental.
            </p>
            <TechnicalBlock
              title="Mortalidade por suicídio"
              rows={[
                ["Fonte", "SIM"],
                ["Período", METHODOLOGY_LOCKS.suicidePeriod],
                ["CID-10", "X60-X84"],
                ["Territorialização", "Município de residência -> Região de Saúde"],
                ["Medida", "Taxa de mortalidade padronizada por idade"],
                ["Transformação no índice", "Percentil nacional"],
                ["População padrão", METHODOLOGY_LOCKS.standardPopulationLabel],
              ]}
            />
            <details className="method-details">
              <summary>Detalhe técnico da mortalidade</summary>
              <p>
                A mortalidade foi agregada no período 2022-2024 e padronizada por
                idade pelo método direto, usando faixas etárias quinquenais com grupo
                terminal de 90 anos ou mais.
              </p>
            </details>

            <TechnicalBlock
              title="Internações psiquiátricas"
              rows={[
                ["Fonte", "SIH/SUS - registros de AIH"],
                ["Período", "2022-2024 pooled"],
                ["Diagnósticos incluídos", "F00-F09; F20-F99"],
                ["Excluídos", "F10-F19"],
                ["Territorialização", "MUNIC_RES / município de residência"],
                ["Unidade contada", "internações / AIHs"],
              ]}
            />
            <p>
              Uma internação não equivale a uma pessoa única. A mesma pessoa pode
              contribuir com mais de uma internação ao longo do período.
            </p>
            <p className="small-text">
              As internações são utilizadas como indicador relacionado à utilização e
              à carga observada no sistema. Elas não representam diretamente a
              prevalência de transtornos mentais.
            </p>
            <Formula>
              Need Score = (percentil de mortalidade por suicídio + percentil de
              internações psiquiátricas) / 2
            </Formula>
            <p className="small-text">
              Suicídio e internações possuem peso igual. O peso igual é uma decisão
              metodológica de composição do índice. Ele não significa que suicídio e
              internações representem parcelas iguais da necessidade real de saúde
              mental.
            </p>
          </Section>

          <Section id="capacity" title="Capacidade pública registrada">
            <p>
              Capacity descreve recursos registrados no setor público utilizados neste
              release. Capacidade registrada não equivale automaticamente a acesso
              efetivo, disponibilidade imediata, cobertura adequada ou qualidade
              assistencial.
            </p>
            <TechnicalBlock
              title="CAPS"
              rows={[
                ["Fonte", "CNES - dezembro de 2024"],
                ["Arquivo/tabela", "ST"],
                ["Filtro", "TP_UNID = 70"],
                ["Contagem", "CNES únicos"],
                ["Tipos", "sem ponderação por modalidade de CAPS neste Capacity Score"],
              ]}
            />
            <p className="small-text">
              CAPS de modalidades diferentes contribuem igualmente para esse
              componente do índice nesta metodologia.
            </p>
            <TechnicalBlock
              title="Leitos SUS de saúde mental em hospital geral"
              rows={[
                ["Fonte", "CNES - dezembro de 2024"],
                ["Arquivo/tabela", "LT"],
                ["Tipo de unidade", "TP_UNID = 05"],
                ["Código do leito", "CODLEITO = 87"],
                ["Quantidade", "QT_SUS"],
              ]}
            />
            <TechnicalBlock
              title="Psiquiatras FTE no SUS"
              rows={[
                ["CBO", "225133"],
                ["Vínculo SUS", "PROF_SUS = 1"],
                ["Horas", "HORA_AMB + HORAHOSP + HORAOUTR"],
                ["Conversão", "FTE = horas semanais registradas / 40"],
                ["Exemplo", "20 horas = 0,5 FTE; 40 horas = 1,0 FTE; 80 horas = 2,0 FTE"],
              ]}
            />
            <p>
              O número de psiquiatras é representado em equivalentes de tempo integral
              (FTE), com base nas horas semanais registradas no CNES.
            </p>
            <p className="small-text">
              FTE representa volume equivalente de carga horária e não necessariamente
              número de pessoas únicas. Foram removidos apenas vínculos exatamente
              duplicados. Não foi aplicado um teto arbitrário às horas registradas.
              Como o FTE depende das horas registradas no CNES, erros ou valores
              extremos de registro podem afetar a medida.
            </p>
            <Formula>
              Capacity Score = (percentil CAPS + percentil leitos + percentil
              psiquiatras FTE) / 3
            </Formula>
            <p className="small-text">
              CAPS, leitos e psiquiatras FTE possuem peso igual: um terço cada. Isso
              não é uma inferência clínica sobre igualdade de importância.
            </p>
          </Section>

          <Section id="percentiles" title="Por que usamos percentis?">
            <p>
              Os indicadores originais possuem escalas diferentes. CAPS, leitos,
              mortalidade e força de trabalho não podem ser combinados diretamente.
              Para colocá-los em uma escala comparável, cada indicador é transformado
              em sua posição relativa na distribuição nacional das 439 Regiões de
              Saúde.
            </p>
            <div className="percentile-scale" aria-label="Escala de percentis de 0 a 100">
              <span>0</span>
              <span>50</span>
              <span>100</span>
            </div>
            <p className="small-text">
              posição relativamente mais baixa <span aria-hidden="true">↔</span>{" "}
              posição relativamente mais alta
            </p>
            <p>
              Um percentil é uma medida de posição relativa. Ele não define se um
              valor é clinicamente adequado ou inadequado.
            </p>
            <ul>
              <li>Percentil 90 de CAPS não significa 90% de cobertura.</li>
              <li>Percentil 90 de Need não significa 90% de necessidade.</li>
            </ul>
            <details className="method-details">
              <summary>Detalhes do cálculo de percentis</summary>
              <p>{METHODOLOGY_LOCKS.percentileAlgorithm}</p>
              <p>{METHODOLOGY_LOCKS.percentileTies}</p>
              <p>{METHODOLOGY_LOCKS.percentileNullHandling}</p>
            </details>
          </Section>

          <Section id="mismatch" title="Mismatch">
            <Formula>Mismatch = Need Score - Capacity Score</Formula>
            <div className="method-card-grid compact">
              <MethodCard title="Mismatch > 0" text="Need ocupa posição relativa superior à Capacity." />
              <MethodCard title="Mismatch ≈ 0" text="Need e Capacity ocupam posições relativas semelhantes." />
              <MethodCard title="Mismatch < 0" text="Capacity ocupa posição relativa superior à Need." />
            </div>
            <div className="claim-box">
              <h3>O que Mismatch não significa</h3>
              <p>
                Mismatch não mede diretamente déficit assistencial, falta de
                atendimento, qualidade do cuidado, necessidade não atendida ou
                quantidade de recursos que deveria ser adicionada a um território.
              </p>
            </div>
            <p>
              Ele é um sinal de desalinhamento territorial relativo entre necessidade
              medida e capacidade registrada que pode justificar investigação
              adicional.
            </p>
          </Section>

          <Section id="spatial" title="Contexto espacial">
            <p>
              Regiões vizinhas podem apresentar padrões semelhantes. A análise
              espacial verifica se os valores de Mismatch apresentam estrutura
              geográfica além do que seria esperado por uma distribuição espacial
              aleatória.
            </p>
            <TechnicalBlock
              title="Global Moran's I"
              rows={[
                ["Variável", "Mismatch contínuo padronizado em z-score"],
                ["Vizinhança", "Queen contiguity"],
                ["Pesos", "row-standardized"],
                ["Ilhas", "0"],
                ["Permutações", METHODOLOGY_LOCKS.moranPermutations],
                ["Seed", METHODOLOGY_LOCKS.moranSeed],
                ["Moran's I", METHODOLOGY_LOCKS.moranI],
                ["pseudo-p", METHODOLOGY_LOCKS.moranPseudoP],
              ]}
            />
            <TechnicalBlock
              title="LISA"
              rows={[
                ["HH", "Mismatch relativamente alto cercado por valores relativamente altos."],
                ["LL", "Mismatch relativamente baixo cercado por valores relativamente baixos."],
                ["HL", "Mismatch relativamente alto cercado por valores relativamente baixos."],
                ["LH", "Mismatch relativamente baixo cercado por valores relativamente altos."],
                ["Significativas", String(METHODOLOGY_LOCKS.lisaSignificant)],
                ["HH / LL / HL / LH", "60 / 66 / 4 / 5"],
              ]}
            />
            <p className="small-text">
              Os clusters LISA referem-se ao Mismatch. Um cluster HH não deve ser
              interpretado como um hotspot de doença mental.
            </p>
          </Section>

          <Section id="quality" title="Observações de qualidade">
            <div className="method-card-grid compact">
              <div className="method-card">
                <h3>Pequeno número de óbitos por suicídio</h3>
                <p>
                  Pouco número de óbitos por suicídio no período agregado; a
                  estimativa deve ser interpretada com cautela.
                </p>
                <strong>{METHODOLOGY_LOCKS.smallSuicideCount} regiões</strong>
              </div>
              <div className="method-card">
                <h3>Zero leitos registrados</h3>
                <p>
                  Nenhum leito SUS deste tipo foi registrado na medida utilizada. Isso
                  não implica necessariamente ausência de acesso regional por
                  referência para outros territórios.
                </p>
                <strong>{METHODOLOGY_LOCKS.zeroRegisteredBeds} regiões</strong>
              </div>
            </div>
          </Section>

          <Section id="limitations" title="Limitações">
            <div className="limitation-list">
              {[
                [
                  "Estudo ecológico",
                  "Os indicadores representam territórios, não indivíduos. A posição de uma Região de Saúde não deve ser utilizada para inferir risco individual.",
                ],
                [
                  "Need é uma medida parcial",
                  "São utilizados dois proxies principais: mortalidade por suicídio e internações psiquiátricas. Eles não capturam toda a necessidade de cuidado em saúde mental.",
                ],
                [
                  "Internações refletem também o funcionamento do sistema",
                  "Internações podem ser influenciadas por disponibilidade de leitos, práticas de admissão, referência, transferências, reinternações e codificação. Portanto, internações não equivalem à prevalência de transtornos mentais.",
                ],
                [
                  "CNES mede estoque registrado",
                  "Um CAPS, leito ou profissional registrado não demonstra necessariamente acesso geográfico, funcionamento efetivo, disponibilidade imediata, capacidade operacional ou qualidade.",
                ],
                [
                  "FTE depende do registro de horas",
                  "Horas extremas ou incorretamente registradas podem afetar a medida.",
                ],
                [
                  "Não representa toda a capacidade em saúde mental",
                  "O núcleo atual utiliza determinados recursos públicos registrados e não representa uma descrição exaustiva de toda a RAPS nem do setor privado.",
                ],
                [
                  "Comparações são relativas",
                  "Need, Capacity e Mismatch dependem da distribuição nacional das 439 regiões. Uma posição relativa pode mudar mesmo quando o valor absoluto de uma região não muda, caso a distribuição nacional se altere.",
                ],
                [
                  "Mismatch não é causal",
                  "Os dados podem revelar padrões territoriais, mas não demonstram que um componente específico causou determinado desfecho nem indicam automaticamente qual recurso deveria ser adicionado a uma região.",
                ],
              ].map(([title, text]) => (
                <div className="limitation-item" key={title}>
                  <h3>{title}</h3>
                  <p>{text}</p>
                </div>
              ))}
            </div>
          </Section>

          <Section id="use" title="Como usar estes dados">
            <div className="use-grid">
              <div>
                <h3>Uso apropriado</h3>
                <ul>
                  <li>identificar padrões territoriais;</li>
                  <li>comparar posições relativas;</li>
                  <li>levantar hipóteses;</li>
                  <li>selecionar regiões para investigação;</li>
                  <li>contextualizar planejamento;</li>
                  <li>apoiar pesquisa;</li>
                  <li>documentar desigualdades;</li>
                  <li>gerar perguntas adicionais.</li>
                </ul>
              </div>
              <div>
                <h3>Uso inadequado</h3>
                <ul>
                  <li>diagnosticar indivíduos;</li>
                  <li>declarar prevalência;</li>
                  <li>produzir ranking moral de melhor e pior;</li>
                  <li>afirmar causalidade;</li>
                  <li>concluir automaticamente que uma região possui déficit;</li>
                  <li>prescrever alocação específica de recursos apenas com esses indicadores.</li>
                </ul>
              </div>
            </div>
          </Section>

          <Section id="versions" title="Versões">
            <p>
              Os resultados do Mente do Brasil são versionados. Alterações
              metodológicas ou correções relevantes não devem substituir
              silenciosamente releases anteriores.
            </p>
            <div className="version-grid">
              <VersionPill label="Método" value={METHOD_IDENTIFIERS.method} />
              <VersionPill label="Release analítico" value={METHOD_IDENTIFIERS.release} />
              <VersionPill label="Canonical" value={METHOD_IDENTIFIERS.canonical} />
              <VersionPill label="Geografia" value={METHOD_IDENTIFIERS.geography} />
              <VersionPill label="Geometria web" value={METHOD_IDENTIFIERS.webGeometry} />
            </div>
            <p className="small-text">Ver dados e versões: rota futura.</p>
          </Section>

          <Section id="reproducibility" title="Reprodutibilidade">
            <details className="method-details" open>
              <summary>Detalhes de reprodutibilidade</summary>
              <TechnicalRows
                rows={[
                  ["canonical", `${METHODOLOGY_LOCKS.canonicalRows} linhas`],
                  ["crosswalk", `${METHODOLOGY_LOCKS.crosswalkRows} linhas`],
                  ["LISA join", METHODOLOGY_LOCKS.lisaJoin],
                  ["provenance bruta", `${METHODOLOGY_LOCKS.rawProvenanceRecords} registros`],
                  ["canonical hash", "a3cc8f3aefc9d556d1bacc636dc72cabf04155052dd63c426dda9bec58ada515"],
                  ["crosswalk hash", "acd7ab896566d5ea730719eb46a079b0571d73fec617ef1d39db93099bd06b15"],
                  ["method version", METHOD_IDENTIFIERS.method],
                  ["geography version", METHOD_IDENTIFIERS.geography],
                  ["release ID", METHOD_IDENTIFIERS.release],
                  ["data access date", METHODOLOGY_LOCKS.sourceAccessDate],
                ]}
              />
            </details>
            <details className="method-details">
              <summary>Denominadores das taxas</summary>
              <TechnicalRows rows={RATE_DENOMINATORS.map((item) => [item.indicator, item.unit])} />
            </details>
          </Section>

          <Section id="scientific-base" title="Base científica">
            <p>
              A metodologia atual do Mente do Brasil deriva de uma infraestrutura
              analítica desenvolvida para estudar o desalinhamento espacial entre
              indicadores de necessidade de saúde mental e capacidade pública
              registrada nas Regiões de Saúde brasileiras.
            </p>
            <p className="small-text">
              {MANUSCRIPT_PUBLIC_STATUS.title}
              <br />
              {MANUSCRIPT_PUBLIC_STATUS.publicClaim}
            </p>
          </Section>

          <Section id="citation" title="Como citar">
            <p>
              A forma definitiva de citação será disponibilizada quando o primeiro
              release público for publicado.
            </p>
            <div className="version-grid">
              <VersionPill label="Release" value={METHOD_IDENTIFIERS.release} />
              <VersionPill label="Método" value={METHOD_IDENTIFIERS.method} />
            </div>
          </Section>
        </article>
      </div>
    </div>
  );
}

function MethodologyNav({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav aria-label="Seções da metodologia">
      {METHODOLOGY_NAV.map(([id, label]) => (
        <a href={`#${id}`} key={id} onClick={onNavigate}>
          {label}
        </a>
      ))}
    </nav>
  );
}

function Section({
  id,
  eyebrow,
  title,
  children,
}: {
  id: string;
  eyebrow?: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="method-section" id={id}>
      {eyebrow && <p className="eyebrow">{eyebrow}</p>}
      <h2>{title}</h2>
      {children}
    </section>
  );
}

function MethodCard({ title, text }: { title: string; text: string }) {
  return (
    <div className="method-card">
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  );
}

function Formula({ children }: { children: React.ReactNode }) {
  return <div className="formula-box">{children}</div>;
}

function VersionPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="version-pill">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function TechnicalBlock({ title, rows }: { title: string; rows: [string, string][] }) {
  return (
    <div className="technical-block">
      <h3>{title}</h3>
      <TechnicalRows rows={rows} />
    </div>
  );
}

function TechnicalRows({ rows }: { rows: [string, string][] }) {
  return (
    <dl className="technical-rows">
      {rows.map(([label, value]) => (
        <div key={`${label}-${value}`}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}
