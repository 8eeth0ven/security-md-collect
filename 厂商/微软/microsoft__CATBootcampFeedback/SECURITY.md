# Security Architecture

This document describes the security architecture of the CAT Bootcamp Feedback application, focusing on authentication, authorization, secret management, and data protection.

## Table of Contents

- [Authentication System](#authentication-system)
- [Authorization (RBAC)](#authorization-rbac)
- [Audit Logging](#audit-logging)
- [Azure Key Vault Integration](#azure-key-vault-integration)
- [API Security](#api-security)
- [Data Protection](#data-protection)
- [Deployment Security](#deployment-security)
- [Security Best Practices](#security-best-practices)

## Authentication System

### Overview

The application uses **JWT (JSON Web Tokens)** with **bcrypt password hashing** for admin authentication. This provides secure, stateless authentication for protected API endpoints.

### Authentication Flow

```
1. Admin logs in with username/password
   ↓
2. Server verifies password using bcrypt against Users table in database (with env-var fallback during migration)
   ↓
3. Server generates JWT signed with secret from Key Vault
   ↓
4. Client stores JWT and includes it in Authorization header
   ↓
5. Server validates JWT on each protected API request
```

### JWT Token Structure

```javascript
{
  "userId": 1,
  "username": "admin",
  "email": "admin@microsoft.com",
  "fullName": "CAT Admin",
  "roles": ["GlobalAdmin"],
  "isProtected": true,
  "iat": 1234567890,  // Issued at timestamp
  "exp": 1234596690,  // Expiration (8 hours)
  "iss": "cat-bootcamp-api",      // Issuer
  "aud": "cat-bootcamp-admin"     // Audience
}
```

### Token Configuration

- **Algorithm**: HS256 (HMAC with SHA-256)
- **Expiration**: 8 hours (configurable via `JWT_EXPIRY` env var)
- **Secret**: Stored in Azure Key Vault (see below)
- **Format**: `Bearer <token>` in Authorization header

### Password Security

**Bcrypt Configuration:**
- Salt rounds: 10
- Algorithm: bcrypt 2b
- Password requirements: Minimum 8 characters (enforced client-side)

**Password Hashes:**
```javascript
// Example hash (for 'CATBootcamp2026!')
$2b$10$.QNiEI80R3baYb5/KxY.Z.O4Gsvp.FC1JXjcd0ycnqK9t10LdpgGG
```

## Authorization (RBAC)

### Role Hierarchy

The application implements role-based access control (RBAC) with 6 granular roles:

| Role | Description |
|------|-------------|
| **GlobalAdmin** | Full access to everything -- sees all events, modules, feedback, and analytics |
| **UserAdmin** | Can manage users and their role assignments |
| **ModuleManager** | Can create, edit, and delete modules in the catalog |
| **EventCreator** | Can create events and manage their event-modules and speakers |
| **FeedbackManager** | Can view and delete feedback for granted events |
| **FeedbackViewer** | Read-only reporting: view feedback, analytics dashboards, and CSV exports for granted events |

### requireRole() Middleware

All protected endpoints use the `requireRole()` middleware to enforce role-based access. The middleware checks the JWT `roles` claim against the required roles for the endpoint.

### Resource-Level Security

Non-GlobalAdmin users are scoped to specific events via the **UserEventAccess** table. When a user with EventCreator, FeedbackManager, or FeedbackViewer roles queries events or feedback, results are automatically filtered to only include events they have been explicitly granted access to.

### GlobalAdmin Bypass

Users with the **GlobalAdmin** role bypass all role checks and resource-level filters. They have unrestricted access to all endpoints and all data.

### Protected Account (IsProtected Flag)

The primary GlobalAdmin account has `IsProtected = true` in the Users table. Protected accounts cannot be deactivated or have their GlobalAdmin role removed, ensuring there is always at least one admin who can manage the system.

## Audit Logging

### Overview

All authenticated actions are logged to the **AuditLog** table in the database. Anonymous feedback submissions are never logged to preserve user privacy.

### What Gets Logged

Each audit log entry captures:
- **UserId** and **Username** of the actor
- **Action** performed (e.g., LOGIN, CREATE, UPDATE, DELETE)
- **ResourceType** (e.g., User, Event, Module, Feedback)
- **ResourceId** of the affected resource
- **Summary** -- human-readable description
- **Details** -- JSON object with full change details
- **IpAddress** of the request
- **Timestamp** (UTC)

### Actions Logged

`LOGIN`, `CREATE`, `UPDATE`, `DELETE`, `ACTIVATE`, `DEACTIVATE`, `ASSIGN_ROLE`, `REMOVE_ROLE`, `GRANT_ACCESS`, `REVOKE_ACCESS`, `ADD_MODULE`, `REMOVE_MODULE`, `CHANGE_PASSWORD`, `RESET_PASSWORD`, `BULK_DELETE`

### Audit Log Viewer

GlobalAdmin users can view the audit log via `GET /api/audit-log`. The viewer supports filtering by user, action, resource type, and date range.

## Azure Key Vault Integration

### Architecture

```
┌─────────────────────────────┐
│   Azure Function App        │
│   (Managed Identity)        │
└──────────┬──────────────────┘
           │
           │ Access Policy: get, list
           │ (No credentials needed)
           ↓
┌─────────────────────────────┐
│   Azure Key Vault           │
│   - JWT-SECRET              │
│   - SQL-SERVER              │
│   - SQL-DATABASE            │
│   - SQL-USER                │
│   - SQL-PASSWORD            │
│   - ADMIN-USERS-JSON        │
│   - ACS-CONNECTION-STRING   │
│   - Encrypted at rest       │
│   - Audit logs enabled      │
└─────────────────────────────┘
```

### Key Vault Resources

| Environment | Key Vault Name | Function App | Secrets |
|------------|---------------|--------------|---------|
| Development | `cat-bootcamp-kv-dev` | `cat-bootcamp-api-win` | `JWT-SECRET`, `SQL-SERVER`, `SQL-DATABASE`, `SQL-USER`, `SQL-PASSWORD`, `ADMIN-USERS-JSON`, `ACS-CONNECTION-STRING` |
| Production | `cat-bootcamp-kv-prod` | `cat-bootcamp-api-prod` | `JWT-SECRET` (TODO: migrate remaining secrets) |

### How It Works

1. **Managed Identity**: Each Function App has a system-assigned managed identity
2. **Access Policy**: Key Vault grants the identity `get` and `list` permissions
3. **Key Vault Reference**: Function App settings use special syntax:
   ```
   JWT_SECRET=@Microsoft.KeyVault(VaultName=cat-bootcamp-kv-dev;SecretName=JWT-SECRET)
   ```
4. **Automatic Resolution**: Azure Functions runtime automatically fetches the secret value at startup
5. **Application Access**: Code reads from `process.env.JWT_SECRET` as usual
6. **Admin Users**: Users are now primarily managed in the database **Users** table. The `ADMIN_USERS_JSON` env var is still supported as a fallback during the migration period and is loaded from Key Vault

### Security Benefits

1. **No Credentials in Code**: Managed identities eliminate credential storage
2. **Encryption at Rest**: All secrets encrypted in Key Vault
3. **Least Privilege**: Function Apps only have read access to specific secrets
4. **Audit Trail**: All secret access logged to Azure Monitor
5. **Separate Secrets**: Dev and prod environments completely isolated
6. **Automatic Rotation**: Secrets can be rotated without code deployment

### Provisioning

See [`../scripts/README.md`](../scripts/README.md) for complete provisioning instructions.

**Quick Start:**
```bash
# Linux/macOS
cd scripts && ./provision-keyvault.sh

# Windows PowerShell
cd scripts && .\provision-keyvault.ps1
```

## API Security

### Public Endpoints

These endpoints are **publicly accessible** without authentication:

- `GET /api/events` - List all active events
- `GET /api/events/{code}/modules` - Get modules for event (by code)
- `POST /api/feedback` - Submit anonymous feedback
- `GET /api/health` - Health check endpoint

**Security Measures:**
- Event code validation prevents unauthorized access
- Input sanitization on all fields
- Rate limiting recommended (implement at API Gateway level)
- No PII collected or stored
- CORS configured for legitimate origins

### Protected Endpoints

These endpoints require **JWT authentication** and **role-based authorization**:

```
# User Management (GlobalAdmin, UserAdmin)
GET/POST/PUT/DELETE /api/users, /api/users/{id}
POST/DELETE /api/users/{id}/roles, /api/users/{id}/events

# Module Management (GlobalAdmin, ModuleManager)
POST/PUT/DELETE /api/modules

# Event Management (GlobalAdmin, EventCreator + resource access)
POST/PUT/DELETE /api/events

# Feedback (GlobalAdmin, FeedbackManager for delete; EventCreator, FeedbackViewer for view)
GET /api/feedback (resource-filtered)
DELETE /api/feedback/{id} (GlobalAdmin, FeedbackManager)

# Audit Log (GlobalAdmin only)
GET /api/audit-log

# Self-Service (Any authenticated user)
GET/PUT /api/users/me
PUT /api/users/me/password
```

**Security Measures:**
- JWT validation on every request
- Role-based authorization via requireRole() middleware
- Resource-level filtering via UserEventAccess table
- Token expiration enforced (8 hours)
- Issuer and audience claims validated
- HTTPS enforced in production
- CORS restricted to admin frontend origin

### CORS Configuration

**Development:**
```
Allowed Origins: https://blue-moss-01913f80f.1.azurestaticapps.net
```

**Production:**
```
Allowed Origins: https://lively-ocean-076d52c0f.2.azurestaticapps.net
```

**Methods Allowed:**
```
GET, POST, PUT, DELETE, OPTIONS
```

**Headers Allowed:**
```
Content-Type, Authorization
```

### Error Handling

Authentication errors return consistent responses:

```javascript
// 401 Unauthorized - Missing token
{
  "success": false,
  "message": "Authentication required",
  "code": "AUTH_REQUIRED"
}

// 401 Unauthorized - Invalid/expired token
{
  "success": false,
  "message": "Invalid or expired token",
  "code": "INVALID_TOKEN"
}
```

## Data Protection

### Database Security

**Azure SQL Database:**
- Encrypted connections (TLS 1.2+)
- Encryption at rest enabled
- Firewall rules restrict access
- Parameterized queries prevent SQL injection
- No PII stored in any table

**Connection Security:**
```javascript
// Encrypted connection string
server=cat-bootcamp-sql-prod.database.windows.net;
database=CATBootcampFeedback-Prod;
user id=sqladmin;
password=***;
encrypt=true;
trustServerCertificate=false;
```

### Privacy Protection

**Zero PII Collection:**
- ❌ No names, emails, or contact information
- ❌ No IP addresses stored in database
- ❌ No User-Agent strings persisted
- ❌ No device identifiers or tracking cookies
- ✅ 100% anonymous feedback

**GDPR/CCPA Compliance:**
- No personal data processing
- No data subject access requests needed (no personal data exists)
- No right to deletion needed (feedback already anonymous)
- Privacy policy available at [PRIVACY.md](../PRIVACY.md)

### Input Validation

**All user inputs validated:**
- String length limits enforced
- SQL parameterization prevents injection
- XSS protection via input sanitization
- Content-Type validation on API requests

**Example Validation:**
```javascript
// Module name
- Min length: 5 characters
- Max length: 200 characters
- Trimmed of whitespace

// Feedback comments
- Max length: 1000 characters
- HTML tags stripped
- Privacy notice displayed
```

## Deployment Security

### Secrets Management

**GitHub Secrets (for CI/CD):**
- `AZURE_FUNCTIONAPP_PUBLISH_PROFILE` - Dev Function App deployment
- `AZURE_FUNCTIONAPP_PUBLISH_PROFILE_PROD` - Prod Function App deployment
- `AZURE_STATIC_WEB_APPS_API_TOKEN` - Dev Static Web App deployment
- `AZURE_STATIC_WEB_APPS_API_TOKEN_PROD` - Prod Static Web App deployment

**Azure Function App Settings (resolved from Key Vault in dev):**
- `JWT_SECRET` - Key Vault reference → `JWT-SECRET`
- `JWT_EXPIRY` - Token expiration time (plain text, not secret)
- `SQL_SERVER` - Key Vault reference → `SQL-SERVER`
- `SQL_DATABASE` - Key Vault reference → `SQL-DATABASE`
- `SQL_USER` - Key Vault reference → `SQL-USER`
- `SQL_PASSWORD` - Key Vault reference → `SQL-PASSWORD`
- `ADMIN_USERS_JSON` - Key Vault reference → `ADMIN-USERS-JSON`
- `AZURE_COMM_CONNECTION_STRING` - Key Vault reference → `ACS-CONNECTION-STRING`

### Email Notifications

Email is sent via **Azure Communication Services (ACS)** using an Azure-managed email domain. The ACS connection string is stored in Key Vault as `ACS-CONNECTION-STRING` and referenced by the Function App at runtime. No email credentials are stored in code or plain-text configuration.

### Environment Isolation

**Development Environment:**
- Separate Azure resources
- Test data only
- Less restrictive branch protection
- Auto-deployment from main branch

**Production Environment:**
- Dedicated Azure resources
- Real user data
- Strict branch protection (1 required approval)
- Manual deployment with approval gate

### HTTPS Enforcement

**All environments enforce HTTPS:**
- Azure Static Web Apps: HTTPS by default
- Azure Functions: HTTPS only enabled
- Redirect HTTP → HTTPS automatic
- TLS 1.2+ required

## Security Best Practices

### For Developers

1. **Never commit secrets** to git repository
2. **Use parameterized queries** for all database operations
3. **Validate all inputs** on both client and server
4. **Follow principle of least privilege** for permissions
5. **Keep dependencies updated** (npm audit regularly)
6. **Test authentication** before deploying to production

### For Administrators

1. **Rotate JWT secrets** every 90 days via Key Vault
2. **Review audit logs** monthly in Azure Monitor
3. **Monitor failed login attempts** in Application Insights
4. **Keep Function Apps updated** to latest runtime version
5. **Review CORS settings** periodically
6. **Backup database** regularly (automated daily backups enabled)

### For DevOps

1. **Require pull request reviews** before merging
2. **Run security scans** in CI/CD pipeline
3. **Separate dev and prod** GitHub secrets
4. **Use managed identities** wherever possible
5. **Enable Azure Defender** for all resources
6. **Configure alerts** for suspicious activity

## Secret Rotation

### JWT Secret Rotation

**Recommended Schedule:** Every 90 days

**Rotation Process:**

1. **Generate new secret:**
   ```bash
   # Generate strong random secret (32+ characters)
   openssl rand -base64 32
   ```

2. **Update Key Vault:**
   ```bash
   # Development
   az keyvault secret set --vault-name cat-bootcamp-kv-dev \
     --name JWT-SECRET --value "NEW_SECRET_HERE"

   # Production
   az keyvault secret set --vault-name cat-bootcamp-kv-prod \
     --name JWT-SECRET --value "NEW_SECRET_HERE"
   ```

3. **Function Apps auto-restart** and pick up new secret within 5 minutes

4. **Existing tokens remain valid** until expiration (8 hours)

5. **Users re-authenticate** with new secret after old tokens expire

**No downtime required!** Azure Functions automatically fetch updated secrets.

### Database Password Rotation

**Recommended Schedule:** Every 180 days

1. Create new SQL user with same permissions
2. Update Function App settings with new credentials
3. Restart Function Apps
4. Verify connectivity
5. Remove old SQL user

## Incident Response

### Suspected JWT Secret Compromise

1. **Immediately rotate secret** in Key Vault (both dev and prod)
2. **Review audit logs** for unauthorized access
3. **Force logout all admins** (secrets change invalidates all tokens)
4. **Investigate attack vector** and patch vulnerability
5. **Document incident** for future prevention

### Database Breach

1. **Verify scope** - no PII exists, so no notification required
2. **Rotate all database credentials**
3. **Review SQL audit logs** for suspicious queries
4. **Check firewall rules** and access patterns
5. **Restore from backup** if data integrity compromised

### Unauthorized Access Attempt

1. **Check Application Insights** for failed auth attempts
2. **Review IP addresses** and patterns
3. **Enable rate limiting** if not already active
4. **Consider adding IP allowlist** for admin endpoints
5. **Update passwords** if credential stuffing suspected

## Compliance

### Standards Adherence

- ✅ **HTTPS/TLS**: All communications encrypted
- ✅ **Zero PII**: GDPR/CCPA compliant by design
- ✅ **Password Hashing**: Industry-standard bcrypt
- ✅ **Secret Management**: Azure Key Vault best practices
- ✅ **SQL Injection Prevention**: Parameterized queries
- ✅ **XSS Protection**: Input sanitization

### Audit Trail

All security-relevant events are logged to the **AuditLog table** in the database and to **Azure Application Insights**:
- Admin login attempts (success and failure)
- All CRUD operations on users, events, modules, and feedback
- Role assignments and revocations
- Event access grants and revocations
- Password changes and resets
- JWT token generation
- Protected endpoint access
- Database query execution
- Key Vault secret access (via Azure Monitor)

## Additional Resources

- [Azure Key Vault Documentation](https://docs.microsoft.com/en-us/azure/key-vault/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Azure Security Best Practices](https://docs.microsoft.com/en-us/azure/security/fundamentals/best-practices-and-patterns)
- [Managed Identities](https://docs.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/)

---

**Last Updated:** March 29, 2026
**Version:** 5.0
