# Audit Rule Pack v1

## Purpose and control objective

The pack contains duplicate-reference and required-field completeness controls. A reference expected to identify
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

SDK configuration supports exactly boolean, integer, string and list[string]; bool is not an integer.
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

## Completeness control: business.missing_required_field

### Objective and identity

Records required for financial, operational, or control processing should contain
all mandatory business fields. This generic detector checks explicitly configured
fields; it makes no accounting-domain assumptions.

Detector `business.missing_required_field`, version `1.0.0`, category
`data_completeness`, emits rule `MISSING_REQUIRED_FIELD`, severity `medium`,
confidence `1.0`. Entity type is the configured table; entity ID is the record key.

### Configuration and required inputs

| Key | Type | Default |
| --- | --- | --- |
| table | string | transactions |
| id_field | string | id |
| required_fields | list[string] | ["reference"] |
| treat_empty_string_as_missing | boolean | true |

The conceptual default table requires explicit configuration with the approved
snapshot inventory. The runnable policy uses `invoices`, `id`, and required fields
`reference` and `vendor_id`. No schema was added. `requirements_for(config)` checks
all configured names through existing schema/context compatibility before analysis,
including empty tables. Missing names are compatibility failures, never findings.

Lists must contain strings only; required_fields must be non-empty and contain no
duplicates. Names follow the SDK identifier syntax. Wrong types, nested arrays,
unknown keys and duplicate names fail deterministically before run creation.
Lists freeze to tuples internally and serialize as JSON arrays. List order is
preserved in configuration and its hash; evidence field order is always ascending.
Existing boolean/integer/string serialization and hashing are unchanged.

### Exact missing-value semantics

Only null is always missing. With treat_empty_string_as_missing=true, the exact
empty string is also missing. With false it is present. No trimming or truthiness
checks occur: whitespace, 0, false, empty arrays and empty objects remain present.
Floating-point 0.0 is rejected by the existing snapshot contract before analysis;
decimals are represented as strings by snapshot normalization. Values are evaluated
exactly as represented in that normalized snapshot.

### Findings, evidence and example result

One incomplete record produces one finding, regardless of how many fields are
missing. This keeps review and remediation centered on the record. The description
is `Record <id> is missing <n> required field(s).` Complete records produce none.

One evidence item identifies each missing field. To preserve the frozen Finding
contract and avoid quadratic duplication, the first item in ascending field order
also carries the record's sorted `missing_fields` and `missing_field_count` in its
context. Every item carries `missing_classification` (`null` or `empty_string`).
No unrelated values or full rows are copied. Example first evidence item (ID omitted):

```json
{
  "source_table": "invoices",
  "source_record_id": {"id": "00000000-0000-4000-a000-000000000003"},
  "field": "reference",
  "observed_value": "",
  "context": {
    "missing_classification": "empty_string",
    "missing_field_count": 2,
    "missing_fields": ["reference", "vendor_id"]
  }
}
```

The second item has field vendor_id, observed_value null and context
`{"missing_classification":"null"}`. The
[canonical result](../audit-engine/fixtures/missing-required-field/example-result.json)
contains two findings: record 2 lacks reference; record 3 lacks reference and
vendor_id. Record 1 is complete.

### Offline example policy

The full [policy](../audit-engine/policies/missing-required-field.json) selects only
this detector through the normal policy CLI. Its detector_configuration is:

```json
{
  "business.missing_required_field": {
    "table": "invoices",
    "id_field": "id",
    "required_fields": ["reference", "vendor_id"],
    "treat_empty_string_as_missing": true
  }
}
```

Copy `audit-engine/fixtures/missing-required-field/snapshots` to a fresh artifact
root as in the example above, then run:

```powershell
& $python -m audit_engine policy validate audit-engine/policies/missing-required-field.json
& $python -m audit_engine --artifacts-dir $root run --snapshot 00000000-0000-4000-a000-000000000200 --policy audit-engine/policies/missing-required-field.json
```

### Determinism, complexity and limitations

The framework derives evidence/finding identities from canonical semantic content,
including detector/rule, table, record key and missing-field evidence. Changing the
missing-field set changes finding identity. Row/key order, snapshot artifact ID,
run ID, timestamps, operator and artifact root do not change logical content/hash.
Tests also mutate record IDs, presence, configuration, detector version, finding
content and evidence content and require different logical hashes. A pre-edit golden
baseline protects duplicate-reference policy/config serialization and its run hash;
the earlier default/boolean/integer golden baselines are retained.

Evaluation and evidence construction cost O(n � f), plus O(f log f) field sorting
and the framework's canonical finding/evidence sorting. Memory is O(n + m), where m
is emitted evidence/content size. No workers, caches or dependencies were added.

Current limitations: approved schema inventory only; unique non-empty string record
identities; unconditional requirements across the whole table; no conditional,
cross-table or format validation. Invalid custom IDs produce sanitized detector
errors. The trusted in-process boundary, unsigned checksums, whole-snapshot hashing
and unverified production deployment limitations described above also apply.

Recommended next rule: `business.sequence_gap`, adding ordering/continuity control
without probabilistic or statistical auditing. It is not implemented in this phase.
