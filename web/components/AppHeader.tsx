"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function AppHeader() {
  const pathname = usePathname();
  return (
    <header className="app-header">
      <div className="header-inner">
        <Link className="brand" href="/">
          Mente do Brasil
        </Link>
        <nav aria-label="Navegação principal" className="nav-links">
          <Link aria-current={pathname === "/" ? "page" : undefined} href="/">
            Explorar
          </Link>
          <Link aria-current={pathname === "/radar" ? "page" : undefined} href="/radar">
            Radar
          </Link>
          <Link aria-current={pathname === "/financiamento" ? "page" : undefined} href="/financiamento">
            Financiamento
          </Link>
          <Link aria-current={pathname === "/gestor" ? "page" : undefined} href="/gestor">
            Gestor
          </Link>
          <Link aria-current={pathname === "/metodologia" ? "page" : undefined} href="/metodologia">
            Metodologia
          </Link>
          <Link aria-current={pathname === "/dados" ? "page" : undefined} href="/dados">
            Dados
          </Link>
          <Link aria-current={pathname === "/sobre" ? "page" : undefined} href="/sobre">
            Sobre
          </Link>
          <details className="nav-more">
            <summary>Mais</summary>
            <div className="nav-more-menu">
              <Link aria-current={pathname === "/dados-abertos" ? "page" : undefined} href="/dados-abertos">
                Dados abertos
              </Link>
              <Link aria-current={pathname === "/desenvolvedores" ? "page" : undefined} href="/desenvolvedores">
                Desenvolvedores
              </Link>
              <Link aria-current={pathname === "/mudancas" ? "page" : undefined} href="/mudancas">
                Mudanças
              </Link>
              <Link aria-current={pathname === "/fluxos" ? "page" : undefined} href="/fluxos">
                Fluxos
              </Link>
            </div>
          </details>
        </nav>
      </div>
    </header>
  );
}
