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

## SSL/TLS Certificates

The repository includes self-signed demo certificates (`powerflex-DEMO-ONLY.crt` and `powerflex-DEMO-ONLY.key`) for initial setup and testing. **These must be replaced for production use.**

If you are using the pre-built monitoring VM, the setup script generates unique certificates automatically during first-time configuration.

### Generating Your Own Certificates

```bash
openssl req -x509 -nodes -days 3650 -newkey rsa:4096 \
  -keyout /etc/grafana/powerflex.key \
  -out /etc/grafana/powerflex.crt \
  -subj "/CN=PowerFlex Monitoring"
```

Set appropriate file permissions:

```bash
chmod 600 /etc/grafana/powerflex.key
chmod 644 /etc/grafana/powerflex.crt
```

Update the certificate paths in `/etc/grafana/grafana.ini` under the `[server]` section if you use different filenames.

## Credential Management

### PowerFlex Cluster Credentials (`clusters.yaml`)

The `clusters.yaml` file contains your PowerFlex gateway credentials. Protect it with restrictive permissions:

```bash
chmod 600 /var/local/telegraf-powerflex/clusters.yaml
```

- Use a dedicated PowerFlex user account with **monitor-level permissions only**
- Do not use administrative accounts for monitoring
- Rotate credentials periodically

### Grafana Admin Password

The default Grafana admin password should be changed on first login. The pre-built VM uses an initial password provided during setup — change it immediately after verifying access.

### Grafana Secret Key (Optional)

The `secret_key` setting in `grafana.ini` encrypts secrets stored in Grafana's database (e.g., data source passwords). In the default configuration, no sensitive credentials are stored in Grafana since InfluxDB connects on localhost without authentication.

If you add additional data sources with stored credentials, consider enabling `secret_key`:

```ini
[security]
secret_key = <your-random-key>
```

Generate a random key with:

```bash
openssl rand -hex 20
```

## Network Security

- Grafana listens on port 443 (HTTPS) by default
- InfluxDB listens on port 8086 (localhost only by default)
- Use firewall rules to restrict access to only authorized users and networks
- The monitoring VM does not need inbound access from the PowerFlex cluster — it initiates all connections outbound to the PowerFlex REST API
