# Environment and Railway configuration

AuditLens uses DATABASE_URL as its only application PostgreSQL connection setting and API_URL as its only public backend endpoint setting. Root .env is for local development; production services do not share an environment file.

## Service responsibilities

| Service | Configuration |
| --- | --- |
| API | NODE_ENV; API_HOST/API_PORT as applicable; DATABASE_URL for database access; future JWT_ACCESS_SECRET and JWT_REFRESH_SECRET; AUDITLENS_DATA_SEED for dataset tooling |
| Web | API_URL at build time; optional WEB_PORT only for local development |
| PostgreSQL container | POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD for image initialization only |

The web service must not receive DATABASE_URL or JWT secrets. API_URL is public and expected to be visible in browser JavaScript. DATABASE_URL contains credentials and is confidential server-side configuration: never log it or return it in API errors. Percent-encode reserved characters in URL credentials.

## Railway

```text
Postgres
    │ DATABASE_URL
    ▼
@auditlens/api
    │ HTTPS
    ▼
@auditlens/web
```

API service variables:

```dotenv
NODE_ENV=production
API_HOST=0.0.0.0
API_PORT=3001
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

Set the API public service target port to match API_PORT. No individual PostgreSQL connection parameters or hard-coded Railway identifiers are needed. JWT secrets remain unused until Phase 2; supply independent server-side secrets when that feature exists. AUDITLENS_DATA_SEED is only needed when using dataset tooling (default 20260914); seed/reset guards refuse production writes.

Web service variable (available during npm run build):

```dotenv
API_URL=https://<API_SERVICE_PUBLIC_DOMAIN>
```

Publish apps/web/dist with a static host supporting SPA fallback. Changing API_URL requires rebuilding. Vite disables automatic environment-prefix exposure and defines exactly import.meta.env.API_URL. Vite's built-in mode flags are still available. Root server environment values are never passed wholesale to client code.

This describes configuration compatibility, not completion of deployment or later phases. Existing authentication, API cross-origin policy and production readiness remain outside this refactor.

## Local Docker

Copy .env.example to .env. Replace CHANGE_ME in DATABASE_URL and POSTGRES_PASSWORD with the same locally chosen password (URL-encoded in DATABASE_URL). Compose initializes the image with POSTGRES_* values; AuditLens connects only through DATABASE_URL. Existing volumes retain their initialized credentials. Host-run applications use 127.0.0.1:5432; an API inside the same Docker network would use postgres:5432. The local seed/reset guard deliberately rejects remote hosts and URL query overrides.
