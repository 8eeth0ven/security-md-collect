# Security

## Reporting a security issue

If you discover a potential security issue in this project, please follow the process in
[CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications). Do **not** create a public
GitHub issue for security reports.

## Demo status

This repository is a **demonstration** and is **not production-ready as-is**. Most notably,
the enrollment attestation check is a stub that accepts any non-empty token. Review the blog
post and [`terraform/README.md`](terraform/README.md) for what to harden before production.

## Checkov suppressions (Terraform)

The Terraform is scanned with [Checkov](https://www.checkov.io/). The findings below are
intentionally suppressed with inline `#checkov:skip=<ID>:<reason>` comments because they are
acceptable trade-offs for a domain-free demo, not false positives (except where noted).
Review and address them before any production use.

| Check | Resource | Skipped because (demo) |
|---|---|---|
| `CKV_AWS_150` | Internal ALB | Deletion protection off so the stack tears down cleanly with `terraform destroy`. Enable it for production. |
| `CKV_AWS_2` | ALB HTTP listener | Internal ALB; TLS terminates at CloudFront and the origin hop stays on the AWS private network. Bring a custom domain + ACM cert for end-to-end TLS. |
| `CKV_AWS_260` | ALB SG ingress | **False positive.** Ingress is restricted to the CloudFront managed VPC-origin security group, not `0.0.0.0/0`. |
| `CKV_AWS_174` | CloudFront distribution | Default `*.cloudfront.net` certificate ignores `minimum_protocol_version`, so the viewer TLS version cannot be raised. Bring a custom domain + ACM cert for production. |
| `CKV_AWS_305` | CloudFront distribution | API distribution, not a website; there is no default root object to serve. |
| `CKV_AWS_86` | CloudFront distribution | Access logging off to keep the sample minimal. Enable CloudFront access logging for production. |
