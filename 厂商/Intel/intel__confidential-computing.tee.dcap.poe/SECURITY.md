# Security Policy
Intel is committed to rapidly addressing security vulnerabilities affecting our customers and providing clear guidance on the solution, impact, severity and mitigation.

## Reporting a Vulnerability
Please report any security vulnerabilities in this project utilizing the guidelines [here](https://www.intel.com/content/www/us/en/security-center/vulnerability-handling-guidelines.html).

## Platform Ownership Endorsement Tools

This repository contains tools for extracting and handling identifiers used in
the [Platform Ownership Endorsement](https://www.intel.com/content/www/us/en/developer/articles/technical/software-security-guidance/technical-documentation/platform-ownership-endorsements.html)
flow for Intel&reg; SGX and Intel&reg; TDX platforms. The following sub-section
describes the user-facing security considerations of using these tools.

### Sensitive Assets — User Responsibility

The tools in this repository extract the following platform identifiers from
platform manifests, PCK certificates, and SGX quotes:

- **Platform Instance ID (PIID)** — uniquely identifies a specific registered
  SGX platform instance (changes on each SGX Factory Reset).
- **Processor Registration ID (PRID)** — identifies a registered processor
  package and is used as part of the platform registration and endorsement flow
  (remains constant for the entire lifespan of a CPU).

> [!IMPORTANT]
> These tools are intended to be deployed and used only in a trusted environment.
> Secure handling of these identifiers is the user’s responsibility.

While these identifiers are not cryptographic secrets, they represent stable
platform identity metadata used during platform attestation.

Unintended disclosure may enable:

- **Unauthorized correlation** of attestation events across time or services,
  by allowing multiple quotes or endorsements to be linked to the same physical
  platform.
- **Fraudulent platform ownership claims**, where an attacker attempts to
  misrepresent or preemptively claim endorsement of a platform instance they
  do not control.

Such impersonation attempts are mitigated by relying parties only trusting
platform ownership endorsements signed by selected, trusted entities
(e.g., trusted CSPs).
Additionally, possession of PIID or PRID values alone is insufficient
 to forge attestation evidence without access to genuine platform hardware.

> [!NOTE]
> Platform registration state, including the associated PIID, can be
> cleared by performing an **SGX Factory Reset** via the system BIOS. This forces
> a new platform establishment and re‑registration on subsequent provisioning.
> An SGX Factory Reset changes the PIID, but it does not change the PRID.
