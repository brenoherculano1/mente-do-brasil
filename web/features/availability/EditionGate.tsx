import { Suspense, type ReactNode } from "react";
import Link from "next/link";
import { internalApiBaseUrl, internalApiHeaders } from "@/lib/api/server";
import { YearSelector } from "./YearSelector";
import "./availability.css";

type Availability = {
  indicator_id: string; label: string; source: string; period: string;
  status: "AVAILABLE" | "UNAVAILABLE" | "PROVISIONAL_NOT_PUBLIC" | "UNDER_VALIDATION";
  reason_unavailable: string | null; latest_available_year: number | null;
  available_publicly: boolean;
};

export function modularPreviewEnabled() {
  if (process.env.VERCEL_ENV === "production") return false;
  return process.env.VERCEL_ENV === "preview" || process.env.NODE_ENV === "development" || process.env.MDB_MODULAR_PREVIEW === "1";
}

export async function EditionGate({ year, children, context = "Dados", code }: {
  year?: string | string[]; children?: ReactNode; context?: string; code?: string;
}) {
  const selected = (Array.isArray(year) ? year[0] : year) === "2025" ? 2025 : 2024;
  const preview = modularPreviewEnabled();
  if (selected === 2025 && !preview) return <section className="page-shell">
    <h1>Dados de 2025</h1><p>Esta atualização está reservada ao ambiente de revisão.</p>
    <Link href="/?ano=2024">Consultar dados de 2024</Link>
  </section>;
  const selector = <div className="page-shell edition-bar"><Suspense><YearSelector year={selected} preview={preview} /></Suspense></div>;
  if (selected === 2024) return <>{selector}{children}</>;
  const response = await fetch(`${internalApiBaseUrl()}/api/v1/observations/availability?year=2025`, {
    headers: internalApiHeaders(), cache: "no-store",
  });
  if (!response.ok) throw new Error("Não foi possível consultar a disponibilidade dos indicadores.");
  const catalog = await response.json() as { reference_year: number; indicators: Availability[] };
  if (catalog.reference_year !== 2025) throw new Error("Ano de referência incompatível.");
  // This view intentionally has no historical value fallback and no synthetic geometry.
  // A validated observed-data adapter is required before an AVAILABLE item is rendered.
  if (catalog.indicators.some((item) => item.available_publicly || item.status === "AVAILABLE")) {
    throw new Error("A apresentação de valores observados exige um contrato validado.");
  }
  const core = catalog.indicators.filter((item) => !item.indicator_id.endsWith("_rate") && !["pooled_psychiatric_admissions", "suicide_deaths", "radar_capacity_signals"].includes(item.indicator_id));
  return <>{selector}<div className="page-shell availability-page">
    <header><p className="eyebrow">{context}</p><h1>Dados disponíveis para 2025</h1>
      <p>Cada indicador tem seu próprio calendário de atualização. Valores ausentes não são estimados nem substituídos.</p>
      {code && <p>A seleção territorial de 2024 foi preservada. A composição regional de 2025 ainda está em validação.</p>}
    </header>
    <section className="availability-summary" aria-labelledby="availability-heading">
      <h2 id="availability-heading">Valores regionais aguardando validação</h2>
      <p>Os arquivos de estrutura e internações de 2025 foram obtidos. Antes de apresentar valores por Região de Saúde, é necessário confirmar quais municípios pertenciam a cada região naquele ano e concluir a validação de cada fonte.</p>
      <p>A mortalidade por suicídio tem uma condição diferente: a fonte oficial ainda apresenta 2025 como prévia. Por isso, necessidade, diferença e análise espacial não estão disponíveis.</p>
    </section>
    {context === "Mapa" && <section><label htmlFor="available-map-indicator">Indicador do mapa em 2025</label>
      <select id="available-map-indicator" value="" disabled aria-describedby="map-availability-reason">
        <option value="">Aguardando indicador regional validado</option>
        {core.map((item) => <option disabled key={item.indicator_id}>{item.label}: indisponível</option>)}
      </select><p id="map-availability-reason">Nenhum indicador regional de 2025 está liberado neste momento. O mapa de 2024 não é usado como substituto.</p></section>}
    {context === "Comparação" && <p>Não há indicadores regionais liberados para comparar em 2025. As linhas abaixo permanecem visíveis, sem valores ou conclusão automática.</p>}
    {context === "Evolução temporal" && <p>A comparação 2024–2025 será apresentada somente para indicadores validados nos dois anos. Não há prolongamento das séries com valores estimados.</p>}
    {context === "Sinais regionais" && <p>Os sinais de estrutura podem ser validados independentemente da mortalidade. O conjunto completo de sinais depende também de necessidade, diferença e análise espacial; ele não é calculado com componentes ausentes.</p>}
    <div className="availability-list">
      {core.map((item) => <section className="availability-row" key={item.indicator_id}>
        <div><h2>{item.label}</h2><p>{item.source} · Referência: {item.period}</p><small>Último dado disponível: {item.latest_available_year ?? "não confirmado"}</small></div>
        <div><strong aria-label={`${item.label}: sem valor disponível`}>—</strong><p>Indisponível para 2025</p>
          <p>{item.reason_unavailable}</p></div>
      </section>)}
    </div>
    <p>Não existe uma edição analítica completa de 2025. Os dados históricos de 2024 permanecem preservados.</p>
    <Link href="/dados?ano=2025">Fontes e disponibilidade por indicador</Link>
  </div></>;
}
