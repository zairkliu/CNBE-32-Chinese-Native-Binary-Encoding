# Security Policy

CNBE-32 is currently a research prototype. It is not a production security product.

## Supported versions

Security review applies to the Python SDK baseline on the `main` branch. Experimental directories (OS, RISC-V, hardware, finance, biology, physics) may not receive the same level of review.

## Reporting a vulnerability

Open a private security advisory on GitHub if available, or contact the maintainer. Include affected files, reproduction steps, expected impact, environment details, and whether the issue affects the stable Python SDK or an experimental prototype.

## Scope

**In scope:** Python package installation behavior, database path handling, unsafe file loading behavior, CI/release process issues, implementation consistency issues that could cause incorrect encoding.

**Out of scope:** Unsupported experimental deployments, OS/kernel prototypes, financial prediction performance, model behavior claims, third-party dependency vulnerabilities without CNBE-32-specific impact.
