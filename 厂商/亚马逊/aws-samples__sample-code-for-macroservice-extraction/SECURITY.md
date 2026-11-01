# Security Policy

## Disclaimer

This project is provided as sample/educational code accompanying an AWS Prescriptive Guidance
pattern. It is NOT intended for production use without additional security hardening.
See the "Production Hardening Recommendations" section below.

## Reporting Vulnerabilities

If you discover a security vulnerability in this project, please report it by emailing
aws-security@amazon.com. Do not report security vulnerabilities through public GitHub issues.

## Tools and Components

- **macroservice-extractor**: Python tool for extracting macro services from monolithic Java applications
- **card-demo-macroservice**: Macro service that was extracted from the modernized card-demo demonstrating the output of the tool
- **modernized-card-demo**: Modernized Java/Angular application used as source

## Known Security Considerations

| Item | Category | Rationale |
|------|----------|-----------|
| xml.etree.ElementTree used for XML parsing | Security Debt | Parses local Maven pom.xml files only — not untrusted input |
| pickle used for data serialization | Security Debt | Serializes/deserializes self-generated analysis data structures |
| Broad exception handling in file processing | Security Debt | Prevents crashes during batch processing of potentially malformed files |

## Production Hardening Recommendations

Before adapting this code for production use:

- **XML Parsing**: Replace `xml.etree.ElementTree` with `defusedxml` to prevent XXE attacks if any XML input could come from untrusted sources
- **Serialization**: Replace `pickle` with JSON serialization or use `restricted-pickle` if data structures require complex serialization
- **Exception Handling**: Replace bare `except Exception` with specific exception types appropriate to each operation
- **Input Validation**: Add path traversal checks if file paths come from user input
- **Dependencies**: Pin all dependency versions and regularly scan for CVEs

## Resource Cleanup

This project does not deploy any cloud resources. No cleanup required.

## Dependencies

| Dependency | Version | Notes |
|------------|---------|-------|
| Python 3.x | As specified in requirements.txt | Core runtime for macroservice-extractor |
| defusedxml | Not yet added | Recommended replacement for xml.etree.ElementTree |
| PyYAML | As specified in requirements.txt | YAML configuration parsing |
