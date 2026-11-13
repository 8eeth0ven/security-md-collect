# Security Policy

## Reporting Security Issues

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a potential security issue in this project, notify AWS/Amazon Security
via the [vulnerability reporting page](https://aws.amazon.com/security/vulnerability-reporting/).

You will receive a response from the security team within 24 hours. If you do not receive
a response, please follow up via email to ensure your report was received.

Please include as much of the following information as possible to help us understand the
nature and scope of the issue:

- Type of issue (e.g., exposed credential, insecure configuration, code injection)
- Location of the affected source file (path, tag, branch, or commit)
- Steps to reproduce the issue
- Proof-of-concept or exploit code (if available)
- Potential impact of the issue

This information will help us triage your report more quickly.

## This Repository Contains Reference Code

This repository contains example code and templates intended for educational use. It does
**not** deploy live infrastructure or handle real data. Security issues of interest include:

- Credentials, secrets, or account IDs accidentally committed to any example
- Hook scripts that could be used for command injection
- Workflow YAML that unsafe-interpolates user-controlled input (e.g., PR titles or bodies
  into shell or script bodies — see `templates/workflows/README.md` for the explicit
  guidance on passing PR content through `env:` rather than `${{ }}` interpolation)
- Insecure Terraform patterns in example infrastructure code
- Any `[PLACEHOLDER]` values in templates that, if left unfilled, would create a security
  misconfiguration in a real deployment

## Supported Versions

This is a reference repository with no versioned releases. Security fixes are applied to
the `main` branch only.
