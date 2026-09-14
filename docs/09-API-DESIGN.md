# API design

Only GET /health is implemented. All other contracts are proposals. Local base URL: http://127.0.0.1:3001. Prefix future operational endpoints with /business; /users always means audit platform identities. No source-write endpoint belongs under /audit.

| Method | Path | Purpose | Authentication | Authorization | Request | Response | Possible errors |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GET | /health | Liveness | Public | None | None | 200 {"status":"ok","service":"auditlens-api"} | 500 |
| POST | /auth/login | Authenticate | Public | Rate limited | {email,password} | 200 {accessToken,user}; refresh cookie | 400,401,429 |
| POST | /auth/refresh | Rotate session | Refresh cookie | Valid session + origin/CSRF | None | 200 {accessToken}; rotated cookie | 401,403,429 |
| POST | /auth/logout | Revoke session | Refresh cookie | Session owner + origin/CSRF | None | 204 | 401,403 |
| GET | /users | List platform identities | JWT | manager | ?limit=20&cursor=... | 200 {data:[{id,email,role,status}],nextCursor} | 401,403,400 |
| GET | /roles | Read platform role definitions | JWT | viewer/auditor/manager | None | 200 {data:[{code,permissions}]} | 401,403 |
| GET | /audit/tests | List versioned tests | JWT | viewer/auditor/manager | ?limit=20 | 200 {data:[{id,code,version,name}],nextCursor} | 400,401,403 |
| POST | /audit/runs | Request run (worker design pending) | JWT | auditor/manager | {testIds,datasetReference,parameters} + Idempotency-Key | 202 {id,status:queued} | 400,401,403,409,422,503 |
| GET | /audit/runs | List runs | JWT | viewer/auditor/manager | ?status=&limit=20 | 200 {data:[{id,status}],nextCursor} | 400,401,403 |
| GET | /audit/runs/{id} | Read run metadata | JWT | viewer/auditor/manager | UUID path | 200 {id,status,parameters,startedAt,finishedAt} | 400,401,403,404 |
| GET | /audit/results | Read results | JWT | viewer/auditor/manager | ?runId=UUID&limit=20 | 200 {data:[{id,testId,outcome,populationCount,exceptionCount}],nextCursor} | 400,401,403,404 |
| GET | /audit/results/{id}/evidence | Read restricted evidence | JWT | auditor/manager | UUID path; cursor | 200 {data:[{id,sourceReference,snapshot,sha256}],nextCursor} | 400,401,403,404 |
| GET | /findings | List findings | JWT | viewer/auditor/manager | ?status=&limit=20 | 200 {data:[{id,title,severity,status}],nextCursor} | 400,401,403 |
| POST | /findings | Draft reviewed observation | JWT | auditor/manager | {title,condition,criteria,riskId,impact,recommendation,severity,evidenceIds} | 201 {id,status:draft} | 400,401,403,422 |
| GET | /findings/{id} | Read finding | JWT | viewer/auditor/manager | UUID path | 200 {id,title,condition,criteria,riskId,impact,recommendation,severity,status,responsibleParty,createdAt,updatedAt} | 400,401,403,404 |
| PATCH | /findings/{id} | Edit or transition finding | JWT | auditor edits draft; manager reviews/closes | {allowedChangedFields,expectedUpdatedAt,transitionReason} | 200 finding | 400,401,403,404,409,422 |
| GET | /risks | List project risks | JWT | viewer/auditor/manager | ?limit=20 | 200 {data:[{id,code,title,description}],nextCursor} | 400,401,403 |
| GET | /controls | List controls and coverage | JWT | viewer/auditor/manager | ?riskId=UUID&limit=20 | 200 {data:[{id,code,title,expectation}],nextCursor} | 400,401,403 |
| GET | /dashboard | Summarize tested scope | JWT | viewer/auditor/manager | ?runId=UUID | 200 {runStatus,coverage,exceptions,findingsBySeverity} | 400,401,403,404 |

## Contract conventions
JSON request/response bodies; UUID identifiers; ISO 8601 UTC timestamps; money serialized as decimal strings. Lists default to 20 and cap at 100 with opaque cursors. Validate identifiers, allowed fields and filters. 400 means malformed input, 401 missing/invalid identity, 403 insufficient access, 404 unavailable resource, 409 stale state/idempotency conflict, 422 invalid business semantics, 429 throttled and 503 unavailable run capacity. Internal failures use 500 with generic detail.

Current Hapi errors use {statusCode,error,message}. Future errors retain that envelope and add an optional requestId; no stack traces, tokens or SQL. Object-level checks apply in addition to role checks. Redact evidence from viewer responses. Risk/control mutations and source-user endpoints are deferred.

Run requests must freeze exact test versions; identical idempotency keys with the same payload return the existing run, while changed payloads conflict. The 202 contract cannot be implemented until durable scheduling exists. Phase 0 does not return fake queued runs. Health does not check PostgreSQL or imply readiness.

