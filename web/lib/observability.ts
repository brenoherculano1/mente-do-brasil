import { randomUUID } from "node:crypto";

const SAFE_REQUEST_ID = /^[A-Za-z0-9._:-]{8,80}$/;
const SENSITIVE_KEY = /(authorization|cookie|password|token|secret|database_url|dsn|ip|x-forwarded-for|x-real-ip)/i;
const RAW_IP_VALUE = /^(?:(?:\d{1,3}\.){3}\d{1,3}|(?:[a-f0-9]{1,4}:){2,}[a-f0-9]{1,4})$/i;

export function requestIdFromHeaders(headers: Headers): string {
  const incoming = headers.get("x-request-id")?.trim();
  if (incoming && SAFE_REQUEST_ID.test(incoming) && !RAW_IP_VALUE.test(incoming)) {
    return incoming;
  }
  return randomUUID();
}

export function sanitizeLogFields(fields: Record<string, unknown>): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(fields).map(([key, value]) => {
      if (SENSITIVE_KEY.test(key)) return [key, "[REDACTED]"];
      if (typeof value === "string" && RAW_IP_VALUE.test(value)) return [key, "[REDACTED]"];
      return [key, value];
    }),
  );
}

export function operationalLog(event: string, fields: Record<string, unknown> = {}): void {
  const payload = sanitizeLogFields({
    timestamp: new Date().toISOString(),
    level: fields.level ?? "info",
    service: "mente-do-brasil-next",
    event,
    ...fields,
  });
  console.log(JSON.stringify(payload));
}
