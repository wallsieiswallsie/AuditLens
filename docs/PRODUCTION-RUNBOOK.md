# Production operations: Rule Pack v1

## Topology and deployment contract

Existing topology: separate Web and API services plus PostgreSQL. The engine is an
operator CLI, with no API invocation, worker, queue or persistent engine service.
There are no Dockerfiles, Nixpacks/Railpack configuration files or Railway project
bindings in this checkout. Actual remote service settings must be inspected before
deploying. The repository uses the npm workspace lockfile at its root.

| Setting | API | Web |
| --- | --- | --- |
| Railway root | `/` | `/` |
| Build/install | `npm ci` | `npm ci --include=dev && npm run build` |
| Explicit start override | `npm run start:api` | `npm run start:web` |
| Runtime | Node 22.12+ | Node 22.12+ |
| Health path | `/health` | `/index.html` |
| Source | apps/api | apps/web |

Set the start override on **each** service; root package intentionally has no
ambiguous default service. This addresses start-command detection without assuming
which service a root `npm start` should launch. Workspace delegation sets the correct
working directory. Migration discovery also resolves from the migration module,
independent of the shell directory. Web serves `apps/web/dist`, binds `0.0.0.0`, and
uses its supplied port; API uses its existing Hapi listener.

With the checkout and installed dependencies present, `npm start` also works from
`apps/api` or `apps/web`; API migration execution is tested there as part of startup.
This does not establish that an isolated Railway build root `/apps/api` can install
the shared root lockfile. Keep build root `/` unless a different install strategy is
actually verified. `npm run test:runtime` verifies both Web start paths after building;
disposable `npm run test:db` verifies both API start paths and migration idempotence.

API startup runs `npm run migrate` then `node src/index.js` in its workspace.
Manual migration: `npm run migrate -w @auditlens/api` from repository root. Only
pending forward migrations run, with existing Knex locks. Failure prevents startup;
errors are sanitized. Do not run seed/reset/rollback/provision commands against
production. The startup identity remains migration-capable; the audit source login
must be a separate restricted identity.

