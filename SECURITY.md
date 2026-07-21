# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |
| < 1.0   | No        |

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not** open a public issue.

Report it privately to the project maintainers. We will acknowledge within 48 hours
and aim to resolve within 30 days.

## Security Considerations

This project is a Claude Code skill harness — it orchestrates AI sub-skills and
runs a knowledge-base crawl pipeline. Key points:

- **No sensitive data storage** — all configuration is in plaintext files. Do not commit API keys.
- **Environment variables** — copy `.env.example` to `.env` for secrets; `.env` is in `.gitignore`.
- **External API calls** — `knowledge_updater.py` makes outbound HTTP calls to ArXiv and Semantic Scholar APIs. These are read-only and do not transmit local data.
- **File system writes** — the updater only appends to `SECOND-KNOWLEDGE-BRAIN.md`.
