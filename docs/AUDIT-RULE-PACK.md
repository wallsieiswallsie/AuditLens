# Audit Rule Pack v1

## Purpose and control objective

The foundation contains exactly one business rule. A reference expected to identify
one business transaction should not occur on multiple records. A finding identifies
a repeated value for review; it does not establish fraud or a duplicate payment.

The rule follows the existing pipeline: snapshot integrity validation → frozen
AuditContext → policy and explicit registry → typed configuration and resolved
requirements → evaluation → canonical AuditResult → local provenance/artifacts.
Framework version remains 0.3.0. Snapshot, policy and result JSON shapes are unchanged.

## Identity and required inputs

| Attribute | Value |
| --- | --- |
| Detector ID | `business.duplicate_transaction_reference` |
| Detector version | `1.0.0` |
| Category | `transaction_integrity` |
| Rule ID | `DUPLICATE_TRANSACTION_REFERENCE` |
| Severity / confidence | `medium` / `1.0` (certainty of repetition, not of misconduct) |
| Entity type | `transaction_reference` |
| Requirements | Schema version `1`; configured table, ID field and reference field |

Metadata declares default requirements. The optional SDK `requirements_for(config)`
hook resolves configured names into the existing DetectorRequirements contract.
Missing tables/fields become deterministic `missing_table`/`missing_field` skipped
results before analysis; the run fails and CLI exits 1. Empty tables are checked
against the existing versioned schema inventory. `policy validate` checks types and
declarations; snapshot compatibility is checked during `run`.

## Configuration

| Key | Type | Default | Meaning |
| --- | --- | --- | --- |
| table | string | transactions | Snapshot table |
| id_field | string | id | Unique, non-empty string record identity |
| reference_field | string | reference_number | Business reference |
| ignore_empty | boolean | true | Exclude null and empty string |
| case_sensitive | boolean | true | Exact strings; false uses Unicode casefold |

SDK configuration supports exactly boolean, integer and string; bool is not an integer.
Unknown keys and wrong types fail policy validation before run artifacts or analysis.
Resolved table/field names follow the existing metadata identifier syntax:
`[a-z][a-z0-9_.-]{0,99}`. Defaults are frozen and recorded in effective configuration.
There is no arbitrary JSON configuration or environment interpolation.

The frozen snapshot loader currently accepts eleven approved tables, not arbitrary
ERP schemas. The conceptual `transactions` default therefore requires explicit
configuration with today's loader. The runnable example uses `invoices`, `id`, and
`reference`. The detector contains no invoice-specific or database-specific logic.

## Exact semantics

- Compare values as represented in the normalized snapshot; do not trim whitespace.
  `A`, ` A` and `A ` are distinct. Whitespace-only strings are not empty.
- With `ignore_empty=true`, exclude only null and `""`. With false, repeated nulls
  form one group and repeated empty strings form another.
- With `case_sensitive=false`, apply Python `str.casefold()` to strings only.
  `Straße` and `STRASSE` match. Original spellings remain in evidence. There is no
  locale behavior or additional Unicode composition normalization.
- Null, string, integer and boolean normalized references are supported; JSON type
  distinctions are retained (`1`, `true` and `"1"` are separate values).
  Nested objects/arrays are unsupported and produce a sanitized `detector_error`.
- Each group containing at least two records produces one finding with all records
  as evidence. Unique values and valid empty tables produce zero findings.
- The configured ID must uniquely identify every row with a non-empty string.
  Invalid/repeated IDs fail with `detector_error`, including on ignored-reference rows.
  This preserves the existing string-valued evidence record-key contract.
- Group across the whole configured table. There is no vendor, company, period,
  currency, status or amount filter and no cross-table grouping.

## Findings and evidence

Each finding includes rule/detector identity, medium severity, confidence, title,
description, entity identity, run/snapshot linkage and evidence using the existing
contracts. Structured details live in evidence `context`; no finding field was added.

The entity ID is SHA-256 of canonical JSON containing table, reference field and
comparison value. The framework computes final finding/evidence IDs from canonical
semantic content, including participating IDs and original reference values.
Evidence includes only table, `{configured_id_field: record_id}`, reference field,
original observed value, comparison value and group size. Other row fields are absent.

Example evidence for one of the two `INV-001` records (generated evidence ID omitted
here for readability):

