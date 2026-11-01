# Security Policy

Thank you for helping keep the Splunk Cisco App Navigator (SCAN) secure!

## Reporting Security Vulnerabilities

**Please do not open a public GitHub issue for security vulnerabilities.**

If you believe you have found a security vulnerability in this repository, please report it privately to Splunk:

- **Splunk Security Research:** [security@splunk.com](mailto:security@splunk.com)
- **HackerOne Program:** [https://hackerone.com/splunk](https://hackerone.com/splunk)

Include the following information in your report:

- A description of the vulnerability
- Steps to reproduce (if applicable)
- Potential impact and severity assessment
- Your contact information for follow-up
- Any proof-of-concept code or screenshots

## Response Timeline

- **Initial Response:** Within 5 business days
- **Status Updates:** As the issue is being investigated
- **Resolution:** Coordinated patch release (typically within 30 days for critical issues)
- **Public Disclosure:** Coordinated timing, typically after patch is available

## Supported Versions

| Version | Supported          | Notes |
|---------|-------------------|-------|
| 1.0.x   | ✅ Yes           | Active development |

## Security Best Practices

When using this app:

1. **Keep Dependencies Updated:** Regularly update Node.js, npm/yarn, and Splunk
2. **Use HTTPS:** Always use HTTPS for Splunk connections
3. **Least Privilege:** Grant minimal necessary permissions to app users
4. **Configuration Protection:** Secure `local/` directory access in production
5. **Secret Management:** Never hardcode credentials; use Splunk secret management

## Security Scanning

This repository uses:

- **GitHub CodeQL:** Automated code scanning for common vulnerabilities
- **Dependabot:** Continuous dependency vulnerability monitoring
- **npm Audit:** Local package vulnerability checks

Run security checks locally:

```bash
# Check dependencies for vulnerabilities
yarn audit

# Run linting and code quality checks
yarn run lint

# Run CodeQL locally (requires CodeQL CLI)
codeql database create /tmp/codeql-db --language=javascript --source-root=.
codeql database analyze /tmp/codeql-db codeql/javascript-bundle --format=sarif-latest --output=codeql-results.sarif
```

## Security-Related Improvements

If you have suggestions for improving this security policy or the app's security posture, please:

1. Open a GitHub discussion (not an issue)
2. Tag it with `security` and `enhancement`
3. Describe the improvement and its rationale

## License

This security policy is part of the Splunk Cisco App Navigator and is provided under the same license as the main project.
