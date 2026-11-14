# Security

## Reporting vulnerabilities

Do not post credentials or exploit details in a public issue. Report security vulnerabilities privately to [Vercel Security](https://vercel.com/security).

## Boundaries

- just-secrets stores credentials in the current user's native OS store. It is not a sandbox, secret broker, or defense against code running as that user.
- On macOS, the trusted Keychain client is `/usr/bin/security`, not the JavaScript package or the calling application.
- Linux requires a working Secret Service session. Windows requires a credential-capable logon session and permission to run the bundled PowerShell bridge.
- Secrets travel through stdin/stdout pipes. They never enter subprocess arguments, generated script source, or library logs. Identifiers are not secrets and can appear in process arguments and native-store metadata.
- There is no automatic plaintext, encrypted-file, memory-cache, or alternate-executable fallback.
- The library bounds subprocess execution and output. It does not return captured stderr, stdout, or native exceptions in operational errors.
- JavaScript and managed-runtime strings cannot be reliably erased. Debugging tools, crash dumps, OS audit tooling, or same-user malware may observe values while in use. Buffer cleanup does not guarantee complete zeroization.
- The application remains responsible for avoiding secret disclosure after retrieval, choosing appropriate service/name scopes, controlling subprocess inheritance, and securing its dependencies and runtime.
- Operations can fail after a mutation commits. Linux's search/unlock/read/delete sequence is not atomic, and timeouts do not imply rollback.

## Review and tests

Changes to subprocess invocation, encoding, error handling, or native bridges require regression tests. Run the native integration suite on every supported OS before release; mocked tests cannot validate OS access-control behavior. The package has no npm dependencies or install-time downloads.