These settings follow Railway's [monorepo](https://docs.railway.com/deployments/monorepo)
and [start-command](https://docs.railway.com/builds/build-and-start-commands) guidance.
Repository configuration inspection is not deployment evidence.

## Environment inventory (names and purpose only)

| Service | Variable | Purpose |
| --- | --- | --- |
| API | NODE_ENV | Enables production configuration validation |
| API | DATABASE_URL | Required PostgreSQL connection for migrations |
| API | PORT | Platform listener port |
| API | API_HOST | Optional bind address override |
| Web build | API_URL | Required public API endpoint, compiled into browser assets |
| Web | NODE_ENV | Runtime environment |
| Web | PORT | Platform static-server listener port |
| Operator CLI | AUDIT_SOURCE_DATABASE_URL | Preferred dedicated source reader connection |
| Operator CLI | DATABASE_URL | Existing fallback source connection; omit when dedicated connection supplied |
| Operator CLI | AUDIT_OPERATOR | Optional explicit provenance label |

Artifact location is the required operator choice `--artifacts-dir`; no artifact
environment variable is invented. Development-only/test variables are listed in
[deployment configuration](DEPLOYMENT.md). API production configuration rejects a
missing/invalid database URL; migrations also require it in development. Web builds
reject missing/invalid API_URL. Intentional local port and health defaults remain.

Use Railway's private PostgreSQL endpoint for services in the same environment.
The browser needs the **public** API address, never the private database endpoint.
Public TCP proxy access is for authorized external administration. Do not print URLs,
paste credentials into logs/docs or expose database variables to Web. See
[private networking](https://docs.railway.com/networking/private-networking).

## Preflight and safe audit invocation

Use an authorized operator shell/job with this checkout, Python 3.12+, Node and npm
dependencies. The current Node-only services do not guarantee Python is installed;
do not claim a Railway engine runtime until that environment is explicitly supplied
and tested. No permanent fourth service is required for the existing CLI workflow.

```sh
npm ci
python -m venv audit-engine/.venv
. audit-engine/.venv/bin/activate
python -m pip install -e audit-engine
python -m audit_engine health
python -m audit_engine detectors list
python -m audit_engine policy validate audit-engine/policies/rulepack-v1.json
```

Provision the existing fixed `auditlens_source_reader` role through the approved
administrator process. It must have SELECT on the eleven approved source tables,
no ownership/DDL/write/TEMP rights, and no privileged memberships. The extractor
sets this role and uses a read-only consistent transaction; it never changes grants.
See [reader security](../apps/api/database/security/README.md). Verify real permission
denials only in staging/disposable acceptance, not by attempting destructive writes
against production data. Review production grants read-only.

Acquire a snapshot using the dedicated reader, or copy the controlled fixture as
described in [Rule Pack v1](RULE-PACK-V1.md). Then run the single readiness command:

```sh
python scripts/audit-readiness.py --artifacts-dir /data/auditlens --snapshot SNAPSHOT_ID
python -m audit_engine --artifacts-dir /data/auditlens run --snapshot SNAPSHOT_ID --policy audit-engine/policies/rulepack-v1.json
python -m audit_engine --artifacts-dir /data/auditlens result inspect RUN_ID
```

Readiness checks imports/registry, canonical policy/configuration, snapshot
integrity/schema requirements, and actual atomic filesystem publication with a
temporary probe. It does not contact the database or guarantee data semantics.
**Current PostgreSQL invoice references are text; full-pack execution fails at
sequence-gap.** A successful controlled fixture run does not establish full source
applicability. Keep strict mode in the canonical policy.

## Health and acceptance

1. Confirm deployment build and startup logs for the intended revision and service.
2. Request public Web `/index.html` and a nested SPA route; request API `/health`.
3. Run `npm run db:check` and `npm run db:status` in the authorized API context.
   Health is liveness only; these read-only commands establish connectivity/migration readiness.
4. Confirm the Web build contains the intended public API endpoint. Pages are
   placeholders; no browser API call or CORS integration exists. Web→API remains
   NOT RUN until a real supported call is available; two HTTP 200s do not prove it.
5. Execute CLI preflight, a controlled audit, result inspection and artifact inventory.
6. Record every Railway check as PASS, FAIL or NOT RUN in [verification](VERIFICATION.md),
   with deployment identity/time, evidence or reason. Never infer remote PASS from local tests.

## Artifact retention and rollback

No Railway Volume or external storage is configured or verified in this repository.
Treat artifacts on an unmounted Railway container filesystem as **ephemeral**, not
durable audit storage. An actual deployment's storage class remains unverified until
its mount is inspected. A directory named `/data` is not proof of a volume. Export
artifacts to an approved retention location before redeploy; preserve the complete
snapshot/run/results tree. Existing [Railway volumes](https://docs.railway.com/volumes/reference)
can provide persistence only if attached, mounted and tested; none is added here.

Rollback application code to the last verified deployment only after checking schema
compatibility. Application rollback does not undo migrations. Never automatically
roll back/reset the database. Capture sanitized errors and keep failed artifacts;
rerun audits with fresh IDs. Artifacts are unsigned and privileged local operators
can tamper with them; hashes provide consistency, not authenticity.

## Failure troubleshooting

| Failure class | Evidence and smallest response |
| --- | --- |
| Build | Inspect dependency/build exit; use repository root and shared lockfile; supply API_URL for Web |
| No start command | Set the service-specific explicit start override above |
| Working directory | Confirm root `/`; do not prefix workspace-local commands with duplicated apps/api paths |
| Environment | Check variable names/presence without dumping values; rebuild Web after API_URL change |
| Migration | Startup emits sanitized failure; inspect migration state/privileges using approved admin access; never reset |
| DB connectivity | Check private hostname, service environment and reachability; retain reader privilege limits |
| Port binding | Confirm separate service PORT and accessible bind host |
| Detector error | Inspect result summary/status and effective configuration; integer-reference precondition applies |
| Artifact publication | Check writable mount and hard-link support; preserve failed run and choose a fresh ID |
| Windows disposable initdb | Restricted-token errors 87/3 require a permitted broader-process run of the isolated runner |

Trust boundary remains trusted in-process Python detectors from an explicit registry.
No API accepts arbitrary policy paths, modules, Python expressions or shell commands.
No OS isolation, timeout system, artifact signing, scheduling or new business rule is
introduced in this phase.

The SDK supplies only frozen context and validated configuration; it does not pass
connections, credentials, filesystem roots or execution services. This is an interface
boundary, not a sandbox: trusted Python code still has normal process capabilities.
