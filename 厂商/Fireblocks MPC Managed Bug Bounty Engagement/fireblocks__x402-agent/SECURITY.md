# Security

For a step-by-step guide to deploying this agent securely — Fireblocks API user scoping, secret storage, Policy Engine rules, and human-in-the-loop signing — see the [**Secure deployment**](README.md#secure-deployment) section in the README.

## Reporting a vulnerability

If you discover a security issue in this repository, please report it privately to:

**security@fireblocks.com**

Please do not open a public GitHub issue for security reports.

Include:

- A description of the issue and its potential impact.
- Steps to reproduce, ideally with a minimal proof-of-concept.
- Affected commit hash or release tag.
- Your name / handle for credit (optional).

We aim to acknowledge reports within two business days.

## Out of scope

- Vulnerabilities in upstream dependencies (Fireblocks SDK, ethers.js, `@modelcontextprotocol/sdk`, etc.) — please report to the respective maintainers.
- Issues that require an attacker to already control the Fireblocks API key, vault private key file, or the local machine running the agent.
- Mis-targeting attacks where an integrator is tricked into pointing the agent at a malicious merchant. The [Secure deployment](README.md#secure-deployment) guide describes the layered controls (Policy Engine destination whitelist, `ALLOWED_MERCHANT_HOSTS`, `REQUIRE_CONFIRM`) that defend against this.
