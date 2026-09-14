# Audit Rule Pack v1

## Purpose and control objective

The pack contains duplicate-reference, required-field completeness, numeric sequence, exact composite payment and statistical amount-outlier controls. A reference expected to identify
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

SDK configuration supports exactly boolean, integer, optional_integer, string and list[string]; bool is not an integer.
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

Evaluation and evidence construction cost O(n × f), plus O(f log f) field sorting
and the framework's canonical finding/evidence sorting. Memory is O(n + m), where m
is emitted evidence/content size. No workers, caches or dependencies were added.

Current limitations: approved schema inventory only; unique non-empty string record
identities; unconditional requirements across the whole table; no conditional,
cross-table or format validation. Invalid custom IDs produce sanitized detector
errors. The trusted in-process boundary, unsigned checksums, whole-snapshot hashing
and unverified production deployment limitations described above also apply.

The duplicate-payment section below specifies the implemented exact composite
matching control; temporal scoping remains outside its version 1.0.0.

## Sequence control: business.sequence_gap

### Objective and identity

Records expected to follow a continuous numerical sequence should not contain
unexplained gaps. This generic control supports document numbering continuity;
a gap is a review signal, not proof of wrongdoing. Detector version is **1.0.0**,
category `sequence_integrity`, rule `SEQUENCE_GAP`, severity `medium`, confidence
1.0 (certainty of the observed gap), entity type `sequence_range`.
It uses the same frozen-context SDK, policy validation, registry, canonical result
and provenance pipeline. Framework version stays **0.3.0**.

### Configuration and requirements

| Key | Type | Default | Meaning |
| --- | --- | --- | --- |
| table | string | transactions | Source table |
| id_field | string | id | Unique non-empty string identity |
| sequence_field | string | sequence_number | Numeric sequence field |
| minimum_value | optional_integer | null | Inclusive lower bound; otherwise observed minimum |
| maximum_value | optional_integer | null | Inclusive upper bound; otherwise observed maximum |
| allow_duplicates | boolean | true | Permit repeated sequence values |

`requirements_for(config)` resolves the configured table and both fields. Missing
schema produces the existing skipped `missing_table`/`missing_field` result and a
failed run before analysis, including for empty tables. Invalid types, names, unknown
configuration or explicit minimum > maximum fail policy validation before analysis.
Equal bounds are valid. Defaults are conceptual; the approved loader inventory
requires an explicitly configured table/field, as with the other business rules.

### Sequence and bound semantics

- Only exact integers and null are valid. Booleans, floating point, stringified
  integers and nested values are never coerced. The snapshot loader already rejects
  floats; direct detector input also rejects them.
- Nulls are ignored, including for duplicate detection; completeness is a separate rule.
- Every row must have a unique non-empty string ID, even when its sequence is null.
- With duplicates allowed, evaluate distinct sequence values. With false, any repeated
  non-null sequence value causes sanitized `detector_error`, failed run and CLI exit 1.
  Invalid inputs are checked throughout the table, including outside configured bounds,
  before any findings are constructed. Duplicate values are never gap findings.
- Unset bounds use observed extrema. Explicit bounds clip the expected population;
  values outside it are not reported as missing. They may substantiate nearby boundaries.
- No observations and no bounds yield zero findings. Two explicit bounds with no
  observations yield one whole-range finding. One bound without observations cannot
  establish a finite range, so yields zero findings. If an inferred opposite bound
  makes the interval empty, there are zero findings. Explicit reversed bounds are errors.
- Integers can be zero or negative. There is no assumed start at 1 and no implied
  missing values beyond the finite expected interval.

### Findings and evidence

Each contiguous missing range is one finding: `1,2,6` yields `3-5`, whereas `1,3,5`
yields separate `2` and `4` findings. This represents the control exception compactly
without emitting one finding per missing number. Messages are deterministic, e.g.
`Sequence gap detected in invoices.reference: 5-7.`

