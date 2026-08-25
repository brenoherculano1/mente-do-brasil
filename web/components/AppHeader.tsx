import Link from "next/link";

export function AppHeader() {
  return (
    <header className="app-header">
      <div className="header-inner">
        <Link className="brand" href="/">
          Mente do Brasil
        </Link>
        <nav aria-label="Navegação principal" className="nav-links">
          <Link aria-current="page" href="/">
            Explorar
          </Link>
          <span className="muted-link" aria-disabled="true">
            Metodologia
          </span>
          <span className="muted-link" aria-disabled="true">
            Dados
          </span>
          <span className="muted-link" aria-disabled="true">
            Sobre
          </span>
        </nav>
      </div>
    </header>
  );
}
