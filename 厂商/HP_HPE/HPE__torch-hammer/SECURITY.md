# Security Release Process

Torch Hammer is a growing community devoted to creating portable PyTorch micro-benchmarks for stress testing and evaluating CPUs, GPUs, and APUs. The community has adopted this security disclosure and response policy to ensure we responsibly handle critical issues.

## Supported Versions

The Torch Hammer project maintains the latest release on the `main` branch. Security fixes will be applied to the current release.

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |

## Reporting a Vulnerability - Private Disclosure Process

Security is of the highest importance and all security vulnerabilities or suspected security vulnerabilities should be reported to Torch Hammer privately, to minimize attacks against current users before they are fixed. Vulnerabilities will be investigated and patched on the next release as soon as possible.

**IMPORTANT: Do not file public issues on GitHub for security vulnerabilities.**

### How to Report

Use **GitHub Security Advisories** to report vulnerabilities privately:

1. Navigate to the [Security tab](../../security) of this repository
2. Click "Report a vulnerability" 
3. Fill out the advisory form with the details below

This allows for private discussion and coordinated disclosure without requiring email.

### Information to Include

Please provide as much of the following information as possible:

* Basic identity information, such as your name and your affiliation or company
* Type of issue (e.g., code injection, arbitrary file access, resource exhaustion, etc.)
* Full paths of source file(s) related to the manifestation of the issue
* The location of the affected source code (tag/branch/commit or direct URL)
* Any special configuration required to reproduce the issue
* Detailed steps to reproduce the vulnerability (scripts, screenshots, and logs are helpful)
* Proof-of-concept or exploit code (if possible)
* Impact of the issue, including how an attacker might exploit it
* List other projects or dependencies that were used in conjunction with Torch Hammer to produce the vulnerability

This information will help us triage your report more quickly. **Please report as soon as possible even if some information cannot be immediately provided.**

## When to Report a Vulnerability

* When you think Torch Hammer has a potential security vulnerability
* When you suspect a potential vulnerability but are unsure that it impacts Torch Hammer
* When you know of or suspect a potential vulnerability in a dependency used by Torch Hammer (e.g., PyTorch, pynvml, amdsmi)

## Patch, Release, and Disclosure

The Torch Hammer maintainers will respond to vulnerability reports as follows:

1. Investigate the vulnerability and determine its effects and criticality
2. If the issue is not deemed to be a vulnerability, follow up with a detailed reason for rejection
3. Initiate a conversation with the reporter within 3 business days
4. If a vulnerability is acknowledged, work on a plan to communicate with the community, including identifying mitigating steps that affected users can take
5. Create a [CVSS](https://www.first.org/cvss/specification-document) score using the [CVSS Calculator](https://www.first.org/cvss/calculator/3.0) if applicable
6. Work on fixing the vulnerability and perform internal testing before rolling out the fix
7. A public disclosure date is negotiated with the bug submitter. We prefer to fully disclose the bug as soon as possible once a mitigation or patch is available

### Public Disclosure Process

Upon release of the patched version, we will publish a public [advisory](../../security/advisories) to the Torch Hammer community via GitHub. The advisory will include any mitigating steps users can take until the fix can be applied.

## Scope

This security policy applies to the Torch Hammer benchmark suite. Note that this is a benchmarking tool, not a production service, so the attack surface is primarily:

* Code execution vulnerabilities in the benchmark scripts
* Dependency vulnerabilities in required packages (PyTorch, pynvml, amdsmi)
* Potential resource exhaustion issues

## Confidentiality, Integrity, and Availability

We consider vulnerabilities leading to the compromise of data confidentiality, elevation of privilege, or integrity to be our highest priority concerns. Availability, particularly relating to DoS and resource exhaustion, is also a serious security concern.

## Preferred Languages

We prefer all communications to be in English.

## Policy

Under the principle of Coordinated Vulnerability Disclosure, researchers disclose newly discovered vulnerabilities directly to the maintainers privately. The researcher allows the maintainers the opportunity to diagnose and offer fully tested updates, workarounds, or other corrective measures before any party discloses detailed vulnerability or exploit information to the public.

For more information on CVD, please review:

* [ISO/IEC 29147:2018 on Vulnerability Disclosure](https://www.iso.org/standard/72311.html)
* [The CERT Guide to Coordinated Vulnerability Disclosure](https://resources.sei.cmu.edu/asset_files/SpecialReport/2017_003_001_503340.pdf)

## Contact for Abuse/Complaints

For general abuse reports or complaints about the project, contact [github@hpe.com](mailto:github@hpe.com).
