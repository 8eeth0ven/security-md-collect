# Security Policy

## Reporting a Vulnerability

There are two ways to report a vulnerability:

- [Vercel's Open Source bounty program on HackerOne](https://hackerone.com/vercel-open-source) **recommended**
- The security tab on the GitHub repository in question ([see documentation](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability#privately-reporting-a-security-vulnerability)). Vulnerabilities disclosed via GitHub are not eligible for a bounty

**Do not open a public issue.**

Please refer to the [Vercel Open Source program instructions](https://hackerone.com/vercel-open-source) for details. In general you need to provide:

- A clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Potential impact
- A proof of concept if possible
- Affected commit / version (if known)

## Timeline

If you report the vulnerability through HackerOne, the timelines mentioned there apply.

If a security vulnerability is reported outside of this, we aim to acknowledge receipt of a valid report within 2 weeks, and aim to provide a remediation plan or decision within 4 weeks. Actual fix time may be shorter or longer depending on severity, complexity, and scope.

## Scope & Threat Model

In scope:

- Vulnerabilities introduced by code in this repository
- Supply-chain risks caused by how this repository consumes or distributes its own code (e.g. insecure Github Actions)

Out of scope:

- Issues only present in third-party dependencies (please report those upstream)
- Issues that can only be exploited when the underlying platform (browser, server runtime) is compromised
- Using untrusted user content without sanitization in places that are not explicitly sanitized by the framework (for example in Svelte putting user content into `{@html ...}` is unsanitized, `{...}` is sanitized insofar as the content cannot alter the HTML structure to e.g. insert script tags)
- Denial of service via excessive legitimate use
- Issues only present in experimental features explicitly marked as such (e.g. where you have to opt in to them via a Svelte compiler flag)
- Denial of service that is dev-time only, e.g. specific string handed to the Svelte compiler that take a long time to compile. Please report those as regular issues.

## Disclosure

Please keep reports private until a fix is released and a Security Advisory is public.

## CVE Publication

By default, we do not publish CVEs for vulnerabilities solely affecting experimental features, though we may opt to publish one if the vulnerability is unusually severe or easy to exploit. An experimental feature is one that is clearly gated behind an `experimental.{name}` configuration flag.

We reserve the right to publish our own CVEs. Please do not pre-reserve CVE records or attempt to publish your own CVE. If we do publish a CVE, we will ensure you receive credit for your discovery and any work you may do to help patch it.
