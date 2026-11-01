# Security

## Disclaimer

This repository contains **sample code for demonstration and educational purposes only**. It is intended to showcase performance optimization techniques for mainframe-refactored batch applications using AWS Transform for mainframe refactor. **Do not deploy this code in a production environment without performing additional security testing and hardening.**

---

## Secrets Management in Production

For production deployments, use [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html) to manage database credentials and sensitive configuration:

- Store database connection strings, passwords, and API keys in Secrets Manager rather than in environment variables, configuration files, or application code
- Enable automatic credential rotation using Secrets Manager's built-in rotation support for RDS/Aurora
- Use IAM roles to grant application-level access to secrets with least-privilege policies
- Reference secrets by ARN in application configuration and resolve them at runtime via the AWS SDK

For database-specific authentication, consider [IAM database authentication](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.html) for RDS/Aurora PostgreSQL to eliminate long-lived database credentials entirely.

---

## Reporting a Vulnerability

If you discover a potential security issue in this project, we ask that you notify AWS/Amazon Security via our [vulnerability reporting page](https://aws.amazon.com/security/vulnerability-reporting/) or directly via email to aws-security@amazon.com.

Please do **not** create a public GitHub issue for security vulnerabilities.
