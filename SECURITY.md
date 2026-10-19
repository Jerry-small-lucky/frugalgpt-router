# Security Policy

## Supported scope

This repository is the **Community Edition** — a rule-based demonstration.
It is **not** the commercial product and is **not** intended for production or
public internet exposure.

- Bind to `127.0.0.1` only (the built-in API does this by default).
- There is **no authentication, no rate limiting, no audit log** in the
  Community Edition.
- Do not put real customer data, production API keys, or confidential prompts
  through the demo API.

## Reporting a vulnerability

If you find a security issue in this repository, please report it privately to
the maintainer (3759513835@qq.com) rather than opening a public issue. Include:

- affected version/commit;
- reproduction steps;
- impact assessment;
- suggested fix (if any).

We aim to acknowledge within 5 business days and to publish a fix or mitigation
within 30 days for confirmed issues.

## Scope exclusions

The following are **out of scope** for this repository:

- the commercial FrugalGPT Router Pro / Enterprise products;
- deployment hardening of third-party model providers;
- issues caused by exposing the demo API to the public internet;
- social engineering or physical attacks.
