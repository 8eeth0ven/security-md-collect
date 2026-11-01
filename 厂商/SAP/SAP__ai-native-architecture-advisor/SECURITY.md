# Security Policy

## Reporting a Vulnerability

SAP takes security bugs seriously. We appreciate your efforts to responsibly
disclose your findings, and will make every effort to acknowledge your
contributions.

Please **do not report security vulnerabilities through public GitHub issues,
discussions, or pull requests.**

Instead, report any security vulnerability you discover to SAP as described in
the [SAP Trust Center — Security Issue reporting](https://www.sap.com/about/trust-center/security/incident-management.html)
page. This is the central, monitored channel for all SAP products and open
source projects.

Please include as much of the information listed below as you can to help us
better understand and resolve the issue:

- The type of issue (e.g. input handling, information disclosure, dependency
  vulnerability).
- Full paths of source file(s) related to the manifestation of the issue.
- The location of the affected source code (tag/branch/commit or direct URL).
- Any special configuration required to reproduce the issue.
- Step-by-step instructions to reproduce the issue.
- Proof-of-concept or exploit code (if possible).
- Impact of the issue, including how an attacker might exploit it.

## Scope

This project is a prompt-and-reference plugin for Claude Code and Codex. It
ships instructions, curated reference data, and a local Node.js HTML publisher.
It stores no secrets and makes no network calls of its own; generated reports
embed their assets and load nothing remote. When reporting, note that the AI
host (Claude Code / Codex) and its model connection are outside the scope of
this repository.
