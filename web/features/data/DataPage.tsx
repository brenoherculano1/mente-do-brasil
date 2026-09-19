import Link from "next/link";

const INDICATORS = [
  ["Suicídio", "Óbitos e taxa padronizada por idade", "2022 a 2024"],
  ["Internações psiquiátricas no SUS", "Contagem e taxa por 100 mil habitantes", "2022 a 2024"],
  ["CAPS", "Quantidade e taxa por 100 mil habitantes", "Dezembro de 2024"],
  ["Leitos SUS de saúde mental", "Quantidade e taxa por 100 mil habitantes", "Dezembro de 2024"],
  ["Psiquiatras no SUS", "Jornadas equivalentes e taxa por 100 mil habitantes", "Dezembro de 2024"],
] as const;

const SOURCES = [
  ["SIM", "Mortalidade por suicídio", "2022 a 2024, agrupado"],
  ["SIH/SUS", "Internações psiquiátricas", "2022 a 2024, agrupado"],
  ["CNES", "CAPS, leitos e jornadas equivalentes de psiquiatras", "Dezembro de 2024"],
  ["DATASUS", "População e associação entre municípios e Regiões de Saúde", "Referência 2024"],
  ["IBGE", "Malha municipal usada para composição territorial", "Malha Municipal Digital 2023"],
] as const;

export function DataPage() {
  return (
    <div className="data-shell page-shell">
      <section className="intro data-hero" aria-labelledby="data-title">
        <p className="eyebrow">Fontes e cobertura</p>
        <h1 id="data-title">De onde vêm os dados</h1>
        <p>
          O Mente do Brasil reúne fontes públicas nacionais e apresenta resultados
          para as 439 Regiões de Saúde, formadas pelos 5.570 municípios brasileiros.
        </p>
      </section>

      <main className="data-content">
        <section className="data-section" aria-labelledby="coverage-title">
          <p className="eyebrow">Cobertura atual</p>
          <h2 id="coverage-title">Dados validados até 2024</h2>
          <p>
            A versão atual combina eventos registrados entre 2022 e 2024 com a
            estrutura do SUS registrada em dezembro de 2024. Essa edição permanece preservada.
          </p>
          <div className="notice-inline">
            <strong>A disponibilidade varia por indicador.</strong> Cada fonte de 2025
            passa por sua própria validação, incluindo cobertura, denominadores e vínculo
            territorial. A estrutura pode ser atualizada independentemente da mortalidade.
            Indicadores compostos só são apresentados quando todos os seus componentes estão válidos.
          </div>
          <p>
            O SIM de 2025 ainda é uma prévia. Mortalidade consolidada, necessidade,
            diferença e análise espacial aguardam consolidação. Os valores regionais
            das outras fontes aguardam a validação do vínculo territorial de 2025 e de cada indicador.
          </p>
        </section>

        <section className="data-section" aria-labelledby="indicators-title">
          <p className="eyebrow">O que é medido</p>
          <h2 id="indicators-title">Indicadores e períodos</h2>
          <div className="table-wrap" tabIndex={0} role="region" aria-labelledby="indicators-title">
            <table>
              <thead><tr><th>Indicador</th><th>Valores apresentados</th><th>Período</th></tr></thead>
              <tbody>
                {INDICATORS.map(([indicator, values, period]) => (
                  <tr key={indicator}><th scope="row">{indicator}</th><td>{values}</td><td>{period}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="small-text">
            Jornadas equivalentes de psiquiatras são calculadas a partir da carga
            horária registrada. Elas não representam uma contagem de pessoas únicas.
          </p>
        </section>

        <section className="data-section" aria-labelledby="sources-title">
          <p className="eyebrow">Fontes públicas</p>
          <h2 id="sources-title">Bases utilizadas</h2>
          <div className="table-wrap" tabIndex={0} role="region" aria-labelledby="sources-title">
            <table>
              <thead><tr><th>Fonte</th><th>Uso</th><th>Período</th></tr></thead>
              <tbody>
                {SOURCES.map(([source, use, period]) => (
                  <tr key={source}><th scope="row">{source}</th><td>{use}</td><td>{period}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="data-section" aria-labelledby="geography-title">
          <p className="eyebrow">Território</p>
          <h2 id="geography-title">Todos os municípios estão identificados</h2>
          <p>
            Cada um dos 5.570 municípios está associado nominalmente à sua Região de
            Saúde. A busca do mapa aceita nomes de cidades, e cada perfil regional
            informa todos os municípios que compõem o território.
          </p>
          <p>
            Os indicadores continuam sendo calculados para a Região de Saúde. A lista
            municipal serve para localizar e compreender a composição da região, não
            para atribuir resultados regionais a uma cidade isolada.
          </p>
        </section>

        <section className="data-section methodology-cta" aria-labelledby="methodology-cta-title">
          <div><p className="eyebrow">Transparência</p><h2 id="methodology-cta-title">Como os indicadores são calculados</h2></div>
          <Link className="text-button" href="/metodologia">Ver metodologia completa →</Link>
        </section>
      </main>
    </div>
  );
}
