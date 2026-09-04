import { ACTIVE_RELEASE_ID } from "@/lib/api/config";

export function AppFooter() {
  return (
    <footer className="app-footer">
      <div className="footer-inner">
        <div>
          <strong>Mente do Brasil</strong>
          <p className="small-text">Inteligência territorial em saúde mental no Brasil.</p>
        </div>
        <div className="small-text">
          <div>Release: {ACTIVE_RELEASE_ID}</div>
          <div>Infraestrutura independente baseada em dados públicos.</div>
          <div className="footer-links">
            <a href="/dados-abertos">Dados abertos</a>
            <a href="/desenvolvedores">Desenvolvedores</a>
            <a href="/governanca">Governança</a>
            <a href="/privacidade">Privacidade</a>
            <a href="/contato">Contato</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
