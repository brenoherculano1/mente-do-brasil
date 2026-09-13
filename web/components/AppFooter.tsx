export function AppFooter() {
  return (
    <footer className="app-footer">
      <div className="footer-inner">
        <div>
          <strong>Mente do Brasil</strong>
          <p className="small-text">Inteligência territorial em saúde mental no Brasil.</p>
          <p className="small-text">Idealizado e desenvolvido por Breno Herculano.</p>
        </div>
        <div className="small-text">
          <div>Plataforma independente baseada em dados públicos.</div>
          <div className="footer-links">
            <a href="/dados">Fontes</a>
            <a href="/dados-abertos">Dados abertos</a>
            <a href="/desenvolvedores">API</a>
            <a href="/governanca">Governança</a>
            <a href="/sobre">Sobre</a>
            <a href="/privacidade">Privacidade</a>
            <a href="/contato">Contato</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
