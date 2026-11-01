# Security Policy

## Supported Versions

We actively support the following versions of the SBOM Graviton App Dependency Compatibility Tool:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability in this project, please report it responsibly.

### How to Report

1. **Do NOT create a public GitHub issue** for security vulnerabilities
2. **Email us directly** at [security@example.com](mailto:security@example.com)
3. **Include the following information**:
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact assessment
   - Any suggested fixes or mitigations

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your report within 48 hours
- **Initial Assessment**: We will provide an initial assessment within 5 business days
- **Regular Updates**: We will keep you informed of our progress
- **Resolution Timeline**: We aim to resolve critical vulnerabilities within 30 days
- **Credit**: We will credit you in our security advisories (unless you prefer to remain anonymous)

## Security Best Practices

### For Users

When deploying and using this tool, follow these security best practices:

#### AWS Account Security
- Use dedicated AWS accounts for different environments (dev, staging, prod)
- Enable AWS CloudTrail in all regions
- Configure AWS Config for compliance monitoring
- Use AWS Organizations for centralized account management
- Enable MFA for all IAM users

#### Infrastructure Security
- Deploy infrastructure using the provided Terraform templates
- Use customer-managed KMS keys for encryption
- Enable VPC endpoints for private connectivity when possible
- Regularly rotate access keys and credentials
- Monitor CloudWatch logs for suspicious activity

#### Access Control
- Follow the principle of least privilege for IAM roles
- Use IAM roles instead of long-term access keys
- Regularly audit IAM permissions
- Enable AWS CloudTrail for API logging
- Use AWS IAM Access Analyzer to identify unused permissions

#### Data Protection
- Encrypt all data at rest using KMS
- Encrypt data in transit using TLS 1.2+
- Classify SBOM data according to your organization's data governance policies
- Implement appropriate data retention policies
- Regularly backup critical configuration and data

### For Contributors

#### Code Security
- Never commit secrets, API keys, or credentials to the repository
- Use environment variables or AWS Parameter Store for configuration
- Follow secure coding practices for Python and Terraform
- Regularly update dependencies to patch security vulnerabilities
- Use static analysis tools to identify potential security issues

#### Development Environment
- Use separate AWS accounts for development and testing
- Implement proper branch protection rules
- Require code reviews for all changes
- Use signed commits when possible
- Keep development tools and dependencies up to date

## Security Features

### Built-in Security Controls

#### Encryption
- **At Rest**: All S3 objects encrypted with customer-managed KMS keys
- **In Transit**: TLS 1.2+ for all API communications
- **Lambda Environment**: Environment variables encrypted with KMS
- **CloudWatch Logs**: Log groups encrypted with dedicated KMS keys

#### Access Control
- **IAM Roles**: Service-specific roles with least privilege permissions
- **Resource Policies**: S3 bucket policies restrict access to authorized services
- **KMS Key Policies**: Granular permissions for encryption key usage
- **VPC Endpoints**: Optional private connectivity for enhanced network security

#### Monitoring and Auditing
- **CloudTrail**: Comprehensive API call logging
- **CloudWatch**: Real-time monitoring and alerting
- **S3 Access Logging**: Detailed access logs for all S3 operations
- **Dead Letter Queues**: Error handling and investigation capabilities

#### Network Security
- **Private Subnets**: CodeBuild runs in private subnets when VPC is configured
- **Security Groups**: Restrictive security group rules
- **NACLs**: Network-level access controls
- **VPC Flow Logs**: Network traffic monitoring

### Security Scanning

#### Automated Security Checks
- **Checkov**: Infrastructure as code security scanning in CI/CD
- **Dependency Scanning**: Regular checks for vulnerable dependencies
- **Container Scanning**: Security scanning of CodeBuild container images
- **SAST**: Static application security testing for Python code

## Compliance Considerations

### Data Governance
- **Data Classification**: SBOM files should be classified according to your organization's policies
- **Data Residency**: Consider data residency requirements for cross-border deployments
- **Retention Policies**: Implement appropriate data retention and deletion policies
- **Access Logging**: Maintain comprehensive access logs for compliance auditing

### Regulatory Compliance
- **SOC 2**: AWS services used are SOC 2 compliant
- **ISO 27001**: Infrastructure follows ISO 27001 security standards
- **GDPR**: Consider GDPR implications if processing EU personal data
- **HIPAA**: Additional controls may be needed for HIPAA compliance

## Incident Response

### Security Incident Handling
1. **Detection**: Monitor CloudWatch alarms and security events
2. **Assessment**: Evaluate the scope and impact of the incident
3. **Containment**: Isolate affected resources and prevent further damage
4. **Investigation**: Analyze logs and forensic evidence
5. **Recovery**: Restore normal operations and implement fixes
6. **Lessons Learned**: Document findings and improve security controls

### Emergency Contacts
- **Security Team**: [security@example.com](mailto:security@example.com)
- **AWS Support**: Use your AWS Support plan for infrastructure issues
- **Incident Response**: [incident-response@example.com](mailto:incident-response@example.com)

## Security Updates

We regularly update this project to address security vulnerabilities:

- **Critical Vulnerabilities**: Patches released within 48 hours
- **High Severity**: Patches released within 1 week
- **Medium/Low Severity**: Patches included in regular releases
- **Dependency Updates**: Monthly security updates for dependencies

Subscribe to our security advisories to stay informed about security updates.

## Additional Resources

- [AWS Security Best Practices](https://aws.amazon.com/architecture/security-identity-compliance/)
- [Terraform Security Best Practices](https://learn.hashicorp.com/tutorials/terraform/security)
- [Python Security Guidelines](https://python-security.readthedocs.io/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

For questions about security practices or to report security issues, contact us at [security@example.com](mailto:security@example.com).