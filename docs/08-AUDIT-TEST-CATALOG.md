# Planned audit test catalog

No rules are implemented. These are project-defined procedures, not professional standards. All tests require validated population completeness and a frozen as_of, source manifest and test version. Expected result is zero unexplained exceptions, not an assurance opinion. Missing required data yields error/inconclusive, never pass. Severity is initial review guidance; assess context and impact before a finding.

## UA-001 Dormant Account

- Test ID: UA-001
- Name: Dormant Account
- Objective: Identify unused access remains available.
- Risk addressed: Unused access remains available.
- Required data: users status, last_login_at, created_at.
- Detection logic: For active human accounts compare last_login_at, or created_at when never used, to frozen as_of minus configurable 90 days; service accounts reviewed separately.
- Expected result: No unexplained matches within a valid, complete population.
- Exception criteria: One active account beyond threshold.
- Severity guidance: medium; human review may adjust with a documented reason.

## UA-002 Inactive User With Access

- Test ID: UA-002
- Name: Inactive User With Access
- Objective: Identify former employees retain access.
- Risk addressed: Former employees retain access.
- Required data: employees status, users employee_id and status.
- Detection logic: Join human accounts to employees; flag active account with inactive employee; missing employee is a data-quality error.
- Expected result: No unexplained matches within a valid, complete population.
- Exception criteria: One enabled account linked to inactive employee.
- Severity guidance: high; human review may adjust with a documented reason.

## UA-003 Excessive Privilege

- Test ID: UA-003
- Name: Excessive Privilege
- Objective: Identify access exceeds job need.
- Risk addressed: Access exceeds job need.
- Required data: users, roles, permissions, approved baseline.
- Detection logic: Expand effective permission sets and compare to versioned approved job/account baseline; missing baseline makes test inconclusive.
- Expected result: No unexplained matches within a valid, complete population.
- Exception criteria: One account with any unauthorized permission.
- Severity guidance: high; human review may adjust with a documented reason.

## SOD-001 Create and Approve Invoice

- Test ID: SOD-001
- Name: Create and Approve Invoice
- Objective: Identify one person controls both invoice steps.
- Risk addressed: One person controls both invoice steps.
- Required data: user_roles, role_permissions, permissions, sod_rules.
- Detection logic: Intersect effective invoice.create and invoice.approve account sets, including permissions obtained through different roles.
- Expected result: No unexplained matches within a valid, complete population.
- Exception criteria: One account/rule pair with both capabilities.
- Severity guidance: high; human review may adjust with a documented reason.

## SOD-002 Create and Confirm Payment

- Test ID: SOD-002
- Name: Create and Confirm Payment
- Objective: Identify one person controls disbursement.
- Risk addressed: One person controls disbursement.
- Required data: user_roles, role_permissions, permissions, sod_rules.
- Detection logic: Intersect payment.create and payment.confirm sets; entitlement conflict is distinct from observed self-confirmation.
- Expected result: No unexplained matches within a valid, complete population.
- Exception criteria: One account/rule pair with both capabilities.
- Severity guidance: high; human review may adjust with a documented reason.

## TX-001 Duplicate Invoice

- Test ID: TX-001
- Name: Duplicate Invoice
- Objective: Identify liability recorded twice.
- Risk addressed: Liability recorded twice.
- Required data: invoices, vendors.
- Detection logic: Group by vendor, normalized reference (trim and uppercase), currency and exact decimal amount; groups of size greater than one are candidates, excluding void records.
- Expected result: No unexplained matches within a valid, complete population.
- Exception criteria: One duplicate group; also report member IDs and excess record count.
- Severity guidance: medium; human review may adjust with a documented reason.

## TX-002 Duplicate Payment

- Test ID: TX-002
- Name: Duplicate Payment
- Objective: Identify cash disbursed twice.
- Risk addressed: Cash disbursed twice.
- Required data: payments, invoices.
- Detection logic: For confirmed payments group by invoice_id, normalized payment reference, currency and amount; broader amount/date similarity is separate future heuristic.
- Expected result: No unexplained matches within a valid, complete population.
- Exception criteria: One duplicate group; partial payments with different references do not match.
- Severity guidance: high; human review may adjust with a documented reason.

## TX-003 Payment Greater Than Invoice

