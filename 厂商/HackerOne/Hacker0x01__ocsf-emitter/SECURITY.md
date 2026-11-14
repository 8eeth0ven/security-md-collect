# Security Policy

## Supported versions

Security fixes are applied to the latest released minor version. We recommend
always running the most recent release.

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |
| older   | :x:                |

## Reporting a vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, report them privately using GitHub's
[private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
("Report a vulnerability" under the repository's **Security** tab), or email the
maintainers.

Please include:

- A description of the issue and its impact.
- Steps to reproduce (a minimal proof of concept if possible).
- Affected version(s) and environment details.

We will acknowledge receipt within a few business days and keep you updated on
remediation progress. Please give us a reasonable window to release a fix before
any public disclosure.

## Scope notes for this library

`ocsf-emitter` constructs and validates OCSF Detection Findings; it does not
perform network I/O at runtime (transport is the caller's responsibility). When
assessing risk, consider:

- **Untrusted input to builders.** Fields you pass into `build_detection_finding`
  are placed into the OCSF payload. Validate/handle sensitive data upstream;
  runtime validation guarantees OCSF *shape*, not that field *contents* are safe
  for a given downstream consumer.
- **Generated models.** `src/ocsf_emitter/_models.py` is generated from the
  pinned OCSF schema. Regenerating from an untrusted schema source is out of
  scope for the security guarantees of a release.
