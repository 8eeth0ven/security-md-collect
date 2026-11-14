# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please email **security@fireblocks.com** with:

- A description of the vulnerability
- Steps to reproduce the issue
- Any potential impact

We will acknowledge your report within 48 hours and work with you to understand and address the issue.

## Scope

This repository contains **reference implementations and tooling** for the Eth-Link protocol. It is not a production service. That said, we take security seriously in all code we publish.

Areas of particular concern include:

- HMAC signing and verification logic
- API key handling and authentication
- Input validation (Zod schemas, request parsing)

## Security Best Practices for Integrators

When building on this reference implementation:

- **Never hardcode API keys or secrets.** Use environment variables.
- **Always use HTTPS** in production. The `strict-ssl false` setting in `.yarnrc` is for local development only.
- **Validate all inputs** at your API boundaries. The Zod schemas in this repo can serve as a starting point, but use whatever validation approach fits your stack.
- **Verify HMAC signatures** on all responses to prevent tampering.
- **Rotate API keys** periodically and revoke compromised keys immediately.

## Supported Versions

Security fixes will be applied to the latest version on the `main` branch.