- Test ID: TX-003
- Name: Payment Greater Than Invoice
- Objective: Identify overpayment.
- Risk addressed: Overpayment.
- Required data: payments, invoices.
- Detection logic: Sum confirmed payments per invoice and currency using decimals; compare to invoice amount; mixed currencies fail validation; no FX guessing.
- Expected result: No unexplained matches within a valid, complete population.
- Exception criteria: One invoice whose cumulative confirmed payments exceed amount.
- Severity guidance: high; human review may adjust with a documented reason.

## TX-004 Invoice Without Approval

- Test ID: TX-004
- Name: Invoice Without Approval
- Objective: Identify unapproved obligation paid.
- Risk addressed: Unapproved obligation paid.
- Required data: invoices, invoice_approvals, payments.
- Detection logic: For approved/paid invoices or confirmed payments require a latest applicable approval before payment; later rejection invalidates earlier approval; policy version required.
- Expected result: No unexplained matches within a valid, complete population.
- Exception criteria: One invoice lacking valid approval; do not flag ordinary drafts.
- Severity guidance: high; human review may adjust with a documented reason.

## TX-005 Inactive Actor Transaction

- Test ID: TX-005
- Name: Inactive Actor Transaction
- Objective: Identify disabled account activity.
- Risk addressed: Disabled account activity.
- Required data: users, employees, audit_logs and status history.
- Detection logic: Compare event time to account/employment effective status history; current status alone is insufficient.
- Expected result: No unexplained matches within a valid, complete population.
- Exception criteria: One event by an inactive actor at that instant.
- Severity guidance: high; human review may adjust with a documented reason.

## TX-006 Unusual Transaction Time

- Test ID: TX-006
- Name: Unusual Transaction Time
- Objective: Identify unreviewed out-of-hours activity.
- Risk addressed: Unreviewed out-of-hours activity.
- Required data: audit_logs, calendar and timezone policy.
- Detection logic: Convert occurred_at using frozen organization timezone and compare to approved schedule; missing calendar is inconclusive.
- Expected result: No unexplained matches within a valid, complete population.
- Exception criteria: One out-of-schedule event.
- Severity guidance: low; human review may adjust with a documented reason.

## TX-007 Missing Supporting Evidence

- Test ID: TX-007
- Name: Missing Supporting Evidence
- Objective: Identify unsupported transaction.
- Risk addressed: Unsupported transaction.
- Required data: invoices supporting_reference.
- Detection logic: Check submitted/approved/paid invoices for absent or invalid synthetic evidence references; never fetch arbitrary user URLs.
- Expected result: No unexplained matches within a valid, complete population.
- Exception criteria: One unsupported invoice.
- Severity guidance: medium; human review may adjust with a documented reason.

## LOG-001 Post-Approval Modification

- Test ID: LOG-001
- Name: Post-Approval Modification
- Objective: Identify approved details changed.
- Risk addressed: Approved details changed.
- Required data: audit_logs, invoice_approvals.
- Detection logic: Order events by time and stable event ID; compare material amount/vendor/currency changes after applicable approval; approved correction policy required.
- Expected result: No unexplained matches within a valid, complete population.
- Exception criteria: One material modification event without reapproval.
- Severity guidance: high; human review may adjust with a documented reason.

## LOG-002 Manual Payment Override

- Test ID: LOG-002
- Name: Manual Payment Override
- Objective: Identify workflow bypass.
- Risk addressed: Workflow bypass.
- Required data: audit_logs.
- Detection logic: Match explicit payment.status_overridden action or documented override metadata; normal confirmation is not override.
- Expected result: No unexplained matches within a valid, complete population.
- Exception criteria: One override event for review.
- Severity guidance: high; human review may adjust with a documented reason.

## LOG-003 Privilege Change

- Test ID: LOG-003
- Name: Privilege Change
- Objective: Identify unauthorized access change.
- Risk addressed: Unauthorized access change.
- Required data: audit_logs, role and permission snapshots.
- Detection logic: Select role/permission assignment changes; compare actor authorization and approved change reference when available.
- Expected result: No unexplained matches within a valid, complete population.
- Exception criteria: One unapproved change; changes alone are review candidates.
- Severity guidance: medium; human review may adjust with a documented reason.

## LOG-004 Deletion or Unusual Administration

