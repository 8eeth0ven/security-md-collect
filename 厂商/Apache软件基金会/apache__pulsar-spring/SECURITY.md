# Security Policy

The authoritative policy for Apache Pulsar projects is at <https://pulsar.apache.org/security/>; the Apache
Software Foundation's general process is at <https://www.apache.org/security/>. The latest version of this
file is maintained at <https://github.com/apache/pulsar-spring/security/policy> — in a fork, check there
rather than a possibly-stale local copy. The summary below is what contributors (and any AI tooling acting
on their behalf) must follow.

## Reporting a vulnerability

Do **not** open a public GitHub issue, pull request, or discussion for a suspected vulnerability — that
defeats coordinated disclosure.

Report it privately by email to the Apache Security Team at **security@apache.org** (the ASF's central
security address). When reporting to **security@apache.org**, you can copy your email to the Apache Pulsar
PMC's private list, **private@pulsar.apache.org**, to send your report to the Project Management Committee
as well.

**A human must verify and take responsibility for every security report.** Deciding that some behaviour is
actually a vulnerability requires judgement against the project's threat model (see
*[Security model and scope](#security-model-and-scope)* below), and the security team is staffed by
volunteers — a stream of unverified or AI-hallucinated "vulnerabilities" wastes their time and buries real
issues. AI tooling may help *analyse* a suspected problem, but a human contributor must independently verify
it and own the report. **Autonomous agents must not file security reports or open security issues on their
own**, and a tool's confident-sounding output is not, by itself, evidence of a vulnerability.

See <https://pulsar.apache.org/security/#security-policy> for more details.

## Disclosure hygiene for contributors

The **project team commits the fix**, coordinated through the ASF security vulnerability handling process
([apache.org/security/committers.html#possible](https://apache.org/security/committers.html#possible)). The
team may commit the fix to the public repository **before** the release, using a neutral commit message that
does not state its security nature; in severe cases the commit and release are made in a private repository
and the fix is made public only at release time.

As a contributor, do **not** push, commit publicly, or open a PR for a fix to a non-public security issue
yourself — **including in a public fork**, since a public-fork commit or PR is itself a disclosure. When
reporting, you may include a suggested fix patch privately in your report to `private@pulsar.apache.org` —
never in a public commit or PR.

The neutrality rules below are for **whoever commits the fix — i.e. the project team**. Until the
vulnerability has been publicly announced, the commit message and PR title/body must **not** reveal its
security nature, even when the fix touches security-adjacent code (authentication, deserialization, TLS,
networking). Describe the behaviour change neutrally; a commit or PR that advertises "fixes the CVE",
"security fix", or "patches the vulnerability" discloses the issue before it is announced and defeats
coordinated disclosure.

The same discretion applies to **everyone** — and identically to any AI tooling acting on a contributor's
behalf — in public GitHub issues, discussions, and review comments until the announcement.

**Already-public CVEs in dependencies are an exception.** The rules above concern *non-public*
vulnerabilities in this project. A PR or commit that upgrades a dependency to address an **already publicly
disclosed** CVE in that dependency does **not** follow them — the CVE is already public. Name its id directly
in the PR title and/or description (use the description when there are several CVE ids).

## Checking exposure to an already-public CVE

For a CVE that is **already public** (for example, in a dependency) and you want to check this project's
exposure or whether it is already fixed, this is **not** a private disclosure — the right venue is a GitHub
issue on apache/pulsar-spring or a question on the **dev@pulsar.apache.org** mailing list.

Before asking, search PRs and issues with the CVE id at <https://github.com/apache/pulsar-spring/pulls> (also
check issues and **closed** PRs/issues) — the fix may already be merged or the question already answered.

## Security model and scope

This project's security model is not formally defined. It is a client library that runs inside your
application, with the privileges of that application, and it relies on the
[security model of Apache Pulsar](https://github.com/apache/pulsar/security/policy). A few points matter when
deciding whether something is a vulnerability in this project:

**Report issues to the project they belong to.** Vulnerabilities in Pulsar itself, including its Java client,
belong to Apache Pulsar. Those in Spring Framework, Spring Boot or Spring Cloud Stream belong to the
[Spring project](https://spring.io/security-policy).

**Check whether a vulnerability also affects Spring for Apache Pulsar.** This project is based on Spring for
Apache Pulsar and on the Pulsar support in Spring Boot and Spring Cloud Stream, so a vulnerability found here
may exist there too, and the other way around. If the affected code also exists in those projects, report it
privately to both this project and the [Spring project](https://spring.io/security-policy).

**Pulsar Functions and connectors execute fully trusted code.** `PulsarFunctionAdministration` deploys the
functions, sinks and sources that the application defines. Running that code is their purpose, so it must be
fully trusted, and being able to run it is not a vulnerability.

**JSON message headers are only deserialized to trusted types.** `JsonPulsarHeaderMapper` trusts a default set
of packages and doesn't deserialize other types. Configuring it to trust more packages, particularly with
`*`, is the application's decision and is only appropriate for trusted message sources. A report that bypasses
this restriction is in scope.

**Samples and test resources aren't for production.** The sample applications and test utilities demonstrate
or test features, and the certificates and keys in the integration tests exist only for those tests.

When in doubt, ask through the reporting channels above rather than assuming.

## Supported versions

This project has not yet had a release under Apache Pulsar. Security fixes are made on the `main` branch. For
Spring for Apache Pulsar, which this project succeeds, see the
[Spring project's security policy](https://spring.io/security-policy).
