# Security Release Process
Slingshot is a growing community devoted in creating a High-Performance Networking Software Stack for HPC use cases. The community has adopted this security disclosure and response policy to ensure we responsibly handle critical issues.

## Supported Versions
The Slingshot project maintains release branches for the three most recent minor releases. Applicable fixes, including security fixes, may be backported to those three release branches, depending on severity and feasibility. Please refer to [RELEASES.md](https://github.com/HewlettPackard/project/blob/main/RELEASES.md) for details.
<!-- TODO fix url -->

## Reporting a Vulnerability - Private Disclosure Process
Security is of the highest importance and all security vulnerabilities or suspected security vulnerabilities should be reported to Slingshot privately, to minimize attacks against current users of Slingshot before they are fixed. Vulnerabilities will be investigated and patched on the next patch (or minor) release as soon as possible. This information from the initial report should be kept entirely internal to the project.

If you know of a publicly disclosed security vulnerability for Slingshot, please **IMMEDIATELY** contact [slingshot-security-issues@hpe.com] to inform the Slingshot Security Team.

**IMPORTANT: Do not file public issues on GitHub for security vulnerabilities**

To report a vulnerability or a security-related issue, please email the private address [slingshot-security-issues@hpe.com] with the details of the vulnerability. The email will be fielded by the Slingshot Security Team, which is made up of Slingshot maintainers who have committer and release permissions. Emails will be addressed within 3 business days, including a detailed plan to investigate the issue and any potential workarounds to perform in the meantime. Do not report non-security-impacting bugs through this channel. Use [GitHub issues](https://github.com/org/project/issues/new/choose) instead.
<!-- TODO fix url -->

### Proposed Email Content
Provide a descriptive subject line and in the body of the email include the following information:
* Basic identity information, such as your name and your affiliation or company.
* Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
* Full paths of source file(s) related to the manifestation of the issue
* The location of the affected source code (tag/branch/commit or direct URL)
* Any special configuration required to reproduce the issue
* Detailed steps to reproduce the vulnerability  (POC scripts, screenshots, and compressed packet captures are all helpful to us).
* Proof-of-concept or exploit code (if possible)
* Impact of the issue, including how an attacker might exploit the issue
  * Description of the effects of the vulnerability on Slingshot and the related hardware and software configurations, so that the Slingshot Security Team can reproduce it.

* How the vulnerability affects Slingshot usage and an estimation of the attack surface, if there is one.
* List other projects or dependencies that were used in conjunction with Slingshot to produce the vulnerability.

This information will help us triage your report more quickly.

**Please provide as much information as possible from above, but notify [slingshot-security-issues@hpe.com] as soon as possible even if some of the information cannot be immediately provided.**

## When to report a vulnerability
* When you think Slingshot has a potential security vulnerability.
* When you suspect a potential vulnerability, but you are unsure that it impacts Slingshot.
* When you know of or suspect a potential vulnerability on another project that is used by Slingshot. For example Slingshot has a dependency on [insert dependency list here], etc.

## Patch, Release, and Disclosure
The Slingshot Security Team will respond to vulnerability reports as follows:

1.  The Security Team will investigate the vulnerability and determine its effects and criticality.
2.  If the issue is not deemed to be a vulnerability, the Security Team will follow up with a detailed reason for rejection.
3.  The Security Team will initiate a conversation with the reporter within 3 business days.
4.  If a vulnerability is acknowledged and the timeline for a fix is determined, the Security Team will work on a plan to communicate with the appropriate community, including identifying mitigating steps that affected users can take to protect themselves until the fix is rolled out.
5.  The Security Team will also create a [CVSS](https://www.first.org/cvss/specification-document) using the [CVSS Calculator](https://www.first.org/cvss/calculator/3.0). The Security Team makes the final call on the calculated CVSS; it is better to move quickly than making the CVSS perfect. Issues may also be reported to [Mitre](https://cve.mitre.org/) using this [scoring calculator](https://nvd.nist.gov/vuln-metrics/cvss/v3-calculator). The CVE will initially be set to private.
6.  The Security Team will work on fixing the vulnerability and perform internal testing before preparing to roll out the fix.
7.  The Security Team will provide early disclosure of the vulnerability by emailing the [slingshot-vulnerability-disclosures@hpe.com] mailing list. Distributors can initially plan for the vulnerability patch ahead of the fix, and later can test the fix and provide feedback to the Slingshot team. See the section **Early Disclosure to Slingshot Distributors List** for details about how to join this mailing list.
8. A public disclosure date is negotiated by the Slingshot Security Team, the bug submitter, and the distributors list. We prefer to fully disclose the bug as soon as possible once a user mitigation or patch is available. It is reasonable to delay disclosure when the bug or the fix is not yet fully understood, the solution is not well-tested, or for distributor coordination. The timeframe for disclosure is from immediate (especially if it’s already publicly known) to a few weeks. For a critical vulnerability with a straightforward mitigation, we expect report date to public disclosure date to be on the order of 14 business days. The Slingshot Security Team holds the final say when setting a public disclosure date.
9.  Once the fix is confirmed, the Security Team will patch the vulnerability in the next patch or minor release, and backport a patch release into all earlier supported releases. Upon release of the patched version of Slingshot, we will follow the **Public Disclosure Process**.

### Public Disclosure Process
The Security Team publishes a public [advisory](https://github.com/HewlettPackard/project/security/advisories) to the Slingshot community via GitHub. In most cases, additional communication via Slack, security mailing lists, and other channels will assist in educating Slingshot users and rolling out the patched release to affected users.

The Security Team will also publish any mitigating steps users can take until the fix can be applied to their Slingshot instances. Slingshot distributors will handle creating and publishing their own security advisories.

## Mailing lists
- Use [slingshot-security-issues@hpe.com] to report security concerns to the Slingshot Security Team, who uses the list to privately discuss security issues and fixes prior to disclosure.
- Join [slingshot-vulnerability-disclosures@hpe.com] for early private information and vulnerability disclosure. Early disclosure may include mitigating steps and additional information on security patch releases. See below for information on how Slingshot distributors or vendors can apply to join this list.

## Early Disclosure to Slingshot Distributors List
This private list is intended to be used primarily to provide actionable information to multiple distributor projects at once. This list is not intended to inform individuals about security issues.

### Membership Criteria
To be eligible to join the [slingshot-vulnerability-disclosure@hpe.com] mailing list, you should:
1. Be an active distributor of Slingshot.
2. Have a publicly verifiable track record up to the present day of fixing security issues.
3. Not be a downstream or rebuild of another distributor.
4. Be a participant and active contributor in the Slingshot community.
5. Accept the Embargo Policy that is outlined below.
6. Has someone who is already on the list vouch for the person requesting membership on behalf of your distribution.

**The terms and conditions of the Embargo Policy apply to all members of this mailing list. A request for membership represents your acceptance to the terms and conditions of the Embargo Policy**

### Embargo Policy
The information that members receive on [slingshot-vulnerability-disclosures@hpe.com] must not be made public, shared, or even hinted at anywhere beyond those who need to know within your specific team, unless you receive explicit approval to do so from the Slingshot Security Team. This remains true until the public disclosure date/time agreed upon by the list. Members of the list and others cannot use the information for any reason other than to get the issue fixed for your respective distribution's users.
Before you share any information from the list with members of your team who are required to fix the issue, these team members must agree to the same terms, and only be provided with information on a need-to-know basis.

In the unfortunate event that you share information beyond what is permitted by this policy, you must urgently inform the slingshot-security-issues@hpe.com mailing list of exactly what information was leaked and to whom. If you continue to leak information and break the policy outlined here, you will be permanently removed from the list.

### Requesting to Join
Send new membership requests to [slingshot-security-issues@hpe.com].
In the body of your request please specify how you qualify for membership and fulfill each criterion listed in the Membership Criteria section above.

## Confidentiality, integrity and availability
We consider vulnerabilities leading to the compromise of data confidentiality, elevation of privilege, or integrity to be our highest priority concerns. Availability, in particular in areas relating to DoS and resource exhaustion, is also a serious security concern. The Slingshot Security Team takes all vulnerabilities, potential vulnerabilities, and suspected vulnerabilities seriously and will investigate them in an urgent and expeditious manner. Due to the sensitive and/or confidential nature of the issue, discussions concerning work related to security vulnerabilities must NOT be occur on public or insecure channels of any kind. A security team member will establish secure channels with involved parties.

Note that we do not currently consider the default settings for Slingshot to be secure-by-default. It is necessary for operators to explicitly configure settings, role based access control, and other resource related features in Slingshot to provide a hardened Slingshot environment. We will not act on any security disclosure that relates to a lack of safe defaults. Over time, we will work towards improved safe-by-default configuration, taking into account backwards compatibility.

## Preferred Languages

We prefer all communications to be in English.

## Policy

Under the principle of Coordinated Vulnerability Disclosure, researchers disclose newly discovered vulnerabilities in hardware, software, and services directly to the vendors of the affected product; to a national CERT or other coordinator who will report to the vendor privately; or to a private service that will likewise report to the vendor privately. The researcher allows the vendor the opportunity to diagnose and offer fully tested updates, workarounds, or other corrective measures before any party discloses detailed vulnerability or exploit information to the public. The vendor continues to coordinate with the researcher throughout the vulnerability investigation and provides the researcher with updates on case progress. Upon release of an update, the vendor may recognize the finder for the research and privately reporting the issue. If attacks are underway in the wild, and the vendor is still working on the update, then both the researcher and vendor work together as closely as possible to provide early public vulnerability disclosure to protect customers. The aim is to provide timely and consistent guidance to customers to help them protect themselve*s.*

For more information on CVD, please review the information provided in the following links:

- [ISO/IEC 29147:2018 on Vulnerability Disclosure](https://www.iso.org/standard/72311.html)
- [The CERT Guide to Coordinated Vulnerability Disclosure](https://resources.sei.cmu.edu/asset_files/SpecialReport/2017_003_001_503340.pdf)

<!-- Definitions -->

[security-reporting-list]: slingshot-security-issues@hpe.com
[security-disclosures-list]: slingshot-vulnerability-disclosures@hpe.com


