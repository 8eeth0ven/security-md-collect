# Security Policy

## Reporting a vulnerability

Please **do not** report security vulnerabilities through public GitHub issues.

Report them to Atlassian through the official channel:
<https://www.atlassian.com/trust/security/report-a-security-vulnerability>

Include enough detail to reproduce the issue: the plugin version
(`plugins/jira/.claude-plugin/plugin.json`), the Claude Code version, the
prompt or command that triggers it, and what you observed.

## Scope

This repository publishes agent plugin content — skills, agent definitions, hooks and
manifests. Reports of particular interest:

- Instruction content that can be steered into destructive or unauthorised writes
  against an Atlassian site.
- Hooks or scripts that exfiltrate prompt text, tokens, cloud IDs, or other user data.
- Anything that widens the access a user already had, rather than acting within it.

Vulnerabilities in the Atlassian products or CLIs the plugin talks to belong in the
Atlassian channel above; they are not fixed here.

## Beta status

This is a pre-release channel. Beta plugins are not covered by Atlassian product
support SLAs, but security reports are taken as seriously as for any other Atlassian
code.
