# AuditLens for stakeholders

AuditLens is a practice platform that helps an auditor review a fictional company's access and transactions. It uses synthetic data, not real client records.

An auditor will choose a review, run defined checks, examine the supporting records, ask for explanations and document findings. For example, the platform may notice that an account remains enabled after an employee becomes inactive.

A **control** is an expected safeguard, such as requiring someone else to approve an invoice. An **exception** is something the check flags for review. A **finding** is the auditor's supported conclusion after checking the explanation and evidence. An exception alone does not prove fraud or wrongdoing.

Data will come from a small Demo Business System that simulates employees, accounts, invoices, approvals, payments and activity history. AuditLens is designed to read those records without changing them. It saves its review work separately.

The future dashboard will show which data and time period were tested, run status, coverage, exception counts and finding severity/status. Failed tests and incomplete data must remain visible. Counts do not measure the whole organization's risk or establish that controls are effective.

Today there are placeholder pages, technical health checks and an offline-verified synthetic dataset with known examples of control failures. Loading the dataset into PostgreSQL remains unverified on this host. There are no completed audits, real findings or live business workflows yet.

