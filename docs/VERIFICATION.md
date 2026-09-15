# Verification record

## Rule Pack v1 integration - 2026-09-15 Asia/Jakarta (current)

Resumed existing changes; framework remains 0.3.0. No new detector, algorithm,
hash contract or source schema. The canonical [policy](../audit-engine/policies/rulepack-v1.json)
composes the five previously verified configurations. See [integration](RULE-PACK-V1.md)
and [production runbook](PRODUCTION-RUNBOOK.md).

### Local Verification

| Check | Actual result |
| --- | --- |
| Full Python suite | PASS: 366 tests in 240.57s; all 357 previous tests plus 9 integration cases |
| Focused integration suite | PASS: 9 tests in 20.70s |
| Node suite | PASS: 19 tests, including startup/environment sanitization |
| Production Web build | PASS: environment-provided API_URL, 26 modules |
| Legacy CLI, health, registry | PASS: actual subprocess commands |
| Default/examples and all five individual policies | PASS: CLI validation, execution, snapshot/result inspection |
| Controlled integrated run | PASS: five results, six findings, nine evidence items |
| Ordering and isolation | PASS: individual logical outputs equal integrated components; source row/key and policy key order invariant; shared frozen context unchanged |
| Logical hash sensitivity | PASS: config, source value, version, finding and evidence changes |
| Strict/partial failure | PASS: exception/missing-field cases; prior results retained; strict later skips; partial later execution; run remains failed |
| Artifacts/provenance | PASS: policy ID/version, all resolved versions/configs, snapshot reference/hash, logical hash, status and existing atomic/no-clobber writes |
| Readiness helper | PASS: snapshot/schema/registry/policy validation and actual atomic output probe; bad ID rejected; probes cleaned |
| API npm start | PASS: repository root and apps/api; migrations first, live health, owned processes stopped |
| Web npm start | PASS: repository root and apps/web; live index, owned processes stopped |
| Documentation/whitespace | PASS: schema parity, 50 Markdown files, 195 relative links, 15 Mermaid diagrams; git diff --check clean |

Controlled expected = actual findings: amount 1, duplicate payment 1, duplicate
reference 1, completeness 2, sequence 1. Eleven tables contain five invoices, eight
payments and nine empty tables. This is a snapshot-contract fixture, not a database
seed. Logical hash:
`8893bf4a40f24d85d545124bb1da878c3228636f59c927a73e60b92d3a1dfb55`.
All seven existing detector goldens remain compatible. The resumed diffs for
default/examples/business-rulepack-v1 policies are formatting-only; JSON values and
normalized serialization are unchanged. CLI evidence and inspectable runs are retained
locally under ignored `audit-engine/artifacts/rulepack-verification`.

Runtime uses the project-local Knex module, module-relative migration paths and
sanitized startup messages. Production API requires DATABASE_URL; development health
defaults remain. No Web configuration semantics or API endpoints changed. Health is
liveness only. Trusted detectors receive frozen context/config, not connections or
credentials; this interface is not an OS sandbox.

### Disposable PostgreSQL Verification

PASS, report **2026-09-15T04:17:16.229Z UTC**: PostgreSQL 17.5; 15 framework checks;
11 tables; 19,654 records; seven constraint checks; 17 reader denials (42501), plus
SELECT on all approved tables. Production API start from both directories and
idempotent migrations passed. Source hashes remained unchanged, audit schema stayed
empty and the private cluster stopped successfully.

| Integrated detector | Input | Evaluated population | Findings | Result |
| --- | ---: | ---: | ---: | --- |
| business.amount_outlier | 2,400 | 2,400 | 122 | findings |
| business.duplicate_payment | 2,400 | 2,400 | 0 | passed |
| business.duplicate_transaction_reference | 2,000 | 2,000 | 0 | passed |
| business.missing_required_field | 2,000 | 2,000 | 0 | passed |
| business.sequence_gap | 2,000 | Not completed | 0 | error / detector_error |

**Framework acceptance PASS is separate from five-rule business compatibility.**
The strict integrated source run is `failed`: sequence requires integer values while
the source has prefixed text references. No source coercion, substitution or detector
weakening occurred. Four compatible results match individual logical outputs exactly.
Sequence is last, so no later controls exist to skip here; controlled failure tests
prove later skips separately. A controlled snapshot run in the same acceptance
environment completed all five controls with the canonical hash above.

Amount evaluation retained 2,400 eligible records, one currency group and one group
meeting sample size eight; all 122 upper findings matched independently computed IDs.
Zero findings in the other compatible controls are valid.

Initial infrastructure failures: initdb reported Windows restricted-token errors 87/3.
The established isolated runner passed with permitted broader process permissions.
A Web smoke run could not stop its owned npm tree in the restricted context; only
identified test processes were stopped, cleanup gained bounded failure handling, and
the broader-process rerun passed. No application permissions or grants were weakened.
A single invalid CP1252 dash in historical verification text was repaired to UTF-8.

### Production/Railway Verification

No Railway CLI, configured Railway environment, public deployment URLs or authenticated
browser session was available. Local results do not establish Railway deployment.

| Railway check | Status | Evidence/reason |
| --- | --- | --- |
| Build | NOT RUN | No project/deployment access |
| Startup | NOT RUN | No remote runtime access |
| API health | NOT RUN | No public API URL |
| Web health | NOT RUN | No public Web URL |
| DB connectivity | NOT RUN | No authorized remote DB context |
| Migrations | NOT RUN | Disposable execution only |
| Web → API | NOT RUN | No URLs; current UI has no real API call |
| Engine health | NOT RUN | No deployed Python CLI environment |
| Rule Pack validation | NOT RUN | Local CLI only |
| Rule Pack execution | NOT RUN | Controlled local run only |
| Artifact creation | NOT RUN | No Railway audit run |
| Artifact inspection | NOT RUN | No Railway artifacts |
| Read-only source | NOT RUN | Remote grants uninspected; disposable denials verified |

Build context remains repository root for the shared lockfile. Service-directory
commands also work after dependencies are installed; an isolated Railway subdirectory
install was not verified. No Railway Volume or external storage is configured here.
Unmounted container artifacts are ephemeral; actual remote mounts are unverified.
No production source was modified and no Git commit was executed.

Phase 0 verified locally; Phase 1 verified on disposable PostgreSQL; Rule Pack v1
integrated on controlled snapshots; production commands verified locally. Railway
build/runtime and production audit execution NOT RUN. Persistence/orchestration and
real audit UI are not started. Recommended next phase: **Audit Run persistence +
Node API orchestration**, the bridge before UI can display real runs/findings.

## Amount outlier rule - 2026-09-15 Asia/Jakarta (previous phase)

