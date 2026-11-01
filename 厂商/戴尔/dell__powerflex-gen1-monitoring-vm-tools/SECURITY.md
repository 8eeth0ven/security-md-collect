# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in this project, please report it responsibly by emailing **PowerFlex.Monitoring@Dell.com**. Do not open a public GitHub issue for security vulnerabilities.

Please include:
- A description of the vulnerability
- Steps to reproduce it
- Any potential impact

We will acknowledge receipt within 72 hours and work to address confirmed vulnerabilities promptly.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | Yes       |

## Script Security

The scripts in this repository are designed to run as **root** on a dedicated monitoring VM. They perform the following privileged operations:

- **Network configuration:** Sets a static IP address via NetworkManager
- **Certificate generation:** Creates a unique self-signed TLS certificate for Grafana
- **Service management:** Starts/stops/restarts InfluxDB, Telegraf, and Grafana services
- **Credential storage:** Writes PowerFlex gateway credentials to `clusters.yaml`

### Recommendations

- Review the scripts before running them on any system
- Run these scripts only on a dedicated monitoring VM, not on shared or production systems
- The `prep_powerflex_monitoring.sh` script is designed for one-time use during initial setup

## Certificate Generation

The `generate_grafana_cert.sh` script creates a unique self-signed RSA 4096-bit certificate on first setup. This replaces the demo certificate included in the pre-built VM image, ensuring each deployed VM has its own unique key pair.

The generated certificate is placed at:
- `/etc/grafana/powerflex.crt` (certificate, mode 644)
- `/etc/grafana/powerflex.key` (private key, mode 600)

For production environments, replace the self-signed certificate with a certificate signed by your organization's certificate authority.

## Credential Handling

The setup scripts prompt for PowerFlex gateway credentials and store them in `/var/local/telegraf-powerflex/clusters.yaml`. This file should have restrictive permissions:

```bash
chmod 600 /var/local/telegraf-powerflex/clusters.yaml
```

- Use a dedicated PowerFlex user account with **monitor-level permissions only**
- Passwords are entered interactively (hidden input) and are not written to logs, but are stored in plain text in `clusters.yaml`
- The `prep_vm_for_template_or_deploy.sh` script resets `clusters.yaml` to placeholder values when preparing the VM as a template

## Grafana Admin Password

The default Grafana admin password is displayed at the end of the setup process. Change this password immediately after first login.
