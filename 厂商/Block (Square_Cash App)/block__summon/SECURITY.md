# Security Policy

Summon's security model depends on a null-origin iframe, restrictive CSP,
host-owned grants, schema-validated policy dispatch, and explicit capability
contracts. Reports involving sandbox escape, grant bypass, CSP weakening,
forged `postMessage` routing, host data exposure, or credential access should
not be filed as public issues.

Use GitHub private vulnerability reporting for this repository. Include:

- A minimal reproduction.
- Browser/runtime and operating system.
- Generated protocol lines or HTML involved, if applicable.
- The selected `SurfacePlan`, granted intents, and granted capabilities.
- Whether the issue affects static, declarative, scripted, worker, or component
  island surfaces.

For non-exploitable bugs, use the public bug report template.
