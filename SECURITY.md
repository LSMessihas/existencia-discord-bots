# Security Policy

## Reporting a Vulnerability

If you discover a security issue in this project, please report it privately instead of opening a public GitHub issue.

Do not publicly disclose:

- Discord bot tokens
- API keys
- Credentials
- Private configuration values
- Database contents
- Security vulnerabilities that could be exploited

When reporting a vulnerability, please include:

- A clear description of the issue
- Steps to reproduce it
- The affected bot or component
- Any relevant logs or screenshots

## Supported Versions

This repository is currently maintained on the latest version available in the `main` branch.

Security fixes, when necessary, will be applied to the latest version of the project.

## Credentials

Real credentials are never intended to be stored in this repository.

Configuration values such as Discord bot tokens must be provided through local environment variables using `.env` files.

The provided `.env.example` files contain only placeholder values and must not contain real credentials.

## Disclosure

Please allow reasonable time for a reported security issue to be reviewed and fixed before publishing details publicly.
