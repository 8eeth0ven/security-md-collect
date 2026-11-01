# Security Policy

`rust-cache-benchmarks` is a benchmark harness — it has no network surface,
no filesystem writes, no privileged operations, and is not deployed into any
production system. Its threat model is therefore narrow:

- Bugs in benchmark methodology, statistical reporting, or workload generation
  that could mislead someone evaluating a cache library.
- Supply-chain risks introduced by transitive dependencies (monitored by the
  `audit` job in CI).
- Any future `unsafe` code (the project currently has none).

## Reporting a vulnerability

**Please do not file public GitHub issues for security reports.** Use one of
the following private channels:

1. **GitHub Security Advisories** (preferred) — open a draft advisory at
   <https://github.com/Shopify/rust-cache-benchmarks/security/advisories/new>.
   This keeps disclosure private and gives us a structured channel to
   coordinate a fix and a CVE if warranted.
2. **Shopify HackerOne program** — <https://hackerone.com/shopify>. This is
   the org-wide channel and is appropriate for anything that touches the
   broader Shopify platform. Note that this benchmark utility is generally
   out of scope for the bug bounty program; reports here will be routed and
   acknowledged but typically do not qualify for a reward.

We will acknowledge receipt of a report within five business days and aim
to publish a fix or coordinated disclosure within thirty days for confirmed
issues. Please give us a reasonable time window to investigate before any
public disclosure.

## Reporting a benchmark methodology bug

Methodology bugs (unfair tuning, biased ordering, broken statistics,
mis-applied warmup) are not security issues but we treat them seriously
because they affect public trust in the comparison. Open a regular issue or
PR — public discussion is encouraged.

## Receiving security updates

Watch this repository on GitHub and subscribe to its releases to be notified
when a security-relevant fix is published.
