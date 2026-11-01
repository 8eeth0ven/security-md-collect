# Security Policy

## Scope

This repository contains **reference customization examples** for IBM Order Management System. The examples are intended as patterns and starting points. They are not a deployable product and do not have formal versioned releases.

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security issue in one of the examples in this repository — for example, an insecure coding pattern, exposed credentials, or a vulnerable dependency used in an example — please report it responsibly by contacting a maintainer directly via GitHub (see [MAINTAINERS.md](MAINTAINERS.md)).

Please include in your report:

- **Subject / opening line:** `[SECURITY] oms-reference-customizations — brief description`
- A description of the issue and its potential impact
- The file(s) or example(s) affected
- Steps to reproduce or demonstrate the issue
- Any suggested remediation, if you have one

We will acknowledge your report within **3 business days** and aim to address confirmed issues promptly. We follow a **90-day responsible disclosure timeline** — we ask that you do not publicly disclose the issue until a fix has been released or the timeline has elapsed.

## Security Expectations for Examples

All examples in this repository are expected to follow secure coding practices:

- No hardcoded credentials, API keys, tokens, or internal IBM URLs
- Use of environment variables or placeholder values for any sensitive configuration
- Dependencies pinned to versions without known critical CVEs

If you notice an example that does not meet these expectations, please open an issue or pull request to address it.
