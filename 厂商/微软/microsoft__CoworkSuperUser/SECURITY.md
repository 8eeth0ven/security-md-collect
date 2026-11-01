# Security

The repository and distributed release assets are classified **Public**.

The distributed PBIT is data-free, has an unset `DataFolder` parameter, and
contains no imported model cache. Power BI does not retain Purview sensitivity
labels in PBIT exports, so the Public classification is documented in the
repository rather than embedded in the template.

The distributed PBIX contains only generated synthetic data. Validation found
no email addresses, customer query identifiers, or local user-profile paths in
the packaged PBIT or PBIX.

Do not commit production CSV exports, customer PBIX files, tenant identifiers,
local source paths, Power BI cache folders, or credentials.

## Report data

- The Consumption Dashboard export contains user-level metrics. Identifiers are
	anonymized by default, but administrators can enable identifiable export.
- Person-level data remains customer-controlled.
- Person IDs displayed by the report are source identifiers and may still be
	personal data even when pseudonymous.
- Dashboard or export access does not authorize onward sharing. Limit access to
	the approved purpose and audience.
- Customers must validate their authorized purpose, workspace permissions, retention, export handling, and downstream sharing.
- No row-level security role is preconfigured in the public template. Add and
	test the required roles before sharing populated reports with restricted
	audiences.
- Apply the organization's required sensitivity label after loading production
	data and before publishing or sharing the report.

## Reporting a vulnerability

Follow the [Microsoft Security Response Center reporting guidance](https://aka.ms/security.md). Do not include customer data, query identifiers, or credentials in a public GitHub issue.