The frozen Finding contract has no content property. Its string `entity_id` contains
canonical JSON with the structured scope/range below. This is deterministic semantic
identity, independent of run IDs, paths or timestamps; the framework derives finding
and evidence SHA-256 IDs as usual. Content remains available when evidence is empty.

```json
{
  "table": "invoices",
  "id_field": "id",
  "sequence_field": "reference",
  "missing_start": 5,
  "missing_end": 7,
  "missing_count": 3
}
```

At most two real boundary records are evidence. Each item contains the configured
record key, field, observed integer, `sequence_role`, range content, and configured
minimum/maximum in context; no full row is copied.

| Example | Gap | Evidence |
| --- | --- | --- |
| Observed 2,6 | 3-5 | 2 before_gap; 6 after_gap |
| Minimum 1; first observed 3 | 1-2 | 3 after_gap |
| Last observed 8; maximum 10 | 9-10 | 8 before_gap |
| No observations; explicit 1..10 | 1-10 | Empty evidence; no source record exists |

Nearest observations are selected from the full validated sequence population.
If several records have a boundary value, choose the canonically smallest JSON
record identity, matching the framework's canonical evidence ordering. Source order
never selects a boundary. Evidence order follows the existing canonical record-key
sort; `sequence_role` indicates whether it is before or after the gap.

### Offline policy and example result

There is no suitable numeric business sequence in the disposable PostgreSQL source.
The fixture deliberately supplies integer document references in the approved
`invoices.reference` column. It is controlled offline data, not a claim that real
string references or arbitrary UUIDs are numerical sequences. It preserves the
existing eleven-table snapshot contract and supplies four records with references
`1,2,4,8`; the other tables are empty. Findings are `3` and `5-7`.

The runnable [policy](../audit-engine/policies/sequence-gap.json) selects only
`business.sequence_gap`, with this effective configuration:

```json
{
  "table": "invoices",
  "id_field": "id",
  "sequence_field": "reference",
  "minimum_value": null,
  "maximum_value": null,
  "allow_duplicates": true
}
```

The [example result](../audit-engine/fixtures/sequence-gap/example-result.json)
is a complete existing AuditResult artifact. Run from the repository root:

```powershell
$python = 'audit-engine/.venv/Scripts/python.exe'
$root = Join-Path $env:TEMP ('auditlens-sequence-' + [guid]::NewGuid())
New-Item -ItemType Directory -Path $root | Out-Null
Copy-Item -Recurse audit-engine/fixtures/sequence-gap/snapshots $root
& $python -m audit_engine policy validate audit-engine/policies/sequence-gap.json
& $python -m audit_engine --artifacts-dir $root run --snapshot 00000000-0000-4000-a000-000000000300 --policy audit-engine/policies/sequence-gap.json
# Use the printed Audit Run ID with result inspect.
```

PostgreSQL acceptance verifies registration, policy validation and schema compatibility
for this rule. Positive gap detection is verified separately using offline snapshots.

### Determinism, complexity and limitations

Findings sort by numeric missing start, then end, including negative and multi-digit
values. Tests vary row/key order, snapshot/run identity, time, operator and artifact
root and require equal logical results/hashes. Sequence values, gaps, either bound,
duplicate configuration, detector version, finding and evidence mutations change
hashes. Existing framework, duplicate and completeness golden hashes remain protected.

Collection and boundary representative selection are O(n); sorting and boundary
lookup give O(n log n) total work and O(n + g) memory, for n observed records and g
gaps. There is no iteration over expected integers. The billion-wide regression
emits `2-999999999` and measures detector peak allocations below 1 MB.

Limitations: one whole-table sequence per execution; no grouping by entity/period,
resetting counters, prefixes, permitted-gap lists or explanation workflow. Integers
must already be represented as integers. Current approved schema and string-ID
requirements apply. Snapshot checksums are unsigned and hashes cover the entire
snapshot. Trusted in-process execution receives only AuditContext and validated
DetectorConfig; no new filesystem, source adapter, credential, network or process
capability is added. Production/Railway verification remains outstanding.


## Payment control: business.duplicate_payment

### Objective and identity

