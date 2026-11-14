# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | ✅ Yes    |

## Reporting a Vulnerability

**Do not open a GitHub issue for security vulnerabilities.**

Auth0 takes security seriously. If you discover a vulnerability in any module in this repository, please report it through Auth0's responsible disclosure program:

**https://auth0.com/responsible-disclosure**

Include:
- A description of the vulnerability and its potential impact
- Steps to reproduce or a proof-of-concept
- The affected module, its version, and the Terraform provider version

**What to expect:**
- Acknowledgement within 48 hours
- A patch for critical vulnerabilities within 30 days
- Credit in the release notes (unless you prefer to remain anonymous)

## Scope

These modules manage Auth0 tenant configuration via Terraform. Security issues in scope include:

- Insecure default variable values that result in a misconfigured Auth0 tenant
- Sensitive values (client secrets, certificates) being exposed in Terraform state or plan output in an unexpected way
- Incorrect resource ordering that could create a window of misconfiguration during apply

Issues with the underlying `auth0/auth0` Terraform provider should be reported to the provider repository at `https://github.com/auth0/terraform-provider-auth0`.
