# Production environment matrix

Values marked secret must be created independently per environment and entered directly
in provider settings. No value is committed or pasted into chat.

## FastAPI project

| Variable | Staging | Production | Secret |
| --- | --- | --- | --- |
| `MDB_PRODUCTION_MODE` | `true` | `true` | no |
| `MDB_DEFAULT_RELEASE_ID` | `MDB_ANALYTICAL_2024_2` | `MDB_ANALYTICAL_2024_2` | no |
| `MDB_API_ENABLE_DOCS` | `false` | `false` | no |
| `MDB_API_ALLOW_FULL_GEOMETRY` | `false` | `false` | no |
| `MDB_API_ALLOWED_ORIGINS` | exact protected web preview origin | `https://mentedobrasil.com.br` | no |
| `MDB_INTERNAL_API_TOKEN` | independent random value, 32+ characters | independent random value, 32+ characters | yes |
| `MDB_DB_HOST` / `PORT` / `NAME` | staging Supavisor transaction endpoint | production Supavisor transaction endpoint | partially |
| `MDB_API_DB_USER` | `mente_do_brasil_api` | `mente_do_brasil_api` | no |
| `MDB_API_DB_PASSWORD` | independent staging role password | independent production role password | yes |
| `MDB_DB_SSLMODE` | `verify-full` | `verify-full` | no |
| `MDB_DB_SSLROOTCERT` | bundled provider CA path | bundled provider CA path | no |
| `MDB_DB_POOL_MIN_SIZE` | `0` | `0` | no |
| `MDB_DB_POOL_MAX_SIZE` | `4` | `4` | no |

## Next.js project

| Variable | Staging | Production | Secret |
| --- | --- | --- | --- |
| `MDB_API_INTERNAL_BASE_URL` | exact staging API URL | exact production API URL | no |
| `MDB_INTERNAL_API_TOKEN` | same value as staging API only | same value as production API only | yes |
| `MDB_RATE_LIMIT_TRUST_PROXY_HEADERS` | `true` | `true` | no |
| `MDB_PUBLIC_INDEXING_ENABLED` | `false` | `false` until final switch, then `true` | no |
| `MDB_PUBLIC_SITE_URL` | unset | `https://mentedobrasil.com.br` | no |
| `MDB_PUBLIC_CONTACT_EMAIL` | unset | only after delivery test | no |
| `MDB_PUBLIC_SECURITY_EMAIL` | unset | only after delivery test | no |

`VERCEL=1` is platform-provided and is required in addition to the explicit proxy trust
flag before the application accepts Vercel's overwritten `x-forwarded-for` value for
rate-limit identity. No secret may use the `NEXT_PUBLIC_` prefix.

Administrative migrations, backups, and rebuilds use the direct/session connection and
an ignored local environment. Application traffic uses only the transaction pooler.
