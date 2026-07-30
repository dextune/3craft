# 3Craft Contribution Guide

Thank you for your interest in 3Craft. This repository is currently a **local MVP** that turns images into 2.5D reliefs and Sponge v3 `.schem` files for Minecraft Java Edition. We do not accept changes that could misrepresent it as real AI mesh reconstruction or a production multi-tenant service.

## Getting started

Requirements:

- Python 3.12+
- Node.js 20.19+, 22.12+, or 24+
- npm

Development environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
npm --prefix apps/web ci
make check
```

Run the local API and Web app together with:

```bash
./scripts/dev.sh
```

Both servers bind only to loopback. Runtime artifacts are stored under `.threecraft-data/` and must not be committed to Git.

## Issues and security reports

- Use the GitHub issue templates for reproducible bugs and general feature proposals.
- Do not open a public issue for vulnerabilities, path traversal, malicious-upload bypasses, or possible artifact disclosure. Follow the [Security Policy](SECURITY.md) instead.
- Changes that add a real AI provider, hosted storage, or external URL fetching require prior review of data policy, licensing, cost, and egress.

## Core invariants

Changes must preserve these contracts:

1. A supplied image takes precedence; generation is used only when no image is supplied.
2. Invalid supplied images fail closed and must never trigger generated fallback content.
3. Generated or edited assets must never be labeled as `observed` evidence.
4. Downloads must remain unavailable after invalid input, a sufficiency blocker, or a failed delivery gate.
5. Semantic hashes reflect block states and coordinate meaning, not palette-index order.
6. Palette index 0 is `minecraft:air` and cannot be used for an occupied block.
7. The supported export target is Sponge Schematic v3 for Java 1.20.4/DataVersion 3700.
8. The frontend uses instancing rather than one React component per block.
9. Three.js geometry, materials, controls, observers, and animation loops are disposed explicitly.
10. Do not add arbitrary URL image fetching, hard-coded secrets, or external transmission of user files.

## Change procedure

1. Link a relevant issue first when one exists.
2. Keep each change focused on one purpose.
3. Include tests and documentation whenever behavior or a contract changes.
4. Stage only source files; exclude `.venv`, `node_modules`, `dist`, and runtime artifacts.
5. Document validation commands and results, known limitations, and security effects in the pull request.

Use the recommended commit format `type(scope): summary`. Examples:

```text
feat(export): validate Sponge v3 block data
fix(viewer): dispose instanced resources on rebuild
docs(readme): clarify local MVP limitations
```

## Required validation

Minimum validation:

```bash
.venv/bin/python -m pytest -q
npm --prefix apps/web run build
```

If dependencies or installation steps change, reproduce the result in a clean virtual environment and with `npm ci`. Schematic changes must pass both the built-in reader and an independent `nbtlib` parse.

## Documentation

- [Current implementation status and validation evidence](docs/implementation-status.md)
- [Complete product and technical plan](docs/plan/README.md)
- [Security Policy](SECURITY.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)

By submitting a contribution, you agree that it may be distributed under the repository's [MIT License](LICENSE).
