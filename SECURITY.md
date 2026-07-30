# 3Craft Security Policy

## Supported scope

3Craft is currently a **local MVP** without authentication or tenant isolation. It is not a production service.

| Target | Security fixes |
|---|---|
| Latest code on the GitHub default branch | Supported |
| Earlier commits, forks, or modified deployments | Not supported |
| Public release artifacts | Not yet provided |

## Deployment precautions

- Bind the API and Vite only to `127.0.0.1`, as configured by default.
- Do not expose the current API to the Internet, a public LAN, or an untrusted multi-user environment.
- Production deployment requires authentication, owner scoping, CSRF and IDOR defenses, rate limits, quotas, retention controls, and object-storage authorization.
- Treat `.threecraft-data/` and uploaded images as private data. Never commit them to a shared repository.
- Use `THREECRAFT_IMAGE_PROVIDER=null` until a real provider adapter has been implemented and reviewed. Supplied-image conversion remains available when generation is disabled.

Implemented defenses and outstanding release gates are recorded in the [implementation status](docs/implementation-status.md).

## Reporting a vulnerability

Do not report vulnerabilities in a public issue. Open a private security advisory under **Security → Report a vulnerability** in this repository.

Include as much of the following as practical:

- affected commit or version;
- reproduction conditions and minimal steps;
- expected and actual behavior;
- impact and attack prerequisites;
- possible mitigations.

Do not attach real secrets, private images, or personal information; use safe fixtures instead. Reports remain private until a fix and disclosure date are agreed. We do not currently guarantee a response SLA, but verifiable reports receive priority review.

## Areas of particular concern

We treat the following issues as especially important:

- image parser/decompression bombs or validation bypasses;
- artifact-ID/path traversal and private-file disclosure;
- early exposure of incomplete job artifacts;
- provenance bypasses that misclassify generated evidence as observed;
- bounds or VarInt errors in the schematic parser/writer;
- unintended network exposure through the Vite proxy or CORS;
- dependency supply-chain issues.

Use the GitHub issue templates for ordinary bugs and feature requests.
