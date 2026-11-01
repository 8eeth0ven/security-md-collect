# Security Policy

`cb-mpc-go` is beta software. It mainly exists to demonstrate and expose the public `cb-mpc` C API through an idiomatic Go package so that MPC protocols can be used more easily from Go.

## Reporting a Vulnerability

If you believe you have found a security issue in this repository, please email `cb-mpc@coinbase.com` with:

- a description of the issue
- affected versions or commits
- reproduction steps or proof-of-concept material, if available
- whether the issue is in the Go API, CGO bridge, examples, or build/test tooling

Please do not report suspected vulnerabilities through public GitHub issues or pull requests.

## Bug Bounty Eligibility

Reports that are specific to `cb-mpc-go` are welcome, but they are not eligible for a bounty through Coinbase's HackerOne program. See `BUG_BOUNTY.md` for scope details.

## Upstream `cb-mpc` Issues

If the issue affects the underlying `cb-mpc` library rather than this Go wrapper, please follow `cb-mpc/SECURITY.md` for disclosure guidance. Any HackerOne eligibility is determined by the upstream `cb-mpc` policy and scope, including `cb-mpc/BUG_BOUNTY.md`.

## Responsible Disclosure

Please avoid public disclosure until the issue has been reviewed and, where appropriate, remediated.