A payment should not be processed more than once for the same business obligation
or payment identity. This generic control flags potential duplicates for review;
matching is not proof of duplicate settlement or misconduct.

| Attribute | Value |
| --- | --- |
| Detector / version | `business.duplicate_payment` / `1.0.0` |
| Category / rule | `payment_integrity` / `DUPLICATE_PAYMENT` |
| Severity / confidence | `high` / `1.0` (certainty of exact matching) |
| Entity type | `payment_match_group` |
| Framework | `0.3.0`, unchanged |

### Configuration and requirements

| Key | Type | Default |
| --- | --- | --- |
| table | string | payments |
| id_field | string | id |
| match_fields | list[string] | invoice_id, amount, currency, reference (in that order) |
| ignore_if_any_match_field_empty | boolean | true |
| case_sensitive_strings | boolean | true |

`match_fields` must contain at least two unique field names. Empty lists, one-field
lists, repeated fields, invalid identifiers, unknown keys and incorrect types fail
policy validation before analysis or run artifacts. Configuration order is preserved
and is hash-significant. Names use the SDK identifier syntax documented above.
The existing `requirements_for(config)` declares the configured table, identity field
and every match field. Missing schema requirements produce `missing_table` or
`missing_field` skipped results and a failed run before analysis, including empty
tables. Record identities must be unique non-empty strings, as in existing business
rules; invalid identities produce a sanitized detector error, not business findings.

The approved `payments` schema contains invoice_id, amount, currency and reference;
it has no vendor_id. The example uses payment obligation plus exact monetary value,
currency and payment reference. All names remain configurable; no business-specific
logic, joins or source access is embedded in the detector.

### Exact matching

All configured fields must compare equal. Canonical JSON of the ordered composite
values is the hash-map key. Null, strings, integers and booleans preserve type identity:
`1`, `true` and `"1"` differ. No conversion to floats or between scalar types occurs.
Money has already been normalized by the existing snapshot loader (for example
`100` becomes `"100.00"`); the detector uses that exact snapshot representation.

Strings compare exactly by default. When `case_sensitive_strings=false`, only
field-level strings use Python `str.casefold()`: `Straße` and `STRASSE` match.
Whitespace is never trimmed: `PAY-001` and ` PAY-001 ` differ. No locale-dependent
transformation, Unicode composition normalization or tolerance is applied.
Original values remain in evidence.

Empty means exactly null or `""`. With the default true flag, any empty match field
excludes the record. With false, empty values participate: two identical null-bearing
composites match, but null differs from `""`. Space, zero, false, arrays and objects
are not empty. Snapshot-supported arrays and objects compare structurally through
canonical JSON: object key order is irrelevant; array order and nested scalar types
are significant. Nested strings and object keys remain exact even in case-insensitive
mode; casefold applies only when the configured field value itself is a string.

### Grouped finding and evidence

Each group of two or more matching records yields one finding, not all record pairs.
Three identical keys yield one finding with three evidence items. The entity ID is
SHA-256 of canonical detector ID, rule ID, table, ordered match field names and
normalized composite values. It excludes record IDs, evidence order and run metadata.
The existing execution layer generates content IDs and sorts findings canonically.

The frozen Finding contract has no arbitrary content property. The deterministic
message reports the group size; minimal evidence context carries structured fields,
original values, normalized ordered values and duplicate count. Each participating
record supplies exactly one Evidence with `field=null` and `observed_value=null`.
No unrelated columns or full rows are copied. Evidence sorts by canonical record
identity, both directly in the detector and through existing result normalization.

Example finding description:
`Potential duplicate payment detected: 2 records share the configured payment match key.`

Example evidence item (content ID omitted here; generated by existing execution):

```json
{
  "source_table": "payments",
  "source_record_id": {"id": "00000000-0000-4000-a000-000000000001"},
  "field": null,
  "observed_value": null,
  "context": {
    "match_fields": ["invoice_id", "amount", "currency", "reference"],
    "match_values": {"invoice_id": "I1", "amount": "100.00", "currency": "IDR", "reference": "P1"},
    "normalized_match_values": ["I1", "100.00", "IDR", "P1"],
    "duplicate_count": 2
  }
}
```

