import type { Metadata } from "next";

export const metadata: Metadata = { title: "Governança | Mente do Brasil" };

const principles = [
  ["Versões imutáveis", "Um release bloqueado não muda de bytes. Correções criam novo ID, relação de substituição e changelog."],
  ["Proveniência", "Cada campo público tem definição, fonte, transformação, unidade, nulabilidade e status de divulgação."],
  ["Atualização validada", "Novos dados entram somente após disponibilidade oficial, validação de aquisição, trava metodológica, regressão científica e QA."],
  ["Privacidade", "Não há dados individuais nem PII. Fluxos exatos abaixo de cinco são excluídos na view, na API e no download."],
  ["Direitos de fontes", "A licença do Mente do Brasil não substitui direitos e termos de fontes terceiras; arquivos com decisão desconhecida ficam fora."],
  ["Correções e retirada", "Releases históricos são preservados, exceto exigência legal, risco de privacidade, segurança ou problema crítico de direitos."],
  ["API estável", "Mudanças incompatíveis exigem v2. A meta de aviso para depreciação é 12 meses, salvo emergência jurídica ou de segurança."],
  ["Uso responsável", "Sinais apoiam investigação territorial; não são ranking, diagnóstico, prevalência, qualidade, acesso ou recomendação automática."],
];

export default function GovernancePage() {
  return <div className="page-shell open-platform-page"><section className="intro open-platform-intro"><span className="eyebrow">MDB_DATA_GOVERNANCE_1.0</span><h1>Governança de dados</h1><p>Regras públicas para versões, fontes, correções, divulgação e continuidade científica da plataforma.</p></section><section className="governance-grid">{principles.map(([title, body], index) => <article key={title}><span>{String(index + 1).padStart(2, "0")}</span><h2>{title}</h2><p>{body}</p></article>)}</section><section className="open-platform-band"><div className="section-heading"><div><span className="eyebrow">Ciclo do release</span><h2>Da fonte ao artefato público</h2></div></div><ol className="release-lifecycle"><li>Disponibilidade da fonte autoritativa</li><li>Validação de aquisição e proveniência</li><li>Trava metodológica e regressão científica</li><li>Construção determinística e QA</li><li>Lock local, staging e gate público separado</li></ol><p className="notice-inline">Estado atual: <strong>LOCKED_LOCAL</strong>. <code>public_release_status=NOT_RELEASED</code>. Nenhum domínio ou indexação foi liberado.</p></section></div>;
}
