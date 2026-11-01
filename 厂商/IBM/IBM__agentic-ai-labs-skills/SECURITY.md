<!-- Copyright contributors to the Agentic AI Labs project -->
<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- This file was authored with the assistance of AI Tool: Claude Code (Claude Opus, Claude Sonnet) -->

# Security Policy

The Agentic AI Labs project takes security seriously. This document explains how
to report a vulnerability and what to expect in return.

## What this project is (and its threat model)

This repository contains **Markdown skills and slash commands** — natural-language
directives that AI coding agents interpret — plus the JSON manifests that
register them as a Claude Code marketplace. It ships **no executable code** and
exposes no APIs or network services. As a result, the security surface is
primarily about the **content** rather than a running program:

- **Prompt-injection / unsafe guidance** — a skill that could steer an AI agent
  toward destructive, insecure, or unintended actions.
- **Accidental disclosure** — credentials, internal hostnames, customer data, or
  other sensitive information committed into the content.
- **Supply-chain of guidance** — instructions that direct users to untrusted
  tools, packages, or endpoints.

The repository has no third-party dependencies and no build step, so it has no
software-composition (SCA) surface. Diagnostic procedures referenced by the
skills (such as the startup credential health check) are carried out by the
user's own coding agent in their own environment, not by anything shipped here.

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues,
pull requests, or discussions.** Public disclosure before a fix is available puts
users at risk.

Instead, use **either** of these private channels:

1. **GitHub private vulnerability reporting (preferred).** Go to the
   repository's **Security** tab → **Report a vulnerability**. This opens a
   private advisory visible only to the maintainers.

2. **IBM PSIRT.** Report to IBM's Product Security Incident Response Team via
   <https://www.ibm.com/trust/security-psirt>. IBM PSIRT coordinates triage and
   disclosure for IBM open source projects.

When reporting, please include as much of the following as you can:

- The file(s) and skill(s) affected.
- A description of the issue and why it is a security concern (e.g. the unsafe
  action an agent could be induced to take).
- Steps to reproduce or a proof-of-concept prompt, if applicable.
- Any suggested remediation.

## What to expect

- **Acknowledgement** of your report within **3 working days**.
- An initial assessment and severity triage, and we will keep you informed of
  progress toward a fix.
- For confirmed issues, remediation in the default branch and a security
  advisory crediting the reporter (unless you prefer to remain anonymous).
- We aim to remediate **High** and **Critical** severity issues promptly.
- This project follows a **90-day disclosure timeline**.

## Supported versions

This project is distributed as a rolling Claude Code marketplace. Security fixes
are applied to the **latest published content on the default branch (`main`)**.
There are no separately maintained release branches.

## Secure use of this content

These skills frequently reference credentials by **environment-variable name**
(for example `WO_API_KEY`, `WO_INSTANCE`) and use placeholders such as `<key>`.
They never contain real secrets, and the guidance instructs users to keep
secrets out of committed files. When you apply a skill in your own project,
follow that guidance: store credentials in your platform's secret manager or
environment, never in source control.

Contributors: see [CONTRIBUTING.md](CONTRIBUTING.md#security-and-secret-scanning)
for the content checklist and the secret-scanning hook.
