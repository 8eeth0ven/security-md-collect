# Hibernate Security Policy

This document explains how to report security issues for **Hibernate** projects.

## Reporting a Vulnerability

Please report suspected security issues privately.

- Submit vulnerability reports via https://hackerone.com/ibm. Find more details (PGP key, other ways of reaching out) in [IBM's Security Vulnerability Management page](https://www.ibm.com/trust/security-vulnerability-management).
- Do **not** open a public JIRA/GitHub issue for suspected vulnerabilities.

When reporting, please include:

- A description of the issue and affected project/versions
- Steps to reproduce (ideally a minimal proof-of-concept)
- Assessment of potential impact
- Your contact information
- Any specific requests, such as anonymity for you and/or the organization you represent

## Maintainer Commitments

We aim to handle reports quickly and responsibly.

- Our goal is to acknowledge reports as soon as possible.
- We will provide an initial assessment as capacity allows.
- Progress updates will be shared until resolution.
- Disclosure will be coordinated with the reporter, and credit given unless anonymity is requested.

## Disclosure and Embargoes

By default, **Hibernate** does **not** accept long embargoes.
Security reports will usually become public once a fix is available and confirmed.
A short embargo may be considered in exceptional cases (e.g., downstream user protection), but is not guaranteed.

## Expectations for Reporters

Reporters should understand that:

- This project's security reports are handled by volunteers and IBM.
- Reports with clear steps, proof-of-concept, or test cases help us respond faster.
- Respecting maintainer capacity and workload benefits the community overall.

## Scope and Versions

This policy applies to the **Hibernate** codebase and related artifacts.
We currently support security fixes for the **latest stable release** of each project, and select older versions supported by contributing software vendors.

To find out which versions match these criteria, go to the corresponding project page on [the Hibernate website](https://hibernate.org/). For example:

* [Hibernate ORM](https://hibernate.org/orm/releases/)
* [Hibernate Search](https://hibernate.org/search/releases/)
* [Hibernate Validator](https://hibernate.org/validator/releases/)
* [Hibernate Reactive](https://hibernate.org/reactive/releases/)

Older versions may not receive patches; in such cases we may advise upgrading.

## Transparency

We may document known security issues or our response status when appropriate.
This helps users understand our process and sets realistic expectations.

