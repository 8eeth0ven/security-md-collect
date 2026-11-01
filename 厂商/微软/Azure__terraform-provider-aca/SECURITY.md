# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it
responsibly through [Microsoft's Security Response Center (MSRC)](https://msrc.microsoft.com/create-report).

**Please do not report security vulnerabilities through public GitHub issues.**

## Scope

This module generates Terraform configurations for Azure Container Apps. Security
considerations include:

- **State file handling**: Terraform state files may contain sensitive data. Always
  use remote state backends with encryption enabled.
- **Provider credentials**: Never commit Azure credentials or subscription IDs to
  source control. Use environment variables or managed identity.
- **AzAPI payloads**: The AzAPI overlay sends raw JSON to Azure ARM. Review the
  generated payloads to ensure they match your security requirements.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅        |
