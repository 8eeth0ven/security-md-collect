# Security Policies and Procedures

This document outlines security procedures and general policies for the
SOC Cockpit project.

- [Disclosing a security issue](#disclosing-a-security-issue)
- [Vulnerability management](#vulnerability-management)
- [Suggesting changes](#suggesting-changes)
- [Known advisories](#known-advisories)

## Disclosing a security issue

The SOC Cockpit maintainers take all security issues in the project seriously.
Thank you for improving the security of SOC Cockpit. We appreciate your
dedication to responsible disclosure and will make every effort to acknowledge
your contributions.

SOC Cockpit leverages GitHub's private vulnerability reporting.

To learn more about this feature and how to submit a vulnerability report,
review [GitHub's documentation on private reporting](https://docs.github.com/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability).

Here are some helpful details to include in your report:

- a detailed description of the issue
- the steps required to reproduce the issue
- versions of the project that may be affected by the issue
- if known, any mitigations for the issue

A maintainer will acknowledge the report within three (3) business days, and
will send a more detailed response within an additional three (3) business days
indicating the next steps in handling your report.

If you've been unable to successfully draft a vulnerability report via GitHub
or have not received a response during the alloted response window, please
reach out via the [Cisco Open security contact email](mailto:oss-security@cisco.com).

After the initial reply to your report, the maintainers will endeavor to keep
you informed of the progress towards a fix and full announcement, and may ask
for additional information or guidance.

## Vulnerability management

When the maintainers receive a disclosure report, they will assign it to a
primary handler.

This person will coordinate the fix and release process, which involves the
following steps:

- confirming the issue
- determining affected versions of the project
- auditing code to find any potential similar problems
- preparing fixes for all releases under maintenance

## Suggesting changes

If you have suggestions on how this process could be improved please submit an
issue or pull request.

## Known advisories

The following advisory is reported by `npm audit` and has been assessed as not
exploitable in this project. It is tracked here rather than suppressed.

### GHSA-w5hq-g745-h8pq — `uuid` missing buffer bounds check

- **Severity:** Moderate
- **Path:** `exceljs` -> `uuid@8.3.2`
- **Status:** Accepted, not reachable.

The advisory affects the v3, v5 and v6 generators when a caller supplies a `buf`
argument. `exceljs` imports only the v4 generator and calls it with no arguments
(`lib/xlsx/xform/sheet/cf-rule-ext-xform.js`), so the vulnerable code path is
never entered.

No upstream fix is available: `exceljs@4.4.0` is the current release and it
requires `uuid@^8.3.0`. Forcing a patched major of `uuid` through an `overrides`
entry would place an incompatible API inside that range, and `npm audit fix
--force` resolves this advisory only by downgrading `exceljs` to 3.4.0, a
breaking change to spreadsheet import and export.

This will be revisited when `exceljs` ships a release that depends on
`uuid@>=11.1.1`.
