import Link from "next/link";
import {
  ABOUT_ACTIONS,
  ABOUT_AUDIENCES,
  ABOUT_FLOW,
  ABOUT_NOT_LIST,
  ABOUT_PAGE,
  ABOUT_PRINCIPLES,
} from "@/lib/about-page";

export function AboutPage() {
  return (
    <div className="about-shell page-shell">
      <section className="intro about-hero" aria-labelledby="about-title">
        <p className="eyebrow">Sobre</p>
        <h1 id="about-title">Sobre o Mente do Brasil</h1>
        <p>{ABOUT_PAGE.heroDescription}</p>
        <div className="metadata-strip" aria-label="Identificação do projeto">
          <VersionTag label="Nome oficial" value="MENTE DO BRASIL" />
          <VersionTag label="Subtítulo" value={ABOUT_PAGE.subtitle} />
          <VersionTag label="Release" value={ABOUT_PAGE.versions.releaseId} />
        </div>
      </section>

      <main className="about-content">
        <section className="about-section" aria-labelledby="what-title">
          <p className="eyebrow">Definição</p>
          <h2 id="what-title">O que é o Mente do Brasil</h2>
          <p>{ABOUT_PAGE.positioning}</p>
          <p>
            O Mente do Brasil organiza dados públicos de diferentes sistemas nacionais
            e os transforma em uma estrutura territorial comparável, versionada e
            documentada.
          </p>
          <p>
            A unidade principal de análise do release atual é a Região de Saúde. Isso
            permite observar como indicadores de necessidade medida e capacidade
            pública registrada se distribuem entre diferentes partes do país sem
            reduzir a análise a limites municipais isolados.
          </p>
          <p>
            O objetivo é tornar dados fragmentados mais úteis para investigação,
            planejamento, pesquisa e compreensão territorial. O mapa é uma das formas
            de explorar essa infraestrutura.
          </p>
        </section>

        <section className="about-section" aria-labelledby="why-title">
          <p className="eyebrow">Problema</p>
          <h2 id="why-title">Por que isso existe</h2>
          <p>
            O Brasil produz grandes volumes de dados públicos em saúde. O problema é
            que disponibilidade não significa, por si só, facilidade de uso.
          </p>
          <p>
            Informações relevantes podem estar distribuídas entre diferentes sistemas,
            períodos, arquivos e estruturas territoriais. Compará-las de forma
            responsável exige decisões sobre geografia, denominadores, definições,
            qualidade, metodologia e versionamento.
          </p>
          <p>
            O Mente do Brasil foi construído para concentrar esse trabalho em uma
            infraestrutura auditável.
          </p>
          <ol className="about-flow" aria-label="Fluxo de transformação dos dados públicos">
            {ABOUT_FLOW.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </section>

        <section className="about-section" aria-labelledby="actions-title">
          <p className="eyebrow">Trabalho</p>
          <h2 id="actions-title">O que fazemos</h2>
          <div className="about-card-grid">
            {ABOUT_ACTIONS.map(([title, text]) => (
              <article className="about-card" key={title}>
                <h3>{title}</h3>
                <p>{text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="about-section" aria-labelledby="audiences-title">
          <p className="eyebrow">Uso público</p>
          <h2 id="audiences-title">Para quem foi construído</h2>
          <p>
            A infraestrutura foi construída para apoiar investigação territorial e
            leitura técnica por diferentes públicos que trabalham com saúde pública.
          </p>
          <ul className="about-list-grid">
            {ABOUT_AUDIENCES.map((audience) => (
              <li key={audience}>{audience}</li>
            ))}
          </ul>
          <p className="small-text">{ABOUT_PAGE.patientDisclaimer}</p>
        </section>

        <section className="about-section" aria-labelledby="principles-title">
          <p className="eyebrow">Como trabalhamos</p>
          <h2 id="principles-title">Princípios do projeto</h2>
          <div className="about-card-grid principles-grid">
            {ABOUT_PRINCIPLES.map(([title, text]) => (
              <article className="about-card" key={title}>
                <h3>{title}</h3>
                <p>{text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="about-section" aria-labelledby="scope-title">
          <p className="eyebrow">Release atual</p>
          <h2 id="scope-title">Escopo atual</h2>
          <p>Região de Saúde é a unidade principal de análise deste release.</p>
          <div className="about-scope-grid">
            <ScopeStat value={String(ABOUT_PAGE.scope.healthRegions)} label="Regiões de Saúde" />
            <ScopeStat
              value="5.570"
              label="municípios associados à geografia do release"
            />
            <ScopeStat value={ABOUT_PAGE.scope.needPeriod} label="período agrupado para Need" />
            <ScopeStat
              value={ABOUT_PAGE.scope.capacityReference}
              label="referência para Capacity no CNES"
            />
          </div>
          <div className="about-card-grid release-components">
            <article className="about-card">
              <h3>Need</h3>
              <p>Mortalidade por suicídio + internações psiquiátricas registradas no SUS.</p>
            </article>
            <article className="about-card">
              <h3>Capacity</h3>
              <p>CAPS + leitos SUS de saúde mental em hospital geral + psiquiatras FTE no SUS.</p>
            </article>
            <article className="about-card">
              <h3>Mismatch</h3>
              <p>
                Sinal de desalinhamento territorial relativo entre necessidade medida
                e capacidade registrada.
              </p>
            </article>
          </div>
          <Link className="text-button" href="/metodologia">
            Ver metodologia completa
          </Link>
        </section>

        <section className="about-section about-negative-section" aria-labelledby="not-title">
          <p className="eyebrow">Limites</p>
          <h2 id="not-title">O que o Mente do Brasil não é</h2>
          <ul className="about-not-list">
            {ABOUT_NOT_LIST.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>

        <section className="about-section" aria-labelledby="independence-title">
          <p className="eyebrow">Independência</p>
          <h2 id="independence-title">Independência e dados públicos</h2>
          <p>{ABOUT_PAGE.independenceStatement}</p>
          <p>
            As fontes utilizadas no release atual incluem sistemas e bases do
            SUS/DATASUS e geografias do IBGE. {ABOUT_PAGE.governmentDisclaimer}
          </p>
          <p className="small-text">
            Sistemas e bases mencionados neste release: {ABOUT_PAGE.sourceSystems.join(", ")}.
          </p>
          <Link className="text-button" href="/dados">
            Ver fontes e versões
          </Link>
        </section>

        <section className="about-section" aria-labelledby="releases-title">
          <p className="eyebrow">Versionamento</p>
          <h2 id="releases-title">Um projeto construído por releases</h2>
          <p>
            O Mente do Brasil foi estruturado para evoluir por releases
            identificáveis.
          </p>
          <p>
            Novas fontes, indicadores, períodos ou metodologias não devem ser
            incorporados silenciosamente aos resultados existentes. Mudanças
            relevantes precisam ser documentadas e versionadas antes de chegar à
            interface pública.
          </p>
          <p>{ABOUT_PAGE.publicReleaseCopy}</p>
          <dl className="technical-rows">
            <Row label="public_release_status" value={ABOUT_PAGE.releaseStatus} />
            <Row label="Contrato de dados" value={ABOUT_PAGE.versions.dataContract} />
            <Row label="Método" value={ABOUT_PAGE.versions.method} />
            <Row label="Geografia" value={ABOUT_PAGE.versions.geography} />
          </dl>
        </section>

        <section className="about-section" aria-labelledby="science-title">
          <p className="eyebrow">Base científica</p>
          <h2 id="science-title">Base científica</h2>
          <p>
            A metodologia atual deriva de uma análise ecológica espacial nacional das
            439 Regiões de Saúde brasileiras.
          </p>
          <p>
            Manuscrito de referência: <cite>{ABOUT_PAGE.manuscriptTitle}</cite>.
          </p>
          <p>{ABOUT_PAGE.manuscriptStatus}</p>
          <p className="small-text">Fonte interna: {ABOUT_PAGE.versions.publicationSource}</p>
        </section>

        <section className="about-section about-explore" aria-labelledby="explore-title">
          <div>
            <p className="eyebrow">Navegação</p>
            <h2 id="explore-title">Explore o projeto</h2>
          </div>
          <div className="about-link-grid">
            <Link className="button" href="/">
              Explorar o Brasil
            </Link>
            <Link className="text-button" href="/metodologia">
              Entender a metodologia
            </Link>
            <Link className="text-button" href="/dados">
              Ver dados e versões
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
}

function VersionTag({ label, value }: { label: string; value: string }) {
  return (
    <div className="version-pill">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ScopeStat({ value, label }: { value: string; label: string }) {
  return (
    <div className="release-stat">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}
