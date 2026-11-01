<!-- BEGIN MICROSOFT SECURITY.MD V0.0.9 BLOCK -->

## Security

Microsoft takes the security of our software products and services seriously, which includes all source code repositories managed through our GitHub organizations, which include [Microsoft](https://github.com/Microsoft), [Azure](https://github.com/Azure), [DotNet](https://github.com/dotnet), [AspNet](https://github.com/aspnet) and [Xamarin](https://github.com/xamarin).

If you believe you have found a security vulnerability in any Microsoft-owned repository that meets [Microsoft's definition of a security vulnerability](https://aka.ms/security.md/definition), please report it to us as described below.

## Reporting Security Issues

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them to the Microsoft Security Response Center (MSRC) at [https://msrc.microsoft.com/create-report](https://aka.ms/security.md/msrc/create-report).

If you prefer to submit without logging in, send email to [secure@microsoft.com](mailto:secure@microsoft.com).  If possible, encrypt your message with our PGP key; please download it from the [Microsoft Security Response Center PGP Key page](https://aka.ms/security.md/msrc/pgp).

You should receive a response within 24 hours. If for some reason you do not, please follow up via email to ensure we received your original message. Additional information can be found at [microsoft.com/msrc](https://www.microsoft.com/msrc). 

Please include the requested information listed below (as much as you can provide) to help us better understand the nature and scope of the possible issue:

  * Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
  * Full paths of source file(s) related to the manifestation of the issue
  * The location of the affected source code (tag/branch/commit or direct URL)
  * Any special configuration required to reproduce the issue
  * Step-by-step instructions to reproduce the issue
  * Proof-of-concept or exploit code (if possible)
  * Impact of the issue, including how an attacker might exploit the issue

This information will help us triage your report more quickly.

If you are reporting for a bug bounty, more complete reports can contribute to a higher bounty award. Please visit our [Microsoft Bug Bounty Program](https://aka.ms/security.md/msrc/bounty) page for more details about our active programs.

## Preferred Languages

We prefer all communications to be in English.

## Policy

Microsoft follows the principle of [Coordinated Vulnerability Disclosure](https://aka.ms/security.md/cvd).

<!-- END MICROSOFT SECURITY.MD BLOCK -->

## NexaMem Security Boundaries

Scope names and environment prefixes are logical namespaces, not authentication or authorization. Validate identifiers in the application and authorize access before each operation. Avoid delimiter and Redis-glob characters in untrusted scope components. Do not expose raw storage APIs or caller-controlled SQL fragments directly to users.

The configuration-driven facade enforces logical expiry on its record reads, listings, searches, and channel reads. It does not implement client-side encryption or automatically enforce quota or PII options. Policy/content-processing helpers are separate components. Protect stored content through application controls, filesystem/database permissions, network restrictions, and backing-service configuration.

Logical expiry is not a physical-deletion deadline: there is no background purge, audit/backup deletion, or transactional protection against concurrent replacements. Raw backend and legacy reads bypass facade expiry. The reserved metadata field `_nexamem_expires_at` must not be caller-supplied. Authorize `purge_expired()` carefully: without a scope it scans all scopes. See [retention guarantees](NEW_ARCHITECTURE.md#retention-and-lifecycle).

Redis collection TTL applies to shared hashes/indexes, and audit-stream TTL is refreshed on later events. These mechanisms do not provide immutable per-record retention, tamper evidence, or compliance certification. Redis checkpoint helpers use an environment/agent namespace rather than full user/session isolation.

TLS certificate verification is required on the repaired Redis paths. Do not disable it. Supply credentials through approved external configuration and prefer managed identity. Entra Redis connections use redis-entraid streaming renewal and token-derived usernames; close owned facades to stop renewal resources and release credentials. Key Vault-backed access keys require reconnecting after rotation. Verify actual Redis data-plane permissions, network policy, long-lived refresh, and failover before deployment.

File records use encoded names and atomic individual replacements, not transactions across all records/indexes. Account for Windows case-insensitivity, filename length, and concurrent writers. Back up stores and follow [migration guidance](LEGACY_API.md) before upgrading.

Framework adapters add no authorization or prompt-injection security boundary. Stored reference content may be untrusted; validate authorship and apply application trust controls before injecting it into agent context. Avoid duplicating Foundry-managed conversation state with application-managed history. Framework SDK telemetry and model-client data collection are outside NexaMem's instrumentation guarantees.

Unit tests use local stores, fakeredis, and mocked identity services. They are not a security audit or live Azure validation. Report vulnerabilities through MSRC using the instructions above, not public GitHub issues.
