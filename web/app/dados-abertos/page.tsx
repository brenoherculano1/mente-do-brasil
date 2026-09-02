import type { Metadata } from "next";
import Link from "next/link";
import { ANALYTICAL_RELEASE, formatBytes, OPEN_DATA_RELEASE, openDataCatalog } from "@/lib/open-data";

export const metadata: Metadata = { title: "Dados abertos | Mente do Brasil" };

export default function OpenDataPage() {
  const { release, files } = openDataCatalog();
  const distributions = files.filter((file) => /\.(csv|parquet)$/.test(file.relative_path));
  return (
    <div className="page-shell open-platform-page">
      <section className="intro open-platform-intro">
        <span className="eyebrow">Release candidate local</span>
        <h1>Dados abertos</h1>
        <p>Camada agregada, versionada e reproduzível para pesquisa, gestão, jornalismo e ciência de dados.</p>
        <div className="release-strip" aria-label="Identificação do release">
          <span><strong>{OPEN_DATA_RELEASE}</strong></span>
          <span>Fonte analítica: {ANALYTICAL_RELEASE}</span>
          <span>{release.status}</span>
          <span>{release.public_release_status}</span>
        </div>
      </section>

      <section className="open-platform-band" aria-labelledby="downloads-title">
        <div className="section-heading"><div><span className="eyebrow">Arquivos imutáveis</span><h2 id="downloads-title">Downloads</h2></div><p>CSV para leitura ampla; Parquet para fluxos analíticos. Cada arquivo tem SHA-256 publicado.</p></div>
        <div className="download-grid">
          {distributions.map((file) => {
            const dataset = file.relative_path.replace(/\.(csv|parquet)$/, "");
            const info = release.datasets[dataset];
            return <article className="download-item" key={file.relative_path}>
              <div><span className="file-format">{file.relative_path.endsWith(".csv") ? "CSV" : "PARQUET"}</span><h3>{dataset.replaceAll("_", " ")}</h3></div>
              <p>{info ? `${info.rows.toLocaleString("pt-BR")} linhas` : "Dicionário de campos"} · {formatBytes(file.bytes)}</p>
              <code title={file.sha256}>SHA-256 {file.sha256.slice(0, 16)}…</code>
              <a className="button" href={`/downloads/${OPEN_DATA_RELEASE}/${file.relative_path}`}>Baixar arquivo</a>
            </article>;
          })}
        </div>
      </section>

      <section className="open-platform-columns">
        <div><span className="eyebrow">Uso responsável</span><h2>O que estes dados representam</h2><p>Inteligência territorial descritiva em Regiões de Saúde. Não mede prevalência, risco individual, acesso direto, qualidade, necessidade não atendida ou recomendação automática de política.</p></div>
        <div><span className="eyebrow">Licença e citação</span><h2>Reutilização com limites claros</h2><p>CC BY 4.0 cobre somente direitos licenciáveis do Mente do Brasil. Direitos de fontes terceiras permanecem com seus titulares.</p><p><Link className="text-link" href="/governanca">Governança e atribuição</Link> · <Link className="text-link" href="/metodologia">Metodologia</Link></p></div>
      </section>
    </div>
  );
}