The complete canonical finding/result is in the
[example artifact](../audit-engine/fixtures/duplicate-payment/example-result.json).
The controlled fixture uses three payment rows and ten empty tables in the existing
snapshot format. Its symbolic invoice IDs represent controlled matching values,
not a relationally complete production dataset.

### Runnable policy and fixture

The [complete example policy](../audit-engine/policies/duplicate-payment.json) enables
only this rule, with the defaults above, info minimum severity, confidence 0.0,
fail-on-error true and partial results false. It leaves all existing policies intact.

```powershell
$py='audit-engine/.venv/Scripts/python.exe'
$root='audit-engine/fixtures/duplicate-payment'
& $py -m audit_engine policy validate audit-engine/policies/duplicate-payment.json
& $py -m audit_engine --artifacts-dir $root run --snapshot 00000000-0000-4000-a000-000000000400 --policy audit-engine/policies/duplicate-payment.json
# Use the printed Audit Run ID:
& $py -m audit_engine --artifacts-dir $root result inspect <audit-run-id>
```

### Determinism, cost and boundaries

Tests vary record/dictionary order, run ID, snapshot artifact identity, timestamps,
operator and artifact root and require identical logical results/hashes. Mutating
match values, participating IDs, ordered match configuration, either boolean option,
detector version, finding content or evidence content changes the logical hash.
Existing health, inventory and all three prior business rule golden hashes remain
protected. The logical hash still covers the whole snapshot, not just selected fields.

Hash-map construction is approximately O(n × f) for bounded-size field values.
Canonicalization also scales with value size and sorts nested object keys. Evidence
sorting adds O(n log n) identity comparisons in the worst case, and group sorting adds
O(g log g), where g is the number of duplicate groups. Memory is O(n × f) for bounded
values plus output. There are no pairwise O(n²) comparisons, new dependencies, threads,
caches or external storage.

The detector receives only frozen AuditContext and validated DetectorConfig. Existing
trusted in-process execution and secret-sentinel coverage remain intact; no adapter,
credential, filesystem, network or subprocess capability is added. PostgreSQL acceptance
checks actual schema, registration, policy and execution and independently compares
real exact groups; positive behavior is always exercised by the controlled fixture.

Limitations: exact single-table matching only; no date windows, amount tolerance,
fuzzy reference matching, cross-table matching, approved-exception lists, statistical
scoring or ML. Currency must be included when relevant to the configured control.
Production/Railway verification remains unverified.

The amount outlier control below adds the first statistical rule. Recommended next
phase: Rule Pack v1 integration and production-readiness verification.

## Statistical control: business.amount_outlier

Identity: `business.amount_outlier` **1.0.0**, category `monetary_anomaly`, rule
`AMOUNT_OUTLIER`, severity `medium`, confidence 1.0 for deterministic rule matching.
Confidence is not a probability of fraud. Framework remains **0.3.0**.

### Audit objective and exact algorithm

Identify unusually large or small monetary records relative to their configured
single-table population. The only algorithm is **Tukey IQR**, with explicit
**median-of-halves quartiles**, **Decimal arithmetic**, and **strict fence comparisons**.

Sort eligible Decimal values ascending once per evaluated group. Split an even
population into equal halves. For an odd population, exclude the overall median
from both halves. Q1 is the lower-half median; Q3 is the upper-half median. For any
even-sized half, median is `(a + b) / 2` using exact Decimal arithmetic.

```text
IQR = Q3 - Q1
lower_fence = Q1 - multiplier * IQR
upper_fence = Q3 + multiplier * IQR
lower outlier: value < lower_fence, if enabled
upper outlier: value > upper_fence, if enabled
```

For values 1 through 8: halves are `[1,2,3,4]` and `[5,6,7,8]`; Q1=2.50,
Q3=6.50, IQR=4.00. With multiplier 1.5 the fences are -3.50 and 12.50.
For 1 through 9, exclude 5: Q1=2.50, Q3=7.50, IQR=5.00; fences -5.00 and 15.00.
Values exactly on either fence are never findings.

