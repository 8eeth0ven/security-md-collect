# Security Policy — NiFi Rock (OCI Image)

## Reporting a Vulnerability

The easiest way to report a security issue is through a [GitHub Private Security Report](https://github.com/canonical/nifi-rocks/security/advisories/new) with a description of the issue, the steps you took to create the issue, affected versions, and, if known, mitigations for the issue.

Alternatively, to report a security issue via email, please email [security@ubuntu.com](mailto:security@ubuntu.com) with a description of the issue, the steps you took to create the issue, affected versions, and, if known, mitigations for the issue.

The [Ubuntu Security disclosure and embargo policy](https://ubuntu.com/security/disclosure-policy) contains more information about what you can expect when you contact us and what we expect from you.

## Supported Versions

The NiFi rock follows the Apache NiFi release cadence, built on Ubuntu 26.04 LTS. The product currently ships interim releases; no LTS commitment is made at this time.

| Rock Version | Apache NiFi | Ubuntu Base                          | Status          | End of Standard Support |
| ------------ | ----------- | ------------------------------------ | --------------- | ----------------------- |
| 2.10.x       | 2.10.x      | Ubuntu 26.04 LTS (Resolute Raccoon)  | **Pre-release** | TBD                     |

## Product Lifetime and Support Phases

| Phase                    | Description                                                       |
| ------------------------ | ----------------------------------------------------------------- |
| **Standard Support**     | Active bug fixes, security patches, and new image builds.         |
| **Security Maintenance** | Security patches only; no new features or non-critical bug fixes. |
| **End of Life (EOL)**    | No further updates. Users must upgrade to a supported version.    |

Support periods are defined in the Workflows team support policy. The current `2.10` series is in **Pre-release** and will transition to Standard Support upon first stable release, followed by Security Maintenance prior to its End of Standard Support date.
