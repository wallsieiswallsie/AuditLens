# ADR-006: Environment connection strings

Status: Accepted
Date: 2026-09-14

## Decision

Use DATABASE_URL as the only application PostgreSQL connection setting and API_URL as the frontend backend endpoint configuration. Extend the existing API config module with required URL validation. Pass the connection string directly to Knex/pg. Inspect the URL only for local dataset write protection, never to reconstruct connection settings.

Expose exactly API_URL through Vite's explicit define mapping, with automatic prefix exposure disabled. Normalize trailing slashes centrally in the web API client.

## Reasons

Simpler deployment configuration, Railway compatibility, reduced configuration mismatch, easier environment portability, and fewer duplicated connection parameters.

## Trade-offs

The PostgreSQL client handles the connection URL; credentials are contained in one sensitive string and reserved characters need URL encoding. API_URL remains public browser configuration and requires a rebuild when changed. Container initialization retains its separate POSTGRES_* settings. Database-free operations do not require a URL. Dataset writes reject URL query options to prevent overriding the validated loopback destination.

No schema, dataset semantics, audit rules, phase scope or application architecture changes. ADR-005 remains the dataset conventions decision.