- Test ID: LOG-004
- Name: Deletion or Unusual Administration
- Objective: Identify concealed records or administrative misuse.
- Risk addressed: Concealed records or administrative misuse.
- Required data: audit_logs, administrative policy.
- Detection logic: Select deletion and privileged maintenance actions; compare to approved activity windows and change records.
- Expected result: No unexplained matches within a valid, complete population.
- Exception criteria: One unexplained administrative event.
- Severity guidance: high; human review may adjust with a documented reason.

## Phase 1 source availability and fixture mapping

No procedures are implemented. All fixtures refer to [ground-truth.json](../database/sample-data/ground-truth.json), accessible only to the test harness. The [fixture policy](../database/sample-data/fixture-policy.json) is independent expected configuration. Existing IDs retain their definitions; an observed transaction conflict is not the same unit as a permission entitlement conflict.

| Planned test | Required business tables | Required fields / additional policy | Ground-truth fixture |
| --- | --- | --- | --- |
| UA-001 | users | status, account_type, last_login_at, created_at; fixed asOf and 90-day threshold | AC-002: 12 accounts |
| UA-002 | employees, users | employee_id, employee status, account status | AC-001: 8 accounts |
| UA-003 | users, roles, user_roles, role_permissions, permissions | user_id, role_id, permission_id, code, is_privileged; allowedRoles baseline | AC-003: 6 accounts |
| SOD-001 | user_roles, role_permissions, permissions | role/permission joins and invoice.create/invoice.approve; future rule config | No entitlement conflicts in v1; observed fixture is SOD-003 below |
| SOD-002 | user_roles, role_permissions, permissions | role/permission joins and payment.create/payment.confirm; future rule config | No entitlement conflicts in v1; observed fixture is SOD-004 below |
| SOD-003 | invoices, invoice_approvals | id, created_by, invoice_id, decided_by, decision | Fixture SOD-001: 10 invoices |
| SOD-004 | payments | id, created_by, confirmed_by, status | Fixture SOD-002: 8 payments |
| TX-001 | invoices, vendors | vendor_id, reference, amount, currency, status | TX-001: 10 groups / 20 members |
| TX-002 | payments, invoices | invoice_id, reference, amount, currency, status | TX-002: 12 groups / 24 members |
| TX-003 | payments, invoices | invoice_id, amount, currency, status | TX-003: 8 invoices |
| TX-004 | invoices, invoice_approvals, payments | invoice_id, status, decision, decided_at, created_at | TX-004: 10 invoices |
| TX-005 | employees, users, audit_logs | hired_at, ended_at, employee_id, actor_id, occurred_at, action | TX-005: 8 invoice.created events after employment end; account-disable history remains unavailable |
| TX-006 | audit_logs | occurred_at, action; fixed timezone/calendar | TX-006: 20 invoice/payment creation events; broader event populations need separate expectations |
| TX-007 | invoices | supporting_reference, status | Clean negative population; no missing-reference anomaly injected |
| LOG-001 | audit_logs, invoice_approvals, invoices | entity_id, before_data, after_data, occurred_at, decided_at | LOG-001: 10 material-change events |
| LOG-002 | audit_logs, payments | action, entity_id, before_data, after_data | LOG-002: 8 override events |
| LOG-003 | audit_logs, roles, role_permissions, permissions | action, actor_id, entity_id, before_data.role_id, after_data.role_id, after_data.change_reference | LOG-003: 12 unapproved changes |
| LOG-004 | audit_logs | action and administrative policy | No deletion/maintenance fixture; remains planned |

### SOD-003 Observed invoice self-approval (planned)

Objective: identify a creator who actually approved their own invoice. Compare invoices.created_by with approved invoice_approvals.decided_by. Exception unit: one invoice, regardless of multiple matching decisions. This supplements, and does not replace, entitlement test SOD-001. Severity guidance: high, subject to human review. Missing source relationships produce inconclusive/error.

### SOD-004 Observed payment self-confirmation (planned)

Objective: identify a creator who actually confirmed their own payment. Compare created_by and confirmed_by on confirmed payments. Exception unit: one payment. This supplements entitlement test SOD-002. Severity guidance: high, subject to human review. Missing confirmation facts produce data-quality error.

Phase 1 approval convention: latest decision by decided_at then id wins; rejection invalidates prior approval. V1 uses one decision per applicable invoice, so repeated-decision boundary coverage remains future work. The existing TX-005 broader account-status test cannot infer historical disablement from current status: v1 benchmarks only employment-ended creation events. This scope is explicit to prevent misleading accuracy claims.
