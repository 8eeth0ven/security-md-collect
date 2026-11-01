# Security

Only the current 3.x release line receives fixes. The 1.x and 2.x tags are
historical releases and are no longer maintained.

Report vulnerabilities privately through GitHub private vulnerability reporting,
when available. Otherwise, contact the public project address
`omics@tencent.com` to arrange a private report. Do not post credentials, private
input data, signed URLs, or unredacted logs in public issues or pull requests.

Use short-lived, narrowly scoped credentials where possible. Keep COS
`sessionToken` separate from the Omics executor's `accessToken`. Configuration
examples read secrets from the environment; no real values belong in this
repository, pipeline parameters, or release assets.

Credential parser errors and HTTP diagnostics intentionally omit source text,
URLs, headers, and bodies. Metadata export is optional and contains workflow
parameters and execution traces, which may include scripts, environment values,
paths, or sensitive application data. Treat generated metadata and normal
Nextflow execution artifacts as private run data and review them before sharing.

This object-storage adapter does not provide POSIX transactions, atomic rename,
or atomic exclusive creation across processes. See the filesystem audit for
documented consistency and failure boundaries.
