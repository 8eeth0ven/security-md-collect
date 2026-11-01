# Security Policy

## Reporting a Vulnerability

If you discover a potential security issue in this project, we ask that you notify AWS Security via our [vulnerability reporting page](https://aws.amazon.com/security/vulnerability-reporting/). Please do **not** create a public GitHub issue for security vulnerabilities.

## Scope

This repository contains a static JSON dataset with no executable code. Security concerns for this project include:

- **Data integrity:** Incorrect lifecycle dates or statuses that could cause consumers to make flawed operational decisions
- **Source authenticity:** Broken or manipulated `sourceUrl` references that undermine the verification model
- **Supply-chain trust:** Unauthorized modifications to the dataset that bypass the review process

## Security Controls

- All data changes require CODEOWNERS approval before merge
- CI validates the JSON schema (including an official AWS `sourceUrl` on every documentation-sourced entry), date consistency, and freshness on every change
- Every `behavior` and every documentation-sourced entry links official AWS documentation for independent verification; API-sourced dates come from the AWS Health Version Catalog (`DescribeServiceLifecycle`)
- The `generatedAt` field shows when the dataset was last checked against its sources, and `lastUpdated` when the data last changed

## Consumer Guidance

- For critical business decisions (upgrade deadlines, cost forecasting, compliance), always verify dates against the official AWS documentation linked in the entry (`behavior.sourceUrl`, or `provenance.sourceUrl` for documentation-sourced entries)
- Pin to tagged releases rather than tracking the main branch for production integrations
- Treat the `status` field as advisory; validate against date fields programmatically for automated decisions
