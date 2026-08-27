import { NextRequest, NextResponse } from "next/server";
import {
  PUBLIC_ROUTE_HEALTH_REGION_CODES,
  PUBLIC_ROUTE_UFS,
} from "@/lib/public-route-inventory";

const HEALTH_REGION_CODE_SET: ReadonlySet<string> = new Set(PUBLIC_ROUTE_HEALTH_REGION_CODES);
const UF_SET: ReadonlySet<string> = new Set(PUBLIC_ROUTE_UFS);

function notFoundResponse(kind: "state" | "region") {
  const title = kind === "state" ? "Estado não encontrado." : "Região de Saúde não encontrada.";
  const body =
    kind === "state"
      ? "A UF informada não corresponde a uma UF válida neste release."
      : "O código informado não corresponde a uma Região de Saúde neste release.";
  const html = [
    "<!doctype html>",
    '<html lang="pt-BR">',
    "<head>",
    '<meta charset="utf-8">',
    `<title>${title}</title>`,
    '<meta name="robots" content="noindex">',
    "</head>",
    "<body>",
    "<main>",
    `<h1>${title}</h1>`,
    `<p>${body}</p>`,
    '<a href="/">Voltar para explorar o Brasil</a>',
    "</main>",
    "</body>",
    "</html>",
  ].join("");
  return new NextResponse(
    html,
    {
      status: 404,
      headers: {
        "content-type": "text/html; charset=utf-8",
        "cache-control": "no-store",
      },
    },
  );
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const stateMatch = /^\/estado\/([^/]+)\/?$/.exec(pathname);
  if (stateMatch) {
    const rawUf = decodeURIComponent(stateMatch[1]);
    const normalizedUf = rawUf.trim().toUpperCase();
    if (!UF_SET.has(normalizedUf)) return notFoundResponse("state");
    if (rawUf !== normalizedUf) {
      const redirectUrl = request.nextUrl.clone();
      redirectUrl.pathname = `/estado/${normalizedUf}`;
      return NextResponse.redirect(redirectUrl, 308);
    }
  }

  const regionMatch = /^\/regiao\/([^/]+)\/?$/.exec(pathname);
  if (regionMatch) {
    const code = decodeURIComponent(regionMatch[1]).trim();
    if (!HEALTH_REGION_CODE_SET.has(code)) {
      return notFoundResponse("region");
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/estado/:path*", "/regiao/:path*"],
};
