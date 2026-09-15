# Audit Rule Pack v1 integration

Framework **0.3.0** runs the five existing business controls through one canonical
[policy](../audit-engine/policies/rulepack-v1.json): `business.rulepack.v1`, version
`auditlens-policy-v1`, name **Audit Rule Pack v1**. No detector, algorithm, schema,
hash contract or legacy policy changes are part of this integration.

| Detector | Purpose | Existing configuration |
| --- | --- | --- |
| business.duplicate_transaction_reference | Uniqueness | invoices: id/reference, case sensitive, ignore empty |
| business.missing_required_field | Completeness | invoices: reference and vendor_id, empty string counts as missing |
| business.sequence_gap | Continuity | invoices.reference, integer values, inferred bounds, duplicates allowed |
| business.duplicate_payment | Exact payment duplication | payments: invoice_id, amount, currency, reference; ignore empty components; case sensitive |
| business.amount_outlier | Statistical monetary review | payments.amount grouped by currency; Tukey IQR multiplier 1.5; minimum 8; upper only; retain zero/negative |

These cover five representative control classes. See [rule semantics](AUDIT-RULE-PACK.md)
for the algorithms and limitations; findings are review candidates.

## Applicability is a deployment gate

The sequence policy requires **integer or null** invoice references. The approved
snapshot scalar contract supports the controlled integer fixture. The existing
PostgreSQL business schema/data uses text references; even numeric-looking strings
are rejected by the sequence detector. Policy/schema validation alone cannot establish
this semantic requirement. The full canonical policy therefore fails closed on that
dataset. Do not coerce references, relabel unrelated fields as sequences, change the
source, or disable a rule while describing the run as complete Rule Pack v1 coverage.

Successful five-control integration is proven on the controlled snapshot. Four
compatible controls can be compared against their individual outputs on the exported
PostgreSQL snapshot; the sequence error must remain visible. Supporting that source
with all five controls requires a separately approved source/sequence mapping decision.

## Lifecycle and execution

Read-only source acquisition → canonical eleven-table snapshot → integrity validation
→ frozen context → policy/configuration/requirements validation → ordered detector
execution → canonical results → provenance and local artifacts. Snapshot integrity is
checked by the loader; no redundant framework detectors are included in this policy.

From repository root, after engine installation:

```sh
python -m audit_engine health
python -m audit_engine detectors list
python -m audit_engine policy validate audit-engine/policies/rulepack-v1.json
python -m audit_engine --artifacts-dir /data/auditlens snapshot
python scripts/audit-readiness.py --artifacts-dir /data/auditlens --snapshot SNAPSHOT_ID
python -m audit_engine --artifacts-dir /data/auditlens run --snapshot SNAPSHOT_ID --policy audit-engine/policies/rulepack-v1.json --operator staging-verification
python -m audit_engine --artifacts-dir /data/auditlens result inspect RUN_ID
```

`SNAPSHOT_ID` and `RUN_ID` mean the actual UUIDs printed by previous commands.
The operator controls local paths; no API accepts paths, imports or commands.

For a safe database-free demonstration, copy the committed
[fixture snapshot directory](../audit-engine/fixtures/rulepack-v1/snapshots/00000000-0000-4000-a000-000000000600/manifest.json)
and all its sibling table files to a writable artifact root under
`snapshots/00000000-0000-4000-a000-000000000600`, then use that UUID. Never seed this
fixture into production. It exercises the existing snapshot contract, not relational
constraints or a new database schema. It has five invoices, eight payments and nine
empty tables, with every approved column present.

| Control | Expected findings | Evidence items |
| --- | ---: | ---: |
| Amount outlier | 1 | 1 |
| Duplicate payment | 1 | 2 |
| Duplicate transaction reference | 1 | 2 |
| Missing required field | 2 | 2 |
| Sequence gap | 1 | 2 |
| Total (five results) | 6 | 9 |

## Determinism and failure behavior

Policy normalization orders detector IDs lexically: amount, payment, reference,
completeness, sequence. Existing canonical finding and evidence ordering applies.
Each control alone produces the same logical result as its component in the pack.
Payment duplicates remain in the amount population; missing fields do not remove rows.

Controlled logical SHA-256:
`8893bf4a40f24d85d545124bb1da878c3228636f59c927a73e60b92d3a1dfb55`.
Run identity, time, operator, output location, snapshot identity, source ordering and
dictionary ordering do not change logical output. Configuration, business source
values, detector versions, findings and evidence do. Hashing remains unsigned.

Canonical execution is strict (`fail_on_detector_error=true`,
`allow_partial_results=false`). An exception yields `detector_error`; an unmet
requirement yields `skipped` with its existing reason. Prior results remain available;
later controls are explicitly `skipped`/`strict_failure`; run status is `failed`.
The separate integration tests also exercise both flags inverted: later controls
continue and successful results persist, but the run still reports `failed`.

## Artifacts and provenance

- `snapshots/ID/manifest.json` and eleven JSONL files: approved inventory/counts/hashes.
- `runs/ID/run.json`: status, framework/policy versions, snapshot identity/hash,
  resolved detector versions and effective configurations.
- `runs/ID/policy.json`: full normalized policy including policy identity and version.
- `runs/ID/provenance.json`: explicit operator, timestamp, execution mode and snapshot reference.
- `runs/ID/logical-results.json`: canonical logical content and SHA-256.
- `results/ID/DETECTOR_ID.json`: five inspectable results with findings/evidence.

Existing atomic/no-clobber writes are retained; only run lifecycle metadata is
intentionally replaced atomically. Publication is per file, not a whole-run
transaction. A killed process can leave incomplete artifacts: inspect status and
inventory, preserve diagnostics and rerun under a new ID. Do not overwrite history.

See [production runbook](PRODUCTION-RUNBOOK.md) for service commands, readiness,
storage and access limitations; [verification](VERIFICATION.md) separates local,
disposable PostgreSQL and actual Railway evidence.