```json
{
  "source_table": "invoices",
  "source_record_id": {"id": "00000000-0000-4000-a000-000000000001"},
  "field": "reference",
  "observed_value": "INV-001",
  "context": {"comparison_value": "INV-001", "group_size": 2}
}
```

The finding description is `2 records in invoices share reference comparison value
"INV-001".` The [complete canonical example result](../audit-engine/fixtures/business-rulepack-v1/example-result.json)
contains one finding and both evidence records, with real content IDs.

## Offline policy and snapshot example

Use [business-rulepack-v1.json](../audit-engine/policies/business-rulepack-v1.json).
It selects only this business detector with explicit invoice fields and strict errors.
The existing `default.json` still selects health only.

The [fixture manifest](../audit-engine/fixtures/business-rulepack-v1/snapshots/00000000-0000-4000-a000-000000000100/manifest.json)
and its eleven canonical JSONL files are the actual Snapshot contract: three invoices
with references `INV-001`, `INV-002`, `INV-001`; other tables empty. They are synthetic
offline data, not a relationally complete seed dataset. No PostgreSQL is needed.
The scoped `.gitattributes` rule preserves exact JSONL bytes across Git checkouts;
automatic Windows line-ending conversion would invalidate the manifest hashes.

From repository root, use the project virtual-environment Python:

```powershell
$python = '.\audit-engine\.venv\Scripts\python.exe'
$root = 'audit-engine/artifacts/rulepack-example'
New-Item -ItemType Directory -Force $root | Out-Null
Copy-Item -Recurse audit-engine/fixtures/business-rulepack-v1/snapshots $root
& $python -m audit_engine policy validate audit-engine/policies/business-rulepack-v1.json
& $python -m audit_engine --artifacts-dir $root snapshot inspect 00000000-0000-4000-a000-000000000100
& $python -m audit_engine --artifacts-dir $root run --snapshot 00000000-0000-4000-a000-000000000100 --policy audit-engine/policies/business-rulepack-v1.json
# Use the Audit Run ID printed above:
& $python -m audit_engine --artifacts-dir $root result inspect <run-id>
```

Use a fresh destination for copying the fixture. The execution creates the ordinary
run, policy, provenance, logical checksum and result artifacts; no separate rule CLI.

## Determinism, compatibility and security

Grouping is expected O(n), plus canonical sorting costs; memory is O(n). No pairwise
comparisons, workers, caches or external dependencies were added. The SDK orders
findings by severity/rule/entity/content ID and evidence by table/canonical record
key/field/content. Source row and dictionary order do not change results.

Regression tests vary row order, dictionary order, root, operator, snapshot ID, run ID
and timestamps and assert identical logical content and SHA-256. Separate mutations
of reference, participating ID, effective configuration, detector version, finding
description and evidence context each change the hash. Unicode/empty/type behavior,
missing inputs, invalid config, subprocess CLI and secret sentinels are covered.

The [legacy baseline](../audit-engine/fixtures/business-rulepack-v1/legacy-baseline.json)
was captured by running the pre-change SDK/execution from Git revision
`52c8b72887480894929cd54e69ccd18e261ae140` on the existing test sample. Regression tests
compare unchanged default, boolean and integer policy JSON and logical hashes with
that baseline. Existing contracts, default policy, health/integrity detectors, artifact
layout and logical hash algorithm remain unchanged. CLI health/no-argument behavior
and the no-policy run output are retained; explicit-policy runs omit the obsolete
"framework smoke only" label.

The detector receives only frozen AuditContext and validated DetectorConfig. It
accesses no adapters, credentials, environment, filesystem, network or subprocesses.
The existing trusted in-process boundary is unchanged; this is not an OS sandbox.

## Conventions and limitations

Future rules should reuse metadata, typed config, resolved requirements, minimal
evidence and canonical result normalization, with semantic/version/hash regressions.
This extends ADR-010's configuration/requirements model; no separate architectural
decision or second metadata system is introduced, so no new ADR is needed.

References must be unique within the whole selected population for the control to
be appropriate. Legitimate reference reuse can require investigation. Single-field
string record identities and the approved snapshot inventory are current limits.
Casefold uses the Python runtime's Unicode tables; retain the runtime when reproducing
historical Unicode comparisons. Snapshot/result hashes are unsigned checksums; they
include the whole snapshot, so unrelated source changes can also change run hashes.
No production/Railway deployment has been verified for this rule.

Recommended next rule: `business.missing_required_field`, to validate completeness
using the same configurable requirements and minimal evidence conventions. It is
not implemented in this phase.
