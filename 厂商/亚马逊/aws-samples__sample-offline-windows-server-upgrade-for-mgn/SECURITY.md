# Security

## Reporting a vulnerability

If you discover a potential security issue in this project, notify AWS/Amazon Security through the
[vulnerability reporting page](https://aws.amazon.com/security/vulnerability-reporting/).
Please do **not** create a public GitHub issue.

## Security considerations for this sample

This is sample code, for non-production usage. Work with your security and legal teams to meet your
organizational requirements before deployment.

- **Least privilege.** The Automation role policy in `iam/` grants only the actions that the runbooks call.
  EC2 actions that act on resources created at run time (the pre-upgrade AMI, the temporary upgrade
  instance, the media volume) use `Resource: "*"` with an `aws:RequestedRegion` condition, because their
  IDs aren't known in advance. Review and tighten these statements for your environment.
- **Pre-signed URLs.** When you stage artifacts in Amazon S3, the runbook creates pre-signed URLs that are
  valid for one hour and scoped to a single object. The URLs aren't written to the command output.
- **Integrity of staged files.** Provide SHA-256 hashes for staged driver packages. The runbook rejects a
  package whose hash doesn't match.
- **Artifact bucket.** Turn on Block Public Access and default encryption, and grant `s3:GetObject` to the
  Automation role only.
- **No internet access.** The runbooks are designed for subnets without an internet gateway or NAT gateway.
  AWS service traffic uses VPC endpoints.
