# Project audit workflow

This is a generic educational workflow defined for AuditLens. It does not implement PwC or any other proprietary methodology, and does not claim compliance with professional standards.

1. **Understand the process:** identify actors, transactions, systems and business boundaries.
2. **Identify risks:** describe what could go wrong and which assets are affected.
3. **Identify controls:** document expected preventive or detective actions and their owners.
4. **Define audit objectives:** state what the test should establish.
5. **Define audit procedures:** specify population, logic, evidence, thresholds and limitations.
6. **Obtain data:** use authorized read-only extraction and record source/time/version.
7. **Validate data:** check completeness, keys, missing values, amounts, timezone and reference integrity; stop or mark inconclusive if unusable.
8. **Perform testing:** run frozen logic against the defined population; preserve metrics and parameters.
9. **Identify exceptions:** retain matched record IDs and explainable reasons.
10. **Evaluate exceptions:** review context, false positives and compensating controls with an owner.
11. **Document findings:** describe supported condition, criteria, risk, impact, recommendation and ownership.
12. **Report results:** summarize coverage, exceptions, reviewed findings and limitations; avoid unsupported assurance claims.

A **risk** is a possible adverse event. A **control** is an action intended to reduce it. An **audit procedure** is the repeatable review method. An **exception** is a match to a deviation rule, not proof of misconduct. **Evidence** supports an observation and must have provenance. A **finding** is a reviewed conclusion connecting facts to expectations and impact. A **recommendation** proposes a practical response.

For example, an active former-employee account is an exception. Employment dates and access snapshots are evidence. After checking approved temporary access and actual exposure, an auditor may write a finding and recommend access removal. Zero matches mean only that this procedure found no deviations in the tested population.

