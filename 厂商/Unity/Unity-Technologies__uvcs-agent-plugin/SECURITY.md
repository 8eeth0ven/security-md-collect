# Security policy

## Reporting a vulnerability

**Do not open a public GitHub issue for security problems.**

Report vulnerabilities to Unity's security team following the process at
<https://unity.com/security> (or use GitHub's private
[security advisory](https://github.com/Unity-Technologies/uvcs-agent-plugin/security/advisories/new)
form on this repository).

Please include what you found, how to reproduce it, and the impact you believe it has. We will
acknowledge your report and keep you informed as we investigate.

## Scope

This plugin ships documentation and skills that instruct an AI agent to run `cm` commands. The
security-relevant surface is therefore narrow but real:

- **Instructions that cause destructive or unintended UVCS operations** — for example a skill
  that leads an agent to check in, merge, undo, or delete without user confirmation. Treat this
  as a security issue, not just a bug.
- **Command injection or unsafe quoting** in documented commands or in `skills/*/scripts/`,
  especially where branch names, comments, or paths are interpolated.
- **Secret or data leakage** — a skill that encourages sending repository contents, credentials,
  tokens, server hostnames, or user data to a third party, or that instructs an agent to read
  credential files.
- **Prompt-injection footguns** — instructions that make an agent treat untrusted repository
  content (changeset comments, file contents, branch attributes) as commands to obey.

Vulnerabilities in the UVCS product itself, in the `cm` CLI, or in a UVCS server are **out of
scope for this repository** — report those through <https://unity.com/security> as Unity Version
Control issues.

## For users of this plugin

- Skills here are written to keep read operations free and to require explicit confirmation
  before anything that mutates a repository. If an agent using this plugin performs a mutating
  operation without asking, please report it.
- Review what your agent is about to run. `cm` acts with your credentials and your permissions.
