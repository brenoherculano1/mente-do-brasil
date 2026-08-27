# Observability

## Scope

This is a vendor-neutral application foundation. It does not install Sentry,
Datadog, New Relic, Grafana Cloud, Prometheus, or any remote provider.

## Structured Logs

FastAPI and the Next operational API emit deterministic JSON logs for important
operational events:

- startup and shutdown;
- readiness failure;
- upstream unavailable;
- rate-limited operational API request;
- unexpected exception.

Expected fields include:

- `timestamp`
- `level`
- `service`
- `event`
- `status`
- `release_id` when applicable
- `route_class` when applicable
- `duration_ms` when applicable
- `error_code` when applicable
- `request_id`

Logs must not include raw IP addresses, authorization headers, cookies,
passwords, tokens, full request bodies, `DATABASE_URL`, or patient-level data.

## Request ID

The Next operational API generates or accepts a safe `X-Request-ID` and returns
it in the response. It forwards the same value to FastAPI for correlation.

`X-Request-ID` is only a debugging correlation ID. It is not authentication,
authorization, or a security boundary.

## Health and Readiness

FastAPI:

- `/health`: process is alive.
- `/ready`: database and default release are ready.

Next:

- `/healthz`: Next process is alive.
- `/readyz`: Next can reach FastAPI `/ready`.

Health and readiness responses use `Cache-Control: no-store`.

## Future Minimum Alerts

When staging or production infrastructure is created, configure at least:

- site unavailable;
- Next `/readyz` failing;
- FastAPI `/ready` failing;
- high 5xx rate;
- sustained 429 rate;
- database unavailable.

## Rate Limiter Deployment Note

Hardening 04 uses `anonymous-global` unless `MDB_RATE_LIMIT_TRUST_PROXY_HEADERS`
is explicitly set to `true`. Production must configure trusted client-IP
provenance at the ingress before enabling that setting. Only enable it after the
provider or reverse proxy is validated to overwrite incoming forwarding headers.

Until that decision is made, `anonymous-global` is the fail-safe behavior.