Added only `business.amount_outlier` 1.0.0, category `monetary_anomaly`, rule
`AMOUNT_OUTLIER`, medium severity. Framework remains 0.3.0. Existing string/list/
integer/boolean configuration, requirements_for, frozen contracts, normal policy CLI
and canonical normalization/hashing are reused. No schema, dependency, previous
policy or security boundary changed. The [statistical contract](AUDIT-RULE-PACK.md#statistical-control-businessamount_outlier)
is Decimal-only Tukey median-of-halves IQR, strict comparisons, and zero findings
for small or zero-IQR groups. Existing ADR boundary/contract practices were inspected;
this versioned rule convention belongs in the rule guide, without a new ADR.

| Executed check | Result |
| --- | --- |
| Initial focused amount-outlier tests | 95 passed, 1 failed in 66.33s; fixture correction below |
| `audit-engine/.venv/Scripts/python.exe -m pytest` | PASS: 357 passed in 199.32s; all 261 previous tests plus 96 new cases |
| New normal CLI subprocess cases | PASS: 11 scenarios covering policy validation/run/result inspection, upper/lower, reordered, sample-size, zero-IQR, null, zero, negative, exact decimals and invalid amount/config |
| Separate grouped CLI exercise | PASS: two findings, independent IDR/USD populations of eight records each |
| `npm test` | PASS: 17 passed, 0 failed |
| `$env:API_URL='http://localhost:3001'; npm run build` | PASS: production build, 26 modules |
| CLI no arguments, health, detector inspection | PASS: actual commands; legacy Pandas health 3.0.5 unchanged |
| Population/input/config tests | PASS: full-table, currency/composite grouping, null/empty/zero/false distinction, per-group minimum, requirements and sanitized errors |
| Decimal tests | PASS: exact odd/even quartiles, serializer, cent/sub-cent statistics, high precision, huge amounts, hostile ambient precision/rounding/traps |
| Separate large shifted-cent calculation | PASS: exact sub-cent quartiles near 999999999999999999.00 with caller precision 3 and Inexact trap |
| Determinism and secret sentinels | PASS: row/key order, run/snapshot IDs, timestamps, operator/root invariance; environment sentinel absent from artifacts |
| Hash sensitivity | PASS: amount/record ID, grouping, multiplier, minimum sample, zero/negative/direction flags, version, finding/evidence mutations |
| All six previous detector goldens | PASS: health, snapshot integrity, reference, completeness, sequence and duplicate payment |
| `$env:PG_BIN='C:/Program Files/PostgreSQL/17/bin'; npm run test:db` | PASS after broader-process retry; PostgreSQL 17.5; report 2026-09-14T23:37:12.307Z UTC |
| PostgreSQL framework acceptance | PASS: 13 checks, 11 tables, 19,654 records |
| PostgreSQL amount control | PASS: 2,400 evaluated/eligible records, one currency group, one group meeting minimum eight, 122 upper findings at multiplier 1.5 |
| Independent PostgreSQL expected IDs | PASS: separately calculated quartiles/fences match all 122 records and their minimal evidence |
| Source/reader boundary | PASS: unchanged source hashes, seven constraints, SELECT and seventeen denials; audit schema empty |
| Disposable cluster shutdown | PASS: runner stopped its private cluster; diagnostics retained |
| `npm run docs:check` | PASS final rerun: schema parity, 48 Markdown files, 178 relative links, 15 Mermaid diagrams |
| `git diff --check` | PASS final rerun |

Initial failures and corrections: the boundary fixture initially included 4 in its
upper half, making the actual fences -2.75 and 7.25 rather than intended -2 and 6.
Both equality and just-outside fixtures were corrected to use 3, yielding Q1=1 and
Q3=3. Exact boundaries then produce zero findings and one-cent crossings produce two.
The focused diagnostic reproduced the same fixture error; no algorithm change was
required. initdb initially failed with Windows restricted-token errors 87/3 before
acceptance ran. The same disposable runner passed with broader process permissions;
it ignores existing DATABASE_URL targets and creates/stops its own private cluster.
No source grant or permission policy was weakened.

The real approved exported payment population was inspected: all 2,400 monetary
values were exact strings and eligible. Currency grouping avoids mixed denominations;
the actual data has one group. The default multiplier was not tuned to produce the
122 findings. These are statistical review candidates, not confirmed error or fraud.
Real duplicate-payment findings remain zero. Sequence acceptance retains actual
registration/policy/schema checks; positive numeric sequence evaluation is offline.

The controlled amount fixture has eight payments, ten empty tables, one upper finding
and one evidence item. Payment amounts retain the existing fixed two-decimal snapshot
representation. The unchanged loader rejects null/non-cent payment amounts; nullable,
high-precision and invalid detector inputs use a configurable reference field allowed
by the existing scalar schema. Snapshot validation was not weakened. Statistics keep
at least two decimal places and any necessary sub-cent digits; original money remains
exact. The detector receives no new source, environment, network or storage authority.

Before editing, the payment golden was rerun and captured with exact policy/config
JSON. Its unchanged hash is
`371fd9dba0a759877b8f42cdfba0d55cae87794e27ff663895c597334e926f7d`.
The amount fixture logical hash is
`cc201df7104ab2c7fc2ba2a0dd9505cf7419aa4064cbb61fab71a5cc4c21e50e`.
All old tests remain intact. No Git commit was executed.

Phase status: Phase 0 verified locally; Phase 1 verified on disposable PostgreSQL;
Local CLI Audit Framework, SDK/policy, Rule Pack v1 foundation, duplicate reference,
completeness, sequence integrity, duplicate payment and amount outlier complete for
local acceptance. Advanced contextual rules not started; Production/Railway unverified.
Recommend Rule Pack v1 integration and production-readiness; no follow-on detector
or deployment was implemented.



## Duplicate payment rule - 2026-09-15 Asia/Jakarta (previous phase)

Added only `business.duplicate_payment` 1.0.0, category payment_integrity, using
existing list[string] configuration and requirements_for. Framework remains 0.3.0.
No SDK/config primitive, frozen contract, hash algorithm, artifact layout, source
schema, default policy or existing business policy changed. See
[payment semantics and examples](AUDIT-RULE-PACK.md#payment-control-businessduplicate_payment).

| Executed check | Result |
| --- | --- |
| New payment tests | PASS: 53 tests; initial focused run 42.63s |
| `audit-engine/.venv/Scripts/python.exe -m pytest` | PASS: 261 passed in 186.19s; all 208 prior tests retained plus 53 new tests |
| Final CLI/fixture assertions | PASS: 10 passed, 43 deselected in 47.63s after adding explicit CLI logical-hash checks |
| `npm test` | PASS: 17 passed, 0 failed |
| `$env:API_URL='http://localhost:3001'; npm run build` | PASS: Vite production build, 26 modules |
| CLI no arguments, health, detector inspection | PASS: actual commands; legacy health returns ok, Pandas 3.0.5 |
| Payment policy validation/run/result inspection | PASS: positive, unique, reordered, case-sensitive/insensitive, empty ignored/participating, invalid config and missing requirement subprocess cases |
| Requirements and configuration | PASS: at least two unique fields; malformed types/names; missing table/ID/match fields before analysis, including empty tables |
| Exact value semantics | PASS: scalar type distinction, Unicode casefold, whitespace preservation, null versus empty, space/zero/false/arrays/objects are not empty; nested object order and array order |
| Grouping and evidence | PASS: one finding per group, all participating records, canonical order, original values and no unrelated columns |
| Reproducibility | PASS: direct reordered frozen context and snapshot executions; record/key order, run/snapshot artifact IDs, timestamps, operator and artifact root invariance |
| Hash sensitivity | PASS: match values, participating IDs, ordered fields, both boolean settings, version, finding and evidence mutations |
| `$env:PG_BIN='C:/Program Files/PostgreSQL/17/bin'; npm run test:db` | PASS after broader-process retry: PostgreSQL 17.5, report 2026-09-14T23:21:58.293Z UTC |
| PostgreSQL framework acceptance | PASS: 12 checks, 11 tables, 19,654 records |
| PostgreSQL payment control | PASS: registration, policy, schema and offline execution from exported snapshot; 0 actual duplicate groups for invoice_id + amount + currency + reference |
| PostgreSQL constraints and reader boundary | PASS: seven constraints, SELECT and seventeen denials; all source hashes unchanged, audit schema empty |
| Disposable cluster shutdown | PASS: runner stopped the cluster; temporary diagnostics retained |
| `npm run docs:check` | PASS: schema parity, 48 Markdown files, 173 relative links, 15 Mermaid diagrams |
| `git diff --check` | PASS: final check |

The approved payments table has invoice_id, amount, currency and reference, but no
vendor_id. Currency is included to avoid comparing equal amounts in different
currencies. The real 2,400-payment dataset had zero exact composite duplicates;
this is not a claim of positive PostgreSQL duplicate findings. The controlled offline
fixture has three payments, ten empty tables, one duplicate group and two evidence
items. It uses the existing snapshot inventory and canonical money strings.

A sequence golden was captured before detector registration changed and protects its
policy/config JSON and logical hash. Existing health/default, snapshot-integrity,
duplicate-reference and completeness goldens and tests remain intact. No old tests
were removed or weakened. A payment logical golden additionally protects reordered
CLI output. The checked-in example uses fixed snapshot/run identities and timestamps.

Initial failure and correction: restricted execution of initdb failed with Windows
restricted-token errors 87/3 and a directory-creation error before acceptance ran.
The same existing disposable runner passed with broader process permissions. It
ignores existing DATABASE_URL targets, creates a private temporary cluster and stops
it afterward. No database permissions were weakened. No detector test failures were
observed. During artifact review the example's transient snapshot ID was replaced
with the controlled fixture ID; logical content and its hash were unaffected.

Matching uses hash-map construction, approximately O(n × f) for bounded values plus
canonical sorting, never pairwise O(n²). Nested JSON cost depends on value size and
object-key sorting. Execution still passes only frozen AuditContext and validated
DetectorConfig; no database, filesystem, network, credential or subprocess access
was added. Python and Node secret-sentinel checks remain in coverage.

Phase status: Phase 0 verified locally; Phase 1 verified on disposable PostgreSQL;
Local CLI Audit Framework, Audit Policy + Detector SDK, Rule Pack v1 foundation,
duplicate-reference, completeness, sequence integrity and duplicate payment complete. Advanced/statistical rules not started;
Production/Railway unverified. Recommend only business.amount_outlier next, after
specifying its deterministic algorithm, population, monetary arithmetic, thresholds,
ties and minimum sample size. No commits or deployments executed.

## Sequence integrity rule - 2026-09-15 Asia/Jakarta (current)

Resumed and reviewed the existing workspace implementation; no restart or redesign.
Added only `business.sequence_gap` 1.0.0, category sequence_integrity. Framework remains
0.3.0. SDK addition is `optional_integer` (exact integer or null; excludes boolean).
Frozen snapshot/result/policy shapes, artifact layout and provenance are unchanged.
See [sequence semantics, policy and result](AUDIT-RULE-PACK.md#sequence-control-businesssequence_gap).

| Executed check | Result |
| --- | --- |
| `audit-engine/.venv/Scripts/python.exe -m pytest` | PASS: final rerun 208 passed in 98.94s; previous 148 tests retained, 60 sequence regressions added |
| `npm test` | PASS: 17 passed, 0 failed, including browser and server secret-sentinel checks |
| `$env:API_URL='http://localhost:3001'; npm run build` | PASS: Vite production build, 26 modules |
| `python -m audit_engine --help`, no arguments, `health`, `detectors list`, `detectors inspect business.sequence_gap` | PASS: actual subprocess commands; five explicit registrations, legacy health unchanged |
| `python -m audit_engine policy validate audit-engine/policies/sequence-gap.json` | PASS: actual normal policy CLI |
| Sequence CLI `run --snapshot ... --policy ...` and `result inspect ...` | PASS: positive, complete, explicit bounds, invalid bounds, boolean/string values, duplicate forbidden, billion-wide range; expected error exits verified |
| Reordered offline fixture CLI | PASS: same logical result/hash and checked-in canonical result; two ranges (3 and 5-7) |
| Requirements and input validation | PASS: missing table/ID/sequence field before analysis; invalid config before artifacts; bool/float/string/nested rejection; deterministic sanitized errors |
| Empty populations and bounds | PASS: no bounds or one bound yields zero findings; both bounds yield full-range finding with empty evidence; equal/negative/clipped bounds covered |
| Boundary evidence | PASS: nearest before/after records; smallest canonical identity for duplicate boundaries; at most two evidence items, no copied rows |
| Large-range memory | PASS: 1 and 1,000,000,000 yield one range 2-999999999; measured detector peak allocations below 1 MB |
| Reproducibility | PASS: record/key order, run/snapshot artifact IDs, timestamp, operator and root invariance; direct shuffled context and reordered CLI tested |
| Hash sensitivity | PASS: observed values, gap range, minimum, maximum, allow_duplicates, detector version, finding and evidence changes |
| Compatibility | PASS: default/health, snapshot-integrity, duplicate-reference and completeness golden hashes; old scalar/list config serialization; legacy CLI, prior policies and old example artifacts |
| `$env:PG_BIN='C:/Program Files/PostgreSQL/17/bin'; npm run test:db` | PASS after broader-process retry: PostgreSQL 17.5, report 2026-09-14T22:54:12.503Z UTC |
| PostgreSQL framework acceptance | PASS: 11 checks, 11 tables, 19,654 records; source hashes unchanged after extraction |
| PostgreSQL constraints and permissions | PASS: seven constraint cases, SELECT and seventeen permission denials; source hashes unchanged and audit schema empty |
| Disposable cluster shutdown | PASS: runner reported Disposable cluster stopped; diagnostic files retained in its temporary directory |
| `npm run docs:check` | PASS: schema parity, 48 Markdown files, 170 relative links and 15 Mermaid diagrams |
| `git diff --check` | PASS after correcting documentation line endings |

PostgreSQL scope for the sequence rule is registration, policy validation and schema
compatibility. Its real reference column contains strings, so this is not claimed as
positive numeric business-sequence detection. Controlled offline integer references
use the approved snapshot contract; the committed fixture has four invoices and ten
empty tables. Positive detection, errors and reordered hashes are verified through
the normal CLI without adding a sequence-specific command.

The completeness golden was captured before changing SDK/execution code. It protects
policy JSON, effective list/scalar configuration JSON and the logical run hash.
Existing default/boolean/integer and duplicate-reference golden tests remain intact.
No prior tests were removed or weakened. Both full Python runs passed at 208 tests.

Initial failures and corrections: the first PostgreSQL invocation failed in initdb
with Windows restricted-token errors 87/3 (and directory creation failure), before
acceptance ran. The same disposable runner succeeded with broader process permissions;
application permissions and source-reader restrictions were not weakened. An initial
documentation edit encountered a legacy non-UTF-8 multiplication byte, then a diff
check detected doubled carriage returns/trailing whitespace. The rule guide was
re-encoded correctly with normal line endings and its original Unicode retained.
These were documentation editing issues; no detector test failed.

Security remains trusted in-process execution with only frozen AuditContext and
validated DetectorConfig passed to the detector. No database, credentials, environment,
filesystem, network, shell, subprocess or dynamic loading capability was added.

Phase status: Phase 0 verified locally; Phase 1 verified on disposable PostgreSQL;
Local CLI Audit Framework, Audit Policy + Detector SDK, Rule Pack v1 foundation,
duplicate-reference, completeness and sequence integrity complete. Advanced business
rules are not started. Production/Railway remains unverified. Recommended next rule:
`business.duplicate_payment`; not implemented. No Git commits were executed.

## Completeness rule — 2026-09-15 Asia/Jakarta (current)

Added only `business.missing_required_field` 1.0.0, category data_completeness.
Framework remains 0.3.0. SDK change: bounded list[string] configuration using the
existing frozen array representation. No result/snapshot/policy contract changes,
new dependencies, source schema changes, production changes or Git commits.
See [rule details and examples](AUDIT-RULE-PACK.md#completeness-control-businessmissing_required_field).

| Executed check | Result |
| --- | --- |
| `audit-engine/.venv/Scripts/python.exe -m pytest` | PASS: 148 passed; all previous 112 retained, 36 new completeness regressions |
| `npm test` | PASS: 17 passed, 0 failed |
| `$env:API_URL='http://localhost:3001'; npm run build` | PASS: Vite production build, 26 modules |
| CLI no arguments / health / detector inspect / policy validate | PASS: actual commands |
| Legacy no-policy / framework policy / duplicate-reference CLI | PASS: retained subprocess tests; existing behavior unchanged |
| Completeness positive / negative / invalid config / missing field / reordered CLI | PASS: actual subprocess tests through normal policy run/result inspection |
| Offline completeness fixture | PASS: three invoices, two findings, three evidence items; checked-in result compared against reordered CLI executions |
| Configuration and requirements | PASS: malformed lists/types, empty/duplicate fields, missing table/ID/required field; analysis not called, including empty tables |
| Missing-value semantics | PASS: null, configurable empty strings, multiple missing fields, complete rows, whitespace, zero, false, arrays and objects |
| Reproducibility and sensitivity | PASS: row/key order, artifact roots, operator, snapshot/run IDs and time invariant; record/presence/config/version/finding/evidence mutations change SHA-256 |
| Prior serialization and logical hashes | PASS: retained default/boolean/integer golden baselines plus pre-edit duplicate-reference policy, effective scalar configuration and hash |
| `$env:PG_BIN='C:/Program Files/PostgreSQL/17/bin'; npm run test:db` | PASS: PostgreSQL 17.5; report 2026-09-14T22:40:04.134Z UTC; disposable cluster stopped |
| PostgreSQL framework acceptance | PASS: 10 checks, 11 tables, 19,654 records; both business policies, offline source isolation, evidence comparison and tamper rejection |
| PostgreSQL constraints / privileges / integrity | PASS: seven constraint cases, reader SELECT and seventeen denials; source hashes unchanged; audit schema empty |
| `npm run docs:check` | PASS: schema parity, 48 Markdown files, 166 relative links, 15 Mermaid diagrams |
| `git diff --check` | PASS: no whitespace errors |

The duplicate-reference baseline was captured from the unchanged working tree before
editing the SDK, using the existing business snapshot and policy. The verified hash
is `0498dd5b110d7ecb3f3364f76f623123befc549e9ba2e2a6347a2f3dec81f932`.

The first Python run reported 147 passed and one failure in a new test assertion:
it omitted the existing DetectorConfig values wrapper. Correcting that assertion
produced the full passing run; no previous test was weakened or deleted.
The first PostgreSQL attempt hit the known Windows restricted-token initdb failure;
the disposable runner was retried with broader process permissions.

Secret-sentinel regressions pass. Detector execution still receives only frozen
AuditContext and validated DetectorConfig, with no new privileged capability.
Record summary metadata lives once in the first canonical evidence context, avoiding
contract changes and quadratic field-list repetition. Current limitations remain
approved inventory, string record identities, unconditional requirements, trusted
in-process execution and unsigned whole-snapshot logical checksums.


## Audit Rule Pack v1 Foundation — 2026-09-15 Asia/Jakarta (current)

Implemented exactly one business detector: `business.duplicate_transaction_reference`
version 1.0.0, category transaction_integrity. Framework remains 0.3.0. The existing
SDK gained string configuration and an optional configured-requirements method;
snapshot, result, policy shapes, source schema and hash algorithm are unchanged.
See [rule semantics, fixture and limitations](AUDIT-RULE-PACK.md).

| Executed check | Result | Evidence |
| --- | --- | --- |
| `audit-engine/.venv/Scripts/python.exe -m pytest` | PASS: 112 passed, 0 failed | All 79 pre-existing tests retained; 33 new business regressions |
| `npm test` | PASS: 17 passed, 0 failed | Existing Node suite and secret-sentinel build tests |
| `$env:API_URL='http://localhost:3001'; npm run build` | PASS | Vite production build, 26 modules |
| CLI no arguments / help / health | PASS | Actual subprocess commands; existing health JSON and no-policy behavior retained |
| CLI detector inspect / policy validate | PASS | Business metadata, business example policy and unchanged default policy |
| Offline fixture snapshot inspect / policy run / result inspect | PASS | Actual CLI; 1 finding, 2 evidence records; checked-in canonical example result |
| Positive / unique / reordered CLI fixtures | PASS | Actual subprocess regression tests; unchanged logical hash for reordered input |
| Invalid configuration / missing-field CLI fixtures | PASS | Expected exit 1; invalid config creates no runs; missing field records skipped result and failed run |
| Missing table / ID field / reference field | PASS | Compatibility errors before analyze, including empty tables |
| Logical reproducibility and sensitivity | PASS | Row/dictionary order, root, operator, IDs, timestamps invariant; reference, record IDs, version, config, finding and evidence mutations change hash |
| Old boolean/integer policy serialization and logical hashes | PASS | Golden values produced using pre-change SDK/execution from Git 52c8b72887480894929cd54e69ccd18e261ae140, then compared against new execution |
| `$env:PG_BIN='C:/Program Files/PostgreSQL/17/bin'; npm run test:db` | PASS | PostgreSQL 17.5; final report 2026-09-14T22:23:54.876Z UTC |
| PostgreSQL framework acceptance | PASS: 9 checks | Eleven tables, 19,654 records, reader extraction twice, legacy/framework/business policy paths, offline source isolation and tamper rejection |
| PostgreSQL constraints, privileges and integrity | PASS | Seven constraint cases; reader SELECT and seventeen denials; source fixture hashes unchanged; audit schema empty |
| `npm run docs:check` | PASS | Schema parity and Markdown links/diagrams validated |
| `git diff --check` | PASS | No whitespace errors |

PostgreSQL's existing synthetic invoice anomalies intentionally change whitespace
and case. Under this rule's exact-reference semantics the business policy correctly
returns zero findings on that exported dataset. Positive duplicate findings and full
record evidence are verified with the checked-in offline snapshot and CLI regression
fixtures, not claimed as positive PostgreSQL detections. Existing generator and
benchmark labels/hashes were not changed.

Initial attempts: the first Python run caught a requirements-hook name collision
with an existing test detector (12 failed, 98 passed). Renaming the optional method
to `requirements_for` fixed the implementation without changing old tests. Subsequent
runs passed (111, then 112 after adding the checked-in-result/reordered CLI regression).
The sandboxed PostgreSQL attempt failed at initdb's Windows restricted token creation.
An authorized broader-process run reached the new acceptance test and caught its
incorrect assumption that existing whitespace-modified benchmark references must
match. That new assertion was corrected to follow the specified exact semantics;
the full subsequent disposable acceptance passed and stopped its cluster. No
application security settings were relaxed and no external database was targeted.

The rule receives only frozen context and validated config, with no DB/environment/
filesystem/network access. Existing secret-leakage tests and new business-run secret
sentinels pass. No new runtime dependencies, source writes, contract/version bumps,
authentication, production deployment or Git commits were introduced.

Phase 0: Verified locally. Phase 1: Verified on disposable PostgreSQL.
Local CLI Audit Framework: Complete. Audit Policy + Detector SDK: Complete.
Audit Rule Pack v1 Foundation: Complete. Additional Business Rules: Not started.
Production/Railway verification: Unverified.

## Audit Policy + Detector SDK — 2026-09-15 Asia/Jakarta (historical)

Completed incrementally on the existing working tree, framework version 0.3.0.
No business detectors, production migrations, authentication or Railway changes.
Continuation added deterministic policy-validation order, explicit finding-hash
mutation, artifact-root/operator/snapshot-identity equivalence and CLI secret-sentinel
tests; prior SDK, lifecycle, contracts and documentation were retained.

| Executed check | Result | Evidence |
| --- | --- | --- |
| Python: .venv Python -m pytest audit-engine/tests -v | PASS: 79 passed, 0 failed | Also 15 unittest subtests passed; all 30 original tests retained |
| npm test | PASS: 17 passed, 0 failed | Full existing Node suite rerun |
| npm run build --workspace @auditlens/web | PASS | API_URL=http://localhost:3001; Vite production assets built |
| CLI help / no arguments / health | PASS | Existing health JSON retained |
| detectors list / inspect | PASS | Two explicit versioned framework detectors |
| policy validate default.json | PASS | Explicit health-only default policy |
| End-to-end execution | PASS | Supported snapshot CLI, snapshot inspect, legacy health run/result and two-detector policy run/result on disposable PostgreSQL |
| npm run test:db | PASS | PostgreSQL 17.5; report 2026-09-14T22:05:37.269Z UTC |
| Framework acceptance | PASS: 8 checks | 11 tables, 19,654 records; multi-detector evidence and offline source isolation |
| Source integrity and privilege denials | PASS | Existing source hashes unchanged; audit schema empty; existing constraints/reader denials pass |
| npm run docs:check | PASS | 46 Markdown files, 152 relative links, 15 Mermaid diagrams |
| git diff --check | PASS | No whitespace errors |

The initial sandboxed PostgreSQL attempt failed because initdb could not create a
Windows restricted process token. The same disposable-only runner succeeded with
broader process permissions; continuation reran that successful mechanism. No
application security settings were relaxed and no external target was used.
The runner shuts down its private cluster and retains temporary diagnostic files.
The first web build attempt lacked API_URL; subsequent explicit local-URL builds
passed. pytest was installed only into the project virtual environment; it is an
optional test extra, not a new runtime dependency or global installation.

The logical result checksum is unsigned and is not automatically recomputed by
result inspect. Detectors remain trusted in-process modules with a frozen argument
boundary, not OS isolation. See [Detector SDK](DETECTOR-SDK.md) and
[ADR-010](adr/ADR-010-detector-sdk-and-audit-policy.md) for actual limitations.
Business Detectors: Not started. Production/Railway verification: Unverified.

## Local CLI Audit Framework — 2026-09-15 Asia/Jakarta (historical)

Implemented and locally verified: typed extraction/snapshot/run/provenance/result/
finding/evidence/context contracts; eleven-table read-only extraction; canonical
JSONL snapshots and hashes; independent integrity validation; immutable context;
local run/provenance/result artifacts; health smoke execution only. No business
detector, authentication, API result persistence or Railway change was made.

| Executed check | Result | Evidence |
| --- | --- | --- |
| npm test | PASS: 17 passed, 0 failed | Existing API, dataset, guards, static serving and enhanced app/env-probe reader-secret isolation |
| npm run build | PASS | API_URL=http://localhost:3001; actual Vite production output generated |
| npm run docs:check | PASS | Compiled migration/dictionary/ERD parity; 43 Markdown files, 145 relative links, 14 Mermaid diagrams |
| Python unittest discover -s audit-engine/tests | PASS: 30 passed, 0 failed | Existing health plus 29 framework tests, including contracts, determinism, integrity, safety, failure lifecycle and CLI |
| python -m audit_engine --help | PASS | Four command groups and artifact-root option printed |
| python -m audit_engine health | PASS | status ok, service auditlens-engine, Pandas 3.0.5 |
| python -m audit_engine | PASS | Original no-argument health behavior retained |
| npm run test:db | PASS | Full disposable PostgreSQL 17.5 acceptance, including Python snapshot/inspect/run/result CLI; final completion 2026-09-14T17:12:52.037Z |
| db:inspect / db:status / db:validate-data | PASS inside acceptance | Real read-only empty inspection/readiness plus populated fixture validation; no configured external target used |
| Reader extraction | PASS | Two exports through authenticated non-superuser login selecting auditlens_source_reader; eleven tables, 19,654 rows |
| Logical determinism | PASS | Both exports: ee36c5de51c49c3eac8828327e67e913206b47eef3ad97c4d23731ca6b389cd8 |
| Source integrity | PASS | Existing fixture hash ce8a804cea5a71bba995530d06dab875433d61faf149ac2bf9ab298284a906f2 and every fixture table hash unchanged after extraction |
| Offline execution / result | PASS | Real CLI run with both database URL variables deliberately unusable; framework.health passed, zero findings; result inspect succeeded |
| Tamper rejection | PASS | Modified live exported snapshot rejected by CLI before execution; offline tests also cover counts, metadata, missing files and hashes |
| PostgreSQL constraints / privileges | PASS | Seven constraint cases and seventeen reader denial cases; approved SELECT succeeds; audit schema stays empty |
| Secrets and labels | PASS | Reader URL/password absent from temporary artifacts; source URL errors sanitized; runtime import regression excludes synthetic labels/generators; Web sentinel tests pass |
| Artifact Git exclusion / whitespace | PASS | git check-ignore confirms default runtime path; git diff --check succeeds |

The first sandboxed test:db attempt failed at initdb's Windows restricted-token
creation (error 87), before migration/extraction. Broader-process runs of the same
self-contained runner passed and stopped their private clusters. No existing database
URL was targeted. Test snapshots/results were temporary and removed by the harness;
stopped cluster files remain in OS temporary storage for diagnosis. Node 22.14.0,
Python 3.12.14 and PostgreSQL 17.5 are the local environment inherited from stabilization.

Snapshot hash differs from the fixture hash by design: the new versioned JSONL/
UTC-microsecond/manifest contract is independent of generator serialization.
Run IDs and timestamps intentionally differ on replay; semantic health output
and content hashes are reproducible. Integrity is not an authenticated signature.

Requires configured PostgreSQL: routine operator snapshot creation needs a separately
authorized reader login/URL and existing grants. Disposable extraction is verified;
no claim is made about any external or production reader identity.

Requires Railway verification: deployed runtime, settings, production grants and
remote audit access remain unverified. Railway was not modified. Phase 0: verified
locally. Phase 1: verified on disposable PostgreSQL. Stabilization: complete locally.
Local CLI Audit Framework: implemented and locally verified. Next: Audit Policy +
Detector SDK. See [framework specification](AUDIT-FRAMEWORK.md) and
[ADR-009](adr/ADR-009-snapshot-based-audit-execution.md).

The older milestone records below are historical and retain their original counts.

## Stabilization acceptance — 2026-09-14 (historical)

This section is the current factual record; all older snapshots below are historical. **Phase 0: VERIFIED locally. Phase 1: VERIFIED on disposable PostgreSQL. Stabilization: COMPLETE for repository/local acceptance. Ready for the next local CLI Audit Framework milestone, after its documented design decisions; framework implementation has not begun.** Railway dashboard/runtime evidence remains NOT VERIFIABLE, independently of the local pass.

Environment: Windows, Node.js 22.14.0, Python 3.12.14 / Pandas 3.0.5, PostgreSQL 17.5 (x86_64-windows). No existing DATABASE_URL or .env was used. The working tree already contained review/path/documentation edits at the start; these were preserved. No Git commit, Railway deployment, existing-database migration or production privilege change was made.

| Command/check | Result | What actually ran |
| --- | --- | --- |
| npm test | PASSED — 17/17 | API/config, fixture parity/QA, local guards, real HTTP serving and app/env-probe bundle secrecy; rerun after database changes; final root-serving adjustment also passed tests/web.test.js (2/2) |
| API health/404/500 | PASSED | Hapi injection plus loopback health HTTP; sanitized internal error, no foreign-Origin CORS header |
| API payload/shutdown | PASSED | Test-only payload route rejects >1 MiB with 413; started server stops cleanly; no application endpoints added |
| PORT cases | PASSED | 3001/8080 accepted; 0/65536/abc/3001.5 rejected; default 3001 |
| npm run build | PASSED | API_URL=http://localhost:3001, no WEB_ALLOWED_HOST needed; Vite production assets emitted |
| Production dist HTTP | PASSED | Actual built index/assets entrypoint served at /, /audit-tests and /findings through apps/web/server.js |
| Web static server tests | PASSED | Root, nested navigation, HEAD, JS MIME, missing asset 404, dot/traversal paths, malformed encoding and method rejection |
| Secret boundary | PASSED | Actual application and explicit import.meta.env probe exclude database/JWT/unrelated prefixed sentinels while retaining public API_URL |
| npm run docs:check | PASSED | Final rerun: generated DDL parity, 41 Markdown files, 121 relative links and 13 Mermaid diagrams |
| audit-engine/.venv/Scripts/python.exe -m unittest discover -s audit-engine/tests | PASSED — 1/1 | Existing engine health test |
| audit-engine/.venv/Scripts/python.exe -m audit_engine | PASSED | status ok; Pandas 3.0.5 |
| npm run test:db | PASSED | Full private-cluster PostgreSQL acceptance; completed 2026-09-14T13:42:37.378Z |
| db:check / db:inspect | PASSED inside acceptance | Real SELECT connectivity and read-only empty-database catalogs; repeated inspection creates no schemas/metadata |
| db:status / db:validate-data | PASSED inside acceptance | Existing metadata/table readiness; consistent full fixture hash and anomaly QA |
| Git whitespace | PASSED | git diff --check passed after all edits |
| Existing Railway operation | REPORTED AS WORKING | Developer report retained; no automated remote proof |
| Railway commands, watch isolation, HTTPS, restart policy, remote grants | NOT VERIFIABLE | No dashboard/remote credentials or service URLs inspected |

Initial acceptance attempts are retained honestly: sandbox initdb FAILED to create its Windows restricted process token. A permitted broader-process run then exposed an admin URL construction defect in the new runner; a later run caught revalidation of Knex-normalized connection settings in reset. Both implementation defects were corrected. The final run above passed; each started cluster was stopped. Docker remains unavailable (missing engine pipe), and was unnecessary for the native PostgreSQL acceptance.

### Disposable target and workflow evidence

The runner accepts no target URL and ignores DATABASE_URL. It initializes a fresh temporary cluster with SCRAM credentials, binds loopback on a selected unused port, creates database auditlens, then executes the API-owned migrations and fixtures. It stops the server in finally. Test files remain in the OS temporary directory for diagnosis; the password file is deleted immediately after initdb. A stopped test cluster is not a provisioned Railway reader.

Verified order: empty inspection twice → connectivity/inspection commands → both migrations → eleven business tables and empty audit schema → seed/validate → rollback last batch → schemas absent → reapply → seed/validate with identical hashes → guarded reset → empty source tables → reseed/validate → constraints → reader provision twice → real permission tests → unchanged source hashes and zero audit tables.

| Table | Generated / manifest / live rows |
| --- | --- |
| employees | 250 / 250 / 250 |
| users | 250 / 250 / 250 |
| roles | 8 / 8 / 8 |
| permissions | 17 / 17 / 17 |
| user_roles | 250 / 250 / 250 |
| role_permissions | 27 / 27 / 27 |
| vendors | 100 / 100 / 100 |
| invoices | 2000 / 2000 / 2000 |
| invoice_approvals | 1840 / 1840 / 1840 |
| payments | 2400 / 2400 / 2400 |
| audit_logs | 12512 / 12512 / 12512 |

Default seed 20260914, fixture version 1.0.0. Logical SHA-256: ce8a804cea5a71bba995530d06dab875433d61faf149ac2bf9ab298284a906f2. Every live per-table hash matched the unchanged canonical [dataset manifest](../apps/api/database/sample-data/dataset-manifest.json) across reloads. Ground truth/policy/manifest matched generation; all 14 exact anomaly sets and groups passed; zero orphans. Neither generators nor benchmark semantics changed. This is fixture QA, not audit detection.

### PostgreSQL constraint and permission evidence

Constraints rejected inside rolled-back transactions: foreign key 23503; invalid status, nonpositive amount, incomplete payment confirmation and invalid employment dates 23514; duplicate employee number 23505; null vendor name 23502. Source data remained intact.

Reader provisioned: auditlens_source_reader, NOLOGIN, non-owner and no parent memberships. A separately authenticated non-superuser auditlens_acceptance_login selected the role; both session_user and current_user were asserted. Ordinary read-write transactions were used for permission attempts so a read-only transaction setting could not mask excess privileges.

| Operation | Actual PostgreSQL result |
| --- | --- |
| SELECT | PASSED on all eleven source tables, including users/invoices/payments |
| INSERT / UPDATE / DELETE / TRUNCATE | PASSED: denied with 42501 |
| CREATE TABLE in business/public/audit | PASSED: denied with 42501 |
| CREATE SCHEMA / CREATE TEMP TABLE | PASSED: denied with 42501 |
| ALTER / DROP source table | PASSED: denied with 42501 |
| Read migration metadata | PASSED: denied with 42501 |
| Read a new business table | PASSED: denied with 42501; no blanket future SELECT |
| Read/update/drop audit test table | PASSED: denied with 42501 |
| Execute new business SECURITY DEFINER function | PASSED: denied with 42501 |
| Integrity afterward | PASSED: unchanged source hashes, no audit tables, migrations ready |

### Definition of Done

| Requirement | Status | Evidence |
| --- | --- | --- |
| PORT contract consistent | PASS | Example/config/tests use PORT; legacy occurrences only historical docs |
| API config tests | PASS | npm test |
| Web environment documented/tested | PASS | Optional preview host and URL tests; DEPLOYMENT |
| API_URL canonical | PASS | Single explicit public mapping |
| DATABASE_URL canonical main connection | PASS | Knex URL contract; no new reader application variable |
| Server secrets excluded from Web | PASS | App and env-probe sentinel builds |
| Production Web build | PASS | npm run build |
| Nested Web routes supportable | PASS | Actual built dist HTTP and static tests |
| Railway deployment contract documented | PASS | DEPLOYMENT dashboard requirements; remote execution unverified |
| Safe read-only DB inspection | PASS | Empty live database unchanged; read-only transaction |
| Database commands classified | PASS | DEPLOYMENT command table |
| Destructive commands guarded | PASS | Opt-in, production refusal, destination guards and tests |
| Disposable migration acceptance | PASS | test:db |
| Fixture seed/validation acceptance | PASS | test:db |
| Deterministic regeneration | PASS | Same live hashes after rollback/reset reload |
| Runtime representative constraints | PASS | PostgreSQL error codes above |
| Reader identity exists/reproducibly provisioned | PASS | Provision twice in fresh cluster; explicit admin tooling |
| Reader SELECT succeeds | PASS | All eleven tables |
| Reader INSERT fails | PASS | 42501 |
| Reader UPDATE fails | PASS | 42501 |
| Reader DELETE fails | PASS | 42501 |
| Reader DDL fails | PASS | CREATE/ALTER/DROP/schema/TEMP 42501 |
| Existing API tests | PASS | npm test |
| Existing dataset tests | PASS | npm test |
| Existing Python tests | PASS | 1/1 |
| Documentation synchronized | PASS | Current status/config/grants/commands and generated schema descriptions |
| VERIFICATION factual results | PASS | This dated record preserves earlier failures and reported facts |
| ROADMAP actual state | PASS | Local verified; remote unverified; no audit framework implemented |

Remaining remote/manual checks do not substitute for any local result. Framework prerequisites still require explicit extraction/snapshot, local operator provenance, policy versioning, evidence retention and result-writer decisions; see [open questions](OPEN-QUESTIONS.md).

## Historical pre-stabilization repository review — 2026-09-14

This historical review superseded earlier snapshots at the time; the stabilization record above now takes precedence. Historical results below are retained as history, not represented as current passes. PostgreSQL connectivity, successful migrations and separate Railway Web/API services are **REPORTED AS WORKING** by the developer. No DATABASE_URL or local .env is available in this review environment; remote runtime was not inspected.

| Check | Current result |
| --- | --- |
| Initial npm test | Failed: dataset imports and database command paths referenced the removed root database directory; port-contract and missing WEB_ALLOWED_HOST failures also reproduced |
| Limited path repairs | Root migration/rollback commands, five script imports and two test files now point into apps/api/database; workspace-local API migration path was already correct |
| npm test after path repairs, WEB_ALLOWED_HOST=localhost supplied | 12/13 passed; API_PORT test fails because implementation reads PORT. Application behavior and that test were not altered |
| Generator and fixture QA | Six dataset tests passed: deterministic equality, alternate seed, exact counts/14 anomaly sets, mutation rejection, local-write guards and offline DDL/rollback compilation |
| Artifact parity | Ground truth, policy and manifest match regenerated fixture; all four three-row sample files checked independently and match |
| Web build | Passed with API_URL=http://localhost:3001 and WEB_ALLOWED_HOST=localhost; missing API_URL fails clearly; API_URL alone does not satisfy required host configuration |
| Browser secret boundary | App and explicit environment probe pass with synthetic database/JWT/unrelated-variable sentinels absent from compiled output |
| API health/error tests | Health, 404 and sanitized 500 contract passed; live loopback HTTP health 200 also passed, with no CORS allow-origin header for a foreign Origin |
| Web development smoke | Vite served nested /findings as HTTP 200 with the application entrypoint; no browser interaction automation |
| Python | Existing virtual environment: unittest 1/1 passed and CLI returned ok with Pandas 3.0.5 |
| db:check and db:validate-data | Attempted; both stop on missing DATABASE_URL before connecting. Not live verification |
| PostgreSQL schema/seed/rollback/constraint/reader denial | Not independently verified; no database writes, migrations or resets were performed |
| Documentation | Compiled ERD/dictionary parity; 39 Markdown files, 104 relative links and 13 Mermaid diagrams validated after reconciliation |
| Git | Clean initial working tree; only documented review changes and stale path repairs; no commit or deployment |

The current API default is API_HOST=0.0.0.0 and PORT=3001, while .env.example still supplies API_PORT and omits WEB_ALLOWED_HOST. Explicit loopback and required Web variables are documented in [deployment](DEPLOYMENT.md). These remaining configuration changes belong to the [next-phase plan](PROJECT-REVIEW.md), not this limited review.

db:status is not guaranteed read-only on an uninitialized database: installed Knex migrate.list() calls ensureTable for migration metadata. It was not run against an unknown destination. A future read-only status command should query catalogs without creating metadata.

## Historical Phase 1 — 2026-09-14

Implementation is delivered, but Phase 1 is **not fully complete** because PostgreSQL runtime and the pre-existing source-reader write-denial acceptance cannot be verified on this host. No authentication or audit detection engine was added.

| Check | Result |
| --- | --- |
| Docker Compose configuration | Passed with a transient placeholder container password; no credential file written |
| docker info / docker compose up -d postgres | BLOCKED: Docker engine named pipe is unavailable; CLI also reports access denied reading its config |
| npm run db:check | BLOCKED: database credentials were absent; command fails clearly before connecting |
| PostgreSQL business/audit schema existence | NOT VERIFIED live |
| public.knex_migrations / clean migration status | NOT VERIFIED live; db:status command supplied |
| Domain migration | PostgreSQL DDL compiles offline: eleven business tables, PK/FK/unique/check constraints and indexes |
| Migration rollback/reapply | Down SQL compiles in reverse FK order; NOT EXECUTED on PostgreSQL |
| npm run db:generate | Passed: 250 users, 2,000 invoices, 1,840 approvals, 2,400 payments, 12,512 events |
| Fixture QA | Passed: all 14 exact anomaly sets and group memberships; zero orphan FKs or log targets; no unexpected duplicate/SoD/dormancy inflation |
| PostgreSQL seed and db:validate-data | NOT EXECUTED: authenticated isolated PostgreSQL unavailable |
| PostgreSQL reset atomicity / actual constraint rejection | NOT VERIFIED live; guarded transactional implementation and offline checks supplied |
| Source-reader write denial | NOT VERIFIED; roles/ingestion remain unimplemented. Existing Phase 1 acceptance remains open |
| npm run build | Passed: React/Vite production build |
| Python health / unittest | Passed: health returned ok and Pandas 3.0.5; 1/1 unittest |
| Automated generator and existing API tests | Passed: 8/8 Node tests, including six dataset/migration/guard tests and two existing API/config tests |
| Documentation consistency | Passed: compiled DDL inventory parity; 35 Markdown files, 72 relative links and 12 Mermaid diagrams parsed |

All data and references are fictional. The source seed writer is a local development administrator, not a restricted source reader. Schema separation alone is not grant enforcement. No .env or real credentials were created, no unrelated database was modified, and no Git commit was made. The existing Phase 0 files were already untracked when this work began.

## Historical definition of done

- [x] PostgreSQL Compose configuration validates statically.
- [ ] PostgreSQL connectivity, schemas, metadata and clean migration status verified live.
- [x] Business migrations exist; rollback SQL compiles.
- [x] Normal and anomalous synthetic data generation works deterministically.
- [x] Ground truth, dataset metadata, role policy and small examples exist.
- [x] Offline validation checks full record identities, keys and expected cases.
- [ ] Database migration/seed/reset/validation/rollback execution verified live.
- [ ] Actual source-reader INSERT/UPDATE/DELETE/DDL denial verified.
- [x] Automated generator tests exist and pass.
- [x] Existing API tests, web build and Python health/tests pass.
- [x] ERD and dictionary are generated from migration SQL.
- [x] Dataset, business process and lineage documentation exist.

## Remaining database verification

Use a dedicated disposable local PostgreSQL instance. Start Docker Desktop's Linux engine; copy .env.example to .env and configure DATABASE_URL and matching Docker-only POSTGRES_PASSWORD. If 5432 is occupied, change the Compose published port and the matching port in DATABASE_URL. Do not alter an unrelated server or delete its data.

```powershell
docker compose up -d postgres
npm run db:check
npm run db:migrate
npm run db:status
# Disposable database only: this drops domain tables and possibly boundary schemas.
npm run db:rollback
npm run db:migrate
npm run db:status
npm run db:seed
npm run db:validate-data
$env:AUDITLENS_ALLOW_LOCAL_RESET='YES'
npm run db:reset
Remove-Item Env:AUDITLENS_ALLOW_LOCAL_RESET
npm run db:seed
npm run db:validate-data
```

Check actual NOT NULL, FK, duplicate master-key, invalid status, nonpositive money and incomplete-confirmation constraint failures inside rollback-only transactions. Confirm audit remains untouched. Provision the future SELECT-only reader separately and prove real writes/DDL fail; mock tests cannot satisfy that acceptance. Record PostgreSQL version and results here before marking Phase 1 complete.

## Phase 0 historical verification

The foundation was previously verified on Windows with Node.js 22.14.0 and bundled Python 3.12 in audit-engine/.venv. npm install, API health/error and invalid-port tests, React/Vite build, API/frontend startup, live health/frontend HTTP requests, Python health/unittest, and relative-link/Mermaid parsing passed. Browser interaction was not automated. PostgreSQL was blocked then by absent credentials and an unavailable Docker Linux engine. Those infrastructure checks were not retrospectively marked passed.

## Historical environment refactor — 2026-09-14

- Node tests: 13/13 passed, including API health/error boundaries, DATABASE_URL validation, exact Knex input, missing-URL failures for all database command entry points, local dataset guard, URL normalization, and production bundle secrecy.
- Production web build passed with API_URL supplied. Both the actual app and an explicit import.meta.env probe were built with synthetic database/JWT/unrelated-variable sentinels; only the public API endpoint was present.
- Python unittest: 1/1 passed.
- Offline db:generate passed; generated fixture files have no Git content changes, anomaly counts unchanged, zero orphans.
- docs:check passed: schema parity, 37 Markdown files, 74 relative links, 12 Mermaid diagrams.
- docker compose config --quiet passed using a transient placeholder POSTGRES_PASSWORD. Docker emitted a config-file access warning; docker info failed because the engine pipe is unavailable.
- Live connectivity, migration, rollback, seed, reset and database validation remain unverified: no configured DATABASE_URL or running Docker engine. Missing-configuration command tests do not substitute for live PostgreSQL verification.
- Final source/Markdown search found no legacy database or frontend endpoint variable names. Dependencies, Git history, virtual environments and generated bundles were excluded from the source search; bundles were checked separately above.
- Corrected a pre-existing stale migration filename in the offline SQL helper so dataset and documentation tests can execute. Migration contents, business rules and phase scope are unchanged.
