"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";

export function AppHeader() {
  const pathname = usePathname();
  return (
    <header className="app-header">
      <div className="header-inner">
        <Link className="brand" href="/">
          <Image src="/brand/mente-do-brasil-mark.png" alt="" width={38} height={38} priority />
          <span>Mente do Brasil</span>
        </Link>
        <nav aria-label="Navegação principal" className="nav-links">
          <Link aria-current={pathname === "/" ? "page" : undefined} href="/">
            Início
          </Link>
          <Link aria-current={pathname === "/radar" ? "page" : undefined} href="/radar">
            Regiões em atenção
          </Link>
          <Link aria-current={pathname === "/comparar" ? "page" : undefined} href="/comparar">
            Comparar
          </Link>
          <Link aria-current={pathname === "/financiamento" ? "page" : undefined} href="/financiamento">
            Recursos
          </Link>
          <Link aria-current={pathname === "/gestor" ? "page" : undefined} href="/gestor">
            Painel para gestores
          </Link>
          <Link aria-current={pathname === "/metodologia" ? "page" : undefined} href="/metodologia">
            Metodologia
          </Link>
          <Link aria-current={pathname === "/dados" ? "page" : undefined} href="/dados">
            Fontes
          </Link>
          <Link aria-current={pathname === "/sobre" ? "page" : undefined} href="/sobre">
            Sobre
          </Link>
        </nav>
      </div>
    </header>
  );
}