### Configuration and requirements

| Field | Existing SDK type | Default | Validation/meaning |
| --- | --- | --- | --- |
| table | string | payments | Valid configured table identifier |
| id_field | string | id | Valid identifier; unique non-empty string record IDs |
| amount_field | string | amount | Valid identifier; exact plain decimal strings or null |
| group_by_fields | list[string] | [] | Distinct valid field identifiers, in configured order |
| iqr_multiplier | string | "1.5" | Positive canonical decimal string |
| minimum_sample_size | integer | 8 | At least 4; booleans rejected |
| detect_lower_outliers | boolean | false | Enable strict lower fence comparison |
| detect_upper_outliers | boolean | true | Enable strict upper fence comparison |
| ignore_zero | boolean | false | Exclude exact zero if true |
| ignore_negative | boolean | false | Exclude amounts less than zero if true |

At least one direction must be enabled. Multiplier grammar accepts `1.5`, `2`,
`2.25`, `0.125`; rejects zero, negatives, NaN, Infinity, exponents, locale commas,
leading plus/zeros, whitespace and redundant fractional zeros such as `1.50`.
Validation uses the existing string type and `requirements_for(config)`; no new
SDK primitive or nested configuration was necessary. Unknown keys and wrong types
fail before analysis/run creation. Requirements include table, ID, amount and every
grouping field. Missing schema requirements are stable compatibility skips in a
failed run, never business findings, including for an empty table.

### Monetary representation and population semantics

The current approved payment snapshot normalizes money to fixed two-decimal strings
and rejects null payment amounts and non-cent precision. That loader is unchanged.
The detector directly parses plain exact strings (`0`, `100`, `100.00`, `-50.25`)
to Decimal, with no float conversion. Other configured fields can carry null or
higher-precision strings supported by the general snapshot scalar contract.
Booleans, integers, objects, arrays, arbitrary text, exponent strings and non-finite
strings fail with the existing sanitized `detector_error`; invalid values are checked
even in a population too small for statistics. Snapshot violations fail earlier.

Null values are ignored by the detector. Missing values belong to
`business.missing_required_field`; no completeness finding is duplicated here.
`ignore_zero=true` removes exact zero, including signed decimal zero. Neither 0.01
nor -0.01 is zero. `ignore_negative=true` removes all values less than zero from
both statistics and findings. Otherwise negatives participate normally, supporting
refunds/credits without declaring them invalid transactions.

Empty grouping fields mean the entire eligible table is one population. Configured
groups use ordered values encoded with the framework's type-safe canonical JSON,
just as composite matching does. Null, empty string, zero, false and string "0"
remain distinct; null group keys never exclude a row. Nested snapshot JSON retains
array order and canonical object keys. No case folding or whitespace trimming occurs.
Use currency where mixed currencies would make one monetary population meaningless.
Payments include currency and invoice_id, but no vendor_id; requirements reject
vendor_id on that table. Composite grouping is configurable, never hardcoded.

Each group independently needs `minimum_sample_size` eligible values **after**
null/zero/negative filtering. Seven values with minimum eight produce zero findings;
eight are evaluated. Small populations are not errors. **If IQR=0, emit zero findings**,
even if a minority of records differ. The selected rule has no useful spread for its
fence; it never switches to another algorithm. This is an explicit detection limitation.

### Decimal serialization and precision

Statistics serialize in plain notation with at least two fractional places, preserving
the snapshot money convention and retaining any necessary sub-cent digits:
`Decimal("100.00") -> "100.00"`, `Decimal("2.5") -> "2.50"`,
`Decimal("0.0150") -> "0.015"`, negative zero -> `"0.00"`.
No exponent, locale formatting, float conversion or context-sensitive `normalize()`
is used. Original amount spelling stays in evidence; multiplier retains its validated
canonical configuration string, e.g. `"1.5"`.

