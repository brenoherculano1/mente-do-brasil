import { pageMetadata } from "@/lib/seo";
import { PRIVACY_NOTICE_STATUS, PRIVACY_NOTICE_VERSION } from "@/lib/public-config";

export const metadata = pageMetadata(
  "/privacidade",
  "Privacidade | Mente do Brasil",
  "Aviso factual de privacidade do Mente do Brasil em fase pré-release.",
);

export default function PrivacyPage() {
  return (
    <div className="page-shell document-page">
      <section className="document-header">
        <p className="eyebrow">Aviso factual de privacidade</p>
        <h1>Privacidade</h1>
        <p>
          Este aviso descreve a configuração atual do Mente do Brasil antes da
          publicação pública final.
        </p>
        <p className="small-text">
          Versão: {PRIVACY_NOTICE_VERSION}. Status: {PRIVACY_NOTICE_STATUS}.
        </p>
      </section>

      <section className="document-section">
        <h2>Dados usados no produto</h2>
        <p>
          O Mente do Brasil utiliza dados públicos agregados territorialmente. O
          produto não contém prontuários e não disponibiliza dados individualizados
          de pacientes.
        </p>
        <p>
          As informações são apresentadas por Região de Saúde, UF e indicadores
          agregados do release analítico versionado.
        </p>
      </section>

      <section className="document-section">
        <h2>Cookies, analytics e rastreamento</h2>
        <p>
          Na configuração atual, o produto não utiliza analytics, tracking pixels
          ou cookies de marketing.
        </p>
        <p>
          A infraestrutura de hospedagem futura poderá processar logs técnicos
          necessários para disponibilidade e segurança. Esses logs podem incluir
          timestamp, IP ou rede de origem, user-agent, rota acessada e status HTTP,
          conforme a infraestrutura de produção adotada.
        </p>
        <p>
          Esses dados técnicos não devem ser usados para perfil comercial. Este
          aviso deverá ser atualizado se funcionalidades de coleta forem adicionadas.
        </p>
      </section>

      <section className="document-section">
        <h2>Contato e correções</h2>
        <p>
          O canal de contato será configurado antes da publicação. Ele poderá ser
          usado para privacidade, correções de dados ou metodologia e comunicação
          de segurança.
        </p>
      </section>
    </div>
  );
}
