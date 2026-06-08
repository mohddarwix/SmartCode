# Security Policy

## Supported Versions

Only the latest commit on the `main` branch is actively supported.
Older commits are not patched; please update to `main` before filing a report.

| Branch | Supported |
|--------|-----------|
| `main` (latest) | Yes |
| Any older commit | No |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**
Public disclosure before a fix is available puts the live deployment at risk.

Instead, send an email to **darwishmohammad433@gmail.com** with:

1. A concise description of the vulnerability.
2. Steps to reproduce (include any relevant request/response snippets, sanitized of real credentials).
3. The potential impact as you understand it.
4. Whether you would like acknowledgement in the fix commit or release notes.

We will acknowledge receipt within **72 hours** and aim to ship a fix or mitigation within **14 days**, depending on severity and complexity.

## Scope

The live deployment at [smartcodelau.com](https://smartcodelau.com) is the only actively maintained instance.
Self-hosted instances are the responsibility of the operator.

## Out of Scope

- Vulnerabilities in third-party dependencies that already have published CVEs (open an issue pointing to the CVE instead).
- Issues that require physical access to the server.
- Social engineering attacks against the authors or users.
- Theoretical attacks with no practical exploit path.