A fresh Decimal Context sizes precision from integer and fractional spans of the
population and multiplier, with room for products, carries and division by two.
It fixes exponent bounds and does not inherit caller precision, rounding or traps.
Tests cover 0.10/0.20/0.30, sub-cent quartiles, high-precision configured strings,
999999999999999999.99 and hostile ambient Decimal settings. No new numerical library
is used. Existing legacy Pandas dependency health remains unchanged; this rule does
not import or use it.

### Findings and minimal evidence

Each outlier record produces exactly one finding, entity_type=configured table and
entity_id=configured record ID. Statistical group identity never replaces record
identity. The existing Finding contract has no content property, so its single
evidence item's context holds the structured statistical summary. It contains no
full sample, unrelated columns or quartile-boundary records.

Example evidence for the fixture (generated evidence ID omitted):

```json
{
  "source_table": "payments",
  "source_record_id": {"id": "00000000-0000-4000-a000-000000000008"},
  "field": "amount",
  "observed_value": "100.00",
  "context": {
    "amount_field": "amount", "amount": "100.00", "direction": "upper",
    "q1": "11.50", "q3": "15.50", "iqr": "4.00", "iqr_multiplier": "1.5",
    "lower_fence": "5.50", "upper_fence": "21.50", "sample_size": 8,
    "group_by_fields": ["currency"], "group_values": ["IDR"]
  }
}
```

The [complete canonical example result](../audit-engine/fixtures/amount-outlier/example-result.json)
contains one finding for 100.00 among `[10,11,12,13,14,15,16,100]`.
The fixture uses eight payments and ten empty tables in the existing approved
snapshot inventory; it is a controlled statistical fixture, not a relational seed.

### Runnable policy and normal CLI

The [complete example policy](../audit-engine/policies/amount-outlier.json) enables
only amount outlier with all defaults except `group_by_fields=["currency"]`. It uses
minimum severity info, confidence 0.0, fail-on-error true and partial results false.
Existing policies and the default health selection are unchanged.

```powershell
$py='audit-engine/.venv/Scripts/python.exe'
$root='audit-engine/fixtures/amount-outlier'
& $py -m audit_engine policy validate audit-engine/policies/amount-outlier.json
& $py -m audit_engine --artifacts-dir $root run --snapshot 00000000-0000-4000-a000-000000000500 --policy audit-engine/policies/amount-outlier.json
# Use the printed Audit Run ID:
& $py -m audit_engine --artifacts-dir $root result inspect <audit-run-id>
```

### Determinism, performance, boundaries and limitations

Finding/evidence IDs use existing canonical content hashing. Amount, record identity,
group and statistics affect findings; effective configuration, version and the whole
snapshot affect the logical hash. Row/dictionary order, run ID, timestamp, operator,
artifact root and snapshot artifact ID do not. Tests retain all prior detector
goldens and a pre-change duplicate-payment policy/config/hash baseline.

Population construction is O(n × f) for bounded grouping values. Sorting costs
sum O(ng log ng) across evaluated groups; only one amount sort per group occurs.
Quartiles and scanning are linear, with O(n × f) memory plus findings; canonical
finding ordering adds O(k log k). Decimal arithmetic cost depends on digit count,
and nested grouping JSON cost depends on its size. No pairwise record comparisons
or repeated full-sample evidence copies exist.

Only frozen AuditContext and validated DetectorConfig reach this trusted in-process
detector. It adds no database/credential, environment, filesystem, network, subprocess
or dynamic-import capability. No ML, external analytics or dependencies were added.

Limitations: IQR only; exact configured single-table populations; no seasonal
adjustment, peer benchmarking, contextual/fuzzy detection, cross-table context or
fallback for zero-IQR/small populations. Statistical outliers are review candidates,
not proof of error or fraud. Production/Railway remains unverified.

ADR practices were inspected: existing ADRs govern architectural boundaries and
contracts. This rule adds no such boundary. Its versioned statistical methodology
and serialization are specified here rather than creating an implementation ADR.
Recommend Rule Pack v1 integration and production-readiness next: representative
reference, completeness, sequence, payment and statistical controls now exist.
