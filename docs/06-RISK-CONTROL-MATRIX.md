# Initial risk and control matrix

**Project-defined sample controls only. These are not authoritative professional audit standards. All tests are planned.** Frequency is the proposed control operation frequency; audit execution frequency is configured separately.

| Risk ID | Risk | Risk description | Control ID | Control | Control type | Audit objective | Audit procedure | Evidence | Frequency | Expected result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R-001 | Unauthorized access | Former staff or dormant accounts retain access | C-001 | Access lifecycle review | Detective | Identify access no longer needed | UA-001/002 compare account activity and employment status | Employee/account snapshot and as_of | Monthly | No unexplained active inactive/dormant accounts |
| R-002 | Excess privileges | Effective permissions exceed approved responsibilities | C-002 | Approved access baseline | Preventive | Verify entitlement appropriateness | UA-003 compare effective permissions with approved baseline | Roles, permissions and versioned policy | On access change | Every privilege is approved |
| R-003 | SoD conflict | One account can initiate and authorize a transaction | C-003 | Incompatible permission restriction | Preventive | Identify incompatible capabilities | SOD-001/002 intersect effective permission sets | Assignments and SoD rule version | On role change | No unmitigated conflict |
| R-004 | Duplicate liability | Repeated invoice entered | C-004 | Invoice duplicate review | Detective | Identify candidate duplicate invoices | TX-001 group supplier/reference/amount/currency | Invoice and vendor extract | Each invoice | No unexplained duplicate group |
| R-005 | Duplicate or excess payment | Same liability paid repeatedly or too much | C-005 | Payment reconciliation | Detective | Identify repeated and excess disbursement | TX-002/003 group payments and sum by invoice | Confirmed payments and invoices | Daily | No duplicate or cumulative overpayment |
| R-006 | Approval bypass | Invoices paid without valid approval | C-006 | Approval gate | Preventive | Verify authorization precedes payment | TX-004 compare approval chronology | Invoices, decisions, payments | Each payment | Valid applicable approval |
| R-007 | Record manipulation | Approved data changed or workflow overridden | C-007 | Change monitoring | Detective | Identify unexplained changes | LOG-001/002/004 inspect events against policy | Before/after logs, change approvals | Daily | Every material change is explained |
| R-008 | Privilege manipulation | Role grants bypass approval | C-008 | Privileged change review | Detective | Verify change authorization | LOG-003 compare changes to approval evidence | Access events and change records | Daily | All changes authorized |

Risk → Control → Audit Test → Evidence → Result → Finding is the review trace. A result references a versioned test; evidence preserves source facts; a finding is a human assessment, not a mandatory output for every result.

