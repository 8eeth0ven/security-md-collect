# Security Policy

## Disclaimer

This project is provided as sample/educational code for pre-migration database assessment and is NOT intended for production use without additional security hardening. See the "Production Hardening Recommendations" section below.

## Reporting Vulnerabilities

If you discover a potential security issue in this project, please report it by emailing aws-security@amazon.com. Do not create a public issue.

## What This Tool Collects

This tool collects sensitive SQL Server metadata including:
- Server configuration and build information
- Login names, roles, and permissions
- Database mail configuration (email addresses, SMTP settings)
- Credential names and identity information
- Linked server configurations
- Network connection information (IP addresses, ports)
- Agent jobs, operators, and proxy configurations

**Data Classification**: The output of this tool should be treated as CONFIDENTIAL. Assessment results contain information that could enable lateral movement or privilege escalation if exposed.

## Prerequisites and Permissions

To run this assessment, you need:
- A Windows account with SQL Server access (Windows Integrated Authentication)
- The permissions defined in `DatabaseAssessment/permissions.sql` on target instances
- PowerShell 5.1+ with SqlServer module
- Network connectivity to target SQL Server instances

## Known Security Considerations

| Item | Category | Rationale |
|------|----------|-----------|
| ALTER ANY SERVER AUDIT permission | Security Debt | Required to enumerate server audit configurations; cannot read audit info without this permission |
| xp_regenumkeys / xp_regread access | Security Debt | Used for service enumeration via registry; limited to read-only access |
| db_datareader on all databases | Security Debt | Required to read system catalog views across all databases; does not access application data tables |

## Production Hardening Recommendations

Before using this tool in a production environment:

- **Credentials**: Never hardcode passwords. Use Windows Integrated Authentication or store credentials in a secure vault.
- **Output Protection**: Encrypt assessment output files at rest. Use ACLs to restrict access to DBA team only.
- **Data Retention**: Delete intermediate CSV files after database import. Establish a retention policy for assessment results.
- **Network Security**: Run assessments from a hardened jump box, not developer workstations. Avoid storing output on network shares.
- **Permissions**: Review the permission grants in `permissions.sql` and scope down to only what's needed for your environment.
- **Assessment Account**: Use a dedicated service account. Disable the account after the assessment window closes.

## Resource Cleanup

After completing the assessment:

1. Disable or drop the `db_assessment_executor` login on source servers
2. Delete intermediate CSV files in `output-*` directories
3. Remove the `AwsDatabaseAssessment` database when no longer needed
4. Revoke permissions granted by `permissions.sql`

## Dependencies

| Dependency | Version | Notes |
|------------|---------|-------|
| PowerShell | 5.1+ | Windows built-in; 7.x for cross-platform |
| SqlServer module | Latest | Microsoft-maintained; used for Invoke-Sqlcmd |
| ImportExcel module | Latest | Used for Excel report generation |
