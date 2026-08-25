"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  DATA_DICTIONARY,
  DATA_DICTIONARY_CATEGORIES,
  DATA_RELEASE,
  DATASETS,
  GEOMETRY_DATASETS,
  PRIMARY_SOURCES,
  PROVENANCE,
} from "@/lib/data-page";

export function DataPage() {
  const [query, setQuery] = useState("");
  const normalizedQuery = query.trim().toLowerCase();
  const filteredFields = useMemo(() => {
    if (!normalizedQuery) return DATA_DICTIONARY;
    return DATA_DICTIONARY.filter((field) =>
      [field.name, field.label, field.category, field.description, field.sourceField]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery),
    );
  }, [normalizedQuery]);

  return (
    <div className="data-shell page-shell">
      <section className="intro data-hero" aria-labelledby="data-title">
        <p className="eyebrow">Dados</p>
        <h1 id="data-title">Dados e versões</h1>
        <p>
          Conheça os datasets, fontes, versões e critérios de publicação que
          sustentam o Mente do Brasil.
        </p>
        <div className="metadata-strip" aria-label="Identificadores do release">
          <VersionTag label="Release analítico" value={DATA_RELEASE.releaseId} />
          <VersionTag label="Método" value={DATA_RELEASE.methodVersion} />
          <VersionTag label="Geografia" value={DATA_RELEASE.geographyVersion} />
        </div>
      </section>

      <main className="data-content">
        <section className="data-section availability-section" aria-labelledby="availability-title">
          <div>
            <p className="eyebrow">Disponibilidade do release</p>
            <h2 id="availability-title">Validado localmente, ainda não publicado</h2>
            <p>{DATA_RELEASE.publicAvailabilityText}</p>
          </div>
          <div className="status-grid">
            <StatusItem label="Qualidade" value="Validada" />
            <StatusItem label="Gate de release" value="Aprovado" />
            <StatusItem label="Prontidão" value="Pronto para decisão de publicação" />
            <StatusItem label="Disponibilidade pública" value={DATA_RELEASE.publicAvailabilityLabel} />
          </div>
          <details className="data-details">
            <summary>Detalhes técnicos do release</summary>
            <dl className="technical-rows">
              <Row label="release_status" value={DATA_RELEASE.releaseStatus} />
              <Row label="quality_status" value={DATA_RELEASE.qualityStatus} />
              <Row label="release_gate" value={DATA_RELEASE.releaseGate} />
              <Row label="release_readiness" value={DATA_RELEASE.releaseReadiness} />
              <Row label="public_release_status" value={DATA_RELEASE.publicReleaseStatus} />
            </dl>
          </details>
        </section>

        <section className="data-section" aria-labelledby="release-inventory-title">
          <p className="eyebrow">Inventário</p>
          <h2 id="release-inventory-title">O que existe neste release</h2>
          <div className="release-stat-grid">
            <ReleaseStat value="439" label="Regiões de Saúde" />
            <ReleaseStat value="5.570" label="municípios no crosswalk" />
            <ReleaseStat value="35" label="campos no dataset analítico principal" />
          </div>
          <div className="two-column">
            <InfoBlock label="Unidade analítica" value="Região de Saúde" />
            <InfoBlock label="Referência geográfica" value="fim de 2024" />
          </div>
        </section>

        <section className="data-section" aria-labelledby="datasets-title">
          <p className="eyebrow">Inventário de datasets</p>
          <h2 id="datasets-title">Datasets</h2>
          <div className="dataset-list">
            {DATASETS.map((dataset) => (
              <article className="dataset-item" key={dataset.title}>
                <div>
                  <h3>{dataset.title}</h3>
                  <p>{dataset.purpose}</p>
                </div>
                <dl className="dataset-meta">
                  <Row label="artefato" value={dataset.path} />
                  <Row label="unidade" value={dataset.unit} />
                  <Row label="rows" value={String(dataset.rows)} />
                  <Row label="columns" value={String(dataset.columns)} />
                  <Row label="formato" value={dataset.format} />
                  <Row label="canonical" value={dataset.canonical} />
                  <Row label="release" value={dataset.release} />
                  <Row label="method" value={dataset.method} />
                  <Row label="geography" value={dataset.geography} />
                  <Row label="sha256" value={dataset.sha256} />
                </dl>
              </article>
            ))}
            {GEOMETRY_DATASETS.map((geometry) => (
              <article className="dataset-item" key={geometry.title}>
                <div>
                  <h3>{geometry.title}</h3>
                  <p>{geometry.description}</p>
                </div>
                <dl className="dataset-meta">
                  <Row label="versão" value={geometry.version} />
                  <Row label="CRS" value={geometry.crs} />
                </dl>
              </article>
            ))}
          </div>
        </section>

        <section className="data-section" aria-labelledby="dictionary-title">
          <p className="eyebrow">Schema</p>
          <h2 id="dictionary-title">Dicionário de dados</h2>
          <p>
            O dicionário abaixo representa o schema canônico versionado do dataset
            analítico. Valores ausentes são preservados como ausentes. Null não
            equivale a zero.
          </p>
          <div className="dictionary-search">
            <label htmlFor="field-search">Buscar campo</label>
            <input
              id="field-search"
              className="input"
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Nome técnico, nome amigável ou categoria"
            />
          </div>
          <p className="small-text" aria-live="polite">
            {filteredFields.length} de {DATA_DICTIONARY.length} campos.
          </p>
          <div className="dictionary-groups">
            {DATA_DICTIONARY_CATEGORIES.map((category) => {
              const fields = filteredFields.filter((field) => field.category === category);
              if (!fields.length) return null;
              return (
                <details className="dictionary-group" key={category} open>
                  <summary>
                    {category} <span>{fields.length}</span>
                  </summary>
                  <div className="dictionary-table-wrap">
                    <table className="dictionary-table">
                      <thead>
                        <tr>
                          <th>Campo</th>
                          <th>Definição</th>
                          <th>Tipo</th>
                          <th>Unidade</th>
                          <th>Nullable</th>
                          <th>Origem</th>
                        </tr>
                      </thead>
                      <tbody>
                        {fields.map((field) => (
                          <tr key={field.name}>
                            <th scope="row">
                              <span>{field.label}</span>
                              <code>{field.name}</code>
                            </th>
                            <td>
                              {field.description}
                              <span className="field-note">{field.limitations}</span>
                            </td>
                            <td>{field.type}</td>
                            <td>{field.unit || "not_applicable"}</td>
                            <td>{field.nullable ? "sim" : "não"}</td>
                            <td>{field.sourceField}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </details>
              );
            })}
          </div>
        </section>

        <section className="data-section" aria-labelledby="sources-title">
          <p className="eyebrow">Fontes primárias</p>
          <h2 id="sources-title">Fontes</h2>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Fonte</th>
                  <th>Uso no release</th>
                  <th>Período</th>
                </tr>
              </thead>
              <tbody>
                {PRIMARY_SOURCES.map(([source, use, period]) => (
                  <tr key={source}>
                    <th scope="row">{source}</th>
                    <td>{use}</td>
                    <td>{period}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="data-section" aria-labelledby="provenance-title">
          <p className="eyebrow">Auditoria</p>
          <h2 id="provenance-title">Proveniência</h2>
          <p>
            O Mente do Brasil preserva a origem dos principais arquivos utilizados
            para que cada release possa ser auditado e reconstruído.
          </p>
          <div className="provenance-grid">
            <InfoBlock label="access date" value={PROVENANCE.accessDate} />
            <InfoBlock label="raw provenance records" value="1.137" />
          </div>
          <div className="table-wrap compact-table">
            <table>
              <thead>
                <tr>
                  <th>Fonte</th>
                  <th>Registros</th>
                </tr>
              </thead>
              <tbody>
                {PROVENANCE.breakdown.map(([source, count]) => (
                  <tr key={source}>
                    <th scope="row">{source}</th>
                    <td>{count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="small-text">{PROVENANCE.cnesNote}</p>
        </section>

        <section className="data-section" aria-labelledby="versions-title">
          <p className="eyebrow">Versionamento</p>
          <h2 id="versions-title">Versões</h2>
          <dl className="technical-rows">
            <Row label="Contrato de dados" value={DATA_RELEASE.dataContract} />
            <Row label="Método" value={DATA_RELEASE.methodVersion} />
            <Row label="Release analítico" value={DATA_RELEASE.releaseId} />
            <Row label="Canonical" value={DATA_RELEASE.canonicalVersion} />
            <Row label="Geografia" value={DATA_RELEASE.geographyVersion} />
            <Row label="Geometria web" value={DATA_RELEASE.webGeometryVersion} />
          </dl>
          <p>
            Um release do Mente do Brasil representa uma combinação versionada de
            dados, método e geografia. Correções ou mudanças metodológicas
            relevantes não devem substituir silenciosamente resultados anteriores.
          </p>
          <ul>
            <li>Novo dado não implica necessariamente o mesmo release.</li>
            <li>Mudança metodológica deve gerar versão identificável.</li>
            <li>Mudança geográfica precisa ser explicitada.</li>
            <li>Consumidores não devem assumir apenas um release para sempre.</li>
          </ul>
        </section>

        <section className="data-section policy-grid" aria-label="Políticas de publicação">
          <PolicyBlock
            title="Downloads"
            text="Os arquivos para reutilização pública serão disponibilizados quando o primeiro release público for aprovado. Os formatos públicos serão definidos no momento da publicação do release."
          />
          <PolicyBlock
            title="API"
            text="A infraestrutura de API já possui contrato versionado para uso interno e validação local. A documentação e o endpoint públicos serão disponibilizados apenas quando o release público for aprovado."
          />
          <PolicyBlock
            title="Licença"
            text="A licença de reutilização do primeiro release público ainda será definida antes da publicação."
          />
          <PolicyBlock
            title="Como citar os dados"
            text="A forma definitiva de citação será disponibilizada junto ao primeiro release público."
          />
        </section>

        <section className="data-section methodology-cta" aria-labelledby="methodology-cta-title">
          <div>
            <p className="eyebrow">Método</p>
            <h2 id="methodology-cta-title">Como os indicadores são calculados</h2>
          </div>
          <Link className="text-button" href="/metodologia">
            Entender como os indicadores são calculados →
          </Link>
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

function StatusItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="status-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ReleaseStat({ value, label }: { value: string; label: string }) {
  return (
    <div className="release-stat">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

function InfoBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="info-block">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function PolicyBlock({ title, text }: { title: string; text: string }) {
  return (
    <article className="policy-block">
      <h2>{title}</h2>
      <p>{text}</p>
    </article>
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
