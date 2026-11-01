# Security Policy

## Supported Versions

Only the latest release on the main branch is actively supported with security updates. Older versions and branches are not maintained and will not receive security fixes.

## Reporting a Vulnerability

This repository contains static reference image assets (`.png`, `.hdr`) with no executable code, so its security surface is limited. Relevant concerns include a maliciously crafted or corrupted asset that could trigger a vulnerability in image-parsing code consuming this repository (e.g. [QHWI](https://github.com/qualcomm/qhwi)).

If you believe you've found such an issue, please report it responsibly by following the guidelines below.

**To report a vulnerability, please email [opensource@qualcomm.com](mailto:opensource@qualcomm.com) with the subject line: QHWI Test Reference Images Security Vulnerability.**

Your report should include the following information:

* A clear description of the vulnerability
* Steps to reproduce the issue
* The potential impact of the vulnerability
* Any suggested fix or mitigation, if available

Once we receive your report:

* We aim to **acknowledge receipt within 5 business days**.
* We aim to **provide a resolution timeline within 10 business days** of acknowledgment.

**Please do not publicly disclose the vulnerability until a fix has been made available.** Responsible disclosure helps protect users of this project.

## Out of Scope

The following are outside the scope of this security policy:

* **Third-party dependencies**: Vulnerabilities in libraries or tools that consume these assets (e.g. image-decoding libraries) should be reported directly to those projects according to their own security policies.
* **Unsupported versions**: Issues found in versions other than the latest release on the main branch will not be addressed under this policy.
