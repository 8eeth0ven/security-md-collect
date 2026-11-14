# Security policy

## Reporting a vulnerability

Report security issues in these plugins to **security@defectdojo.com**. Please
do not open a public issue for a security problem.

Include what you did, what happened, and the version from the `VERSION` file or
the release tag. We will acknowledge receipt and keep you informed as we work
through it.

For vulnerabilities in DefectDojo itself rather than in these plugins, follow
the disclosure process at [defectdojo.com](https://defectdojo.com).

## How credentials are handled

Understanding this makes it easier to judge what is and is not a vulnerability.

- Your API token is entered once, when the plugin is enabled, and is stored by
  Claude Code in the operating system keychain.
- It is written to `~/.defectdojo/claude-code.json` with owner-only permissions
  (0600) at session start, so the `dd-api` command can read it. This is the same
  trust model as `~/.netrc` or `~/.aws/credentials`.
- The token is sent only to the instance URL you configured, as an
  `Authorization: Token` header.
- It is never passed on a command line, so it does not appear in the process
  table. It is never printed, including in verbose output, where it is redacted.
- The model never sees the token. Skills are prohibited from referencing it.
- Every action runs as your DefectDojo user, under your existing permissions.
  The plugin cannot do anything in DefectDojo that you cannot do yourself.

If you prefer no credential on disk, set `DD_BASE_URL` and `DD_API_TOKEN` in the
environment instead. They take priority over the file.

## If a token is exposed

Revoke it in DefectDojo and issue a new one. Tokens are revocable from your user
profile. If a token appeared in a conversation transcript, treat it as
compromised.

## Scope

These plugins send data only to the DefectDojo instance you configure. They do
not send telemetry anywhere, and they add no third-party network destinations.
