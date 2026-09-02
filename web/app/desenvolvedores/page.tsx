import type { Metadata } from "next";

export const metadata: Metadata = { title: "Desenvolvedores | Mente do Brasil" };

const example = `{
  "meta": {
    "api_version": "MDB_PUBLIC_API_V1",
    "open_data_release": "MDB_OPEN_DATA_2024_1",
    "analytical_release": "MDB_ANALYTICAL_2024_2"
  },
  "data": {
    "health_region_code": "12001",
    "health_region_name": "Alto Acre",
    "uf": "AC"
  }
}`;

export default function DevelopersPage() {
  return <div className="page-shell open-platform-page">
    <section className="intro open-platform-intro"><span className="eyebrow">MDB_PUBLIC_API_V1</span><h1>API para desenvolvedores</h1><p>Interface pública anônima, somente leitura e vinculada ao release de dados. Base local: <code>/api/public/v1</code>.</p></section>
    <section className="api-layout">
      <nav className="api-index" aria-label="Índice da API"><strong>Referência</strong><a href="#endpoints">Endpoints</a><a href="#pagination">Paginação</a><a href="#errors">Erros</a><a href="#examples">Exemplos</a><a href="/api/public/v1/openapi.json">OpenAPI 3.1</a></nav>
      <div className="api-content">
        <section id="endpoints"><span className="eyebrow">GET · HEAD · OPTIONS</span><h2>Endpoints</h2><div className="endpoint-list">{["/releases", "/health-regions", "/health-regions/{code}", "/health-regions/{code}/timeline", "/changes", "/financing", "/health-regions/{code}/flows", "/health-regions/{code}/peers", "/municipalities/{ibge_code}/health-region", "/metadata/indicators", "/metadata/methodology"].map((path) => <code key={path}>GET /api/public/v1{path}</code>)}</div></section>
        <section id="pagination"><h2>Paginação e limites</h2><p><code>limit</code> padrão 100, máximo 500, com <code>next_cursor</code> opaco. Fluxos são limitados a 100. Limite anônimo local: 120 requisições por 60 segundos.</p></section>
        <section id="errors"><h2>Erros</h2><p>Erros usam <code>application/problem+json</code>. A API não aceita credenciais, escrita nem parâmetros SQL livres.</p></section>
        <section id="examples"><h2>Exemplos reais</h2><div className="code-pair"><div><h3>curl</h3><pre><code>{`curl -s http://localhost:3000/api/public/v1/health-regions/12001`}</code></pre><h3>Python</h3><pre><code>{`import requests\nBASE = "http://localhost:3000/api/public/v1"\nr = requests.get(BASE + "/health-regions/12001", timeout=10)\nr.raise_for_status()\nprint(r.json()["data"])`}</code></pre><h3>JavaScript</h3><pre><code>{`const BASE = "/api/public/v1";\nconst r = await fetch(BASE + "/health-regions/12001");\nif (!r.ok) throw await r.json();\nconsole.log((await r.json()).data);`}</code></pre></div><div><h3>Resposta reduzida</h3><pre><code>{example}</code></pre></div></div></section>
        <section><span className="eyebrow">English quick reference</span><h2>Stable, read-only public data</h2><p>Responses identify the API, open-data, and analytical releases. Attribute Mente do Brasil and the original public sources. This is territorial intelligence, not a clinical or individual-risk tool.</p></section>
      </div>
    </section>
  </div>;
}
