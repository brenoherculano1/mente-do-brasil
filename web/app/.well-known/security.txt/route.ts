import { applyOperationalSecurityHeaders } from "@/lib/api/ingress-policy";
import { absolutePublicUrl, publicSiteConfig } from "@/lib/public-config";
import { requestIdFromHeaders } from "@/lib/observability";

export const dynamic = "force-dynamic";

export function GET(request: Request) {
  const requestId = requestIdFromHeaders(request.headers);
  const config = publicSiteConfig();
  const headers = applyOperationalSecurityHeaders(
    new Headers({
      "Cache-Control": "no-store",
      "Content-Type": "text/plain; charset=utf-8",
      "X-Request-ID": requestId,
    }),
  );
  if (!config.siteUrl || !config.securityEmail) {
    return new Response("Not configured.\n", { status: 404, headers });
  }
  return new Response(
    [
      `Contact: mailto:${config.securityEmail}`,
      "Preferred-Languages: pt-BR, en",
      `Canonical: ${absolutePublicUrl("/.well-known/security.txt", config)}`,
      "",
    ].join("\n"),
    { status: 200, headers },
  );
}
