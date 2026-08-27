import { pageMetadata } from "@/lib/seo";
import { publicSiteConfig } from "@/lib/public-config";

export const metadata = pageMetadata(
  "/contato",
  "Contato | Mente do Brasil",
  "Canais preparados para contato, correções científicas e comunicação de segurança do Mente do Brasil.",
);

export default function ContactPage() {
  const config = publicSiteConfig();
  const contact = config.contactEmail;
  const security = config.securityEmail;
  return (
    <div className="page-shell document-page">
      <section className="document-header">
        <p className="eyebrow">Contato</p>
        <h1>Contato</h1>
        <p>
          Esta página prepara os canais operacionais do Mente do Brasil para a
          publicação. Não há formulário, banco de mensagens ou armazenamento de
          relatos pelo site.
        </p>
      </section>

      <section className="document-section">
        <h2>Contato geral</h2>
        {contact ? (
          <p>
            Envie mensagens para <a className="inline-link" href={`mailto:${contact}`}>{contact}</a>.
          </p>
        ) : (
          <p>Canal de contato será configurado antes da publicação.</p>
        )}
      </section>

      <section className="document-section">
        <h2>Correção de dados ou metodologia</h2>
        <p>Ao reportar possível erro, inclua quando aplicável:</p>
        <ul>
          <li>URL da página.</li>
          <li>Região de Saúde e código.</li>
          <li>Indicador relacionado.</li>
          <li>Descrição objetiva do problema.</li>
          <li>Fonte ou referência, se houver.</li>
        </ul>
        <p className="small-text">Não envie informações identificáveis de pacientes.</p>
      </section>

      <section className="document-section">
        <h2>Segurança</h2>
        {security ? (
          <p>
            Relatos de segurança podem ser enviados para{" "}
            <a className="inline-link" href={`mailto:${security}`}>{security}</a>.
          </p>
        ) : (
          <p>
            O canal de segurança será configurado antes da publicação. Se apenas
            um email público for definido, ele poderá receber contato geral,
            correções e segurança.
          </p>
        )}
      </section>
    </div>
  );
}
