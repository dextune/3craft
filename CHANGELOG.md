# Changelog

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Changes remain under `Unreleased` until the project has a stable public API.

## [Unreleased]

### Added

- PNG/JPEG/WebP upload and deterministic local development-image generation
- Unified image-first `POST /api/v1/sources` flow: supplied bytes always win, and generation runs only when no image is supplied
- `threecraft build` for one-command source resolution, conversion, validation, and artifact delivery
- OpenAI/ChatGPT-compatible root `SKILL.md` with local-only, fail-closed workflow instructions
- Provenance, canonicalization, SensePack, and fail-closed sufficiency checks
- Deterministic 16/32/64 surface, hollow, and solid relief voxelization
- Java-safe concrete palette, BOM, and Sponge Schematic v3 export
- FastAPI local asynchronous jobs, CLI, and React/Three.js preview
- Independent `nbtlib` semantic validation and a 33-test regression suite
- GitHub CI, contribution/security policies, and issue/pull-request templates
- English user-facing copy, runtime messages, configuration, and planning documentation

### Known limitations

- No real AI image generation or mesh reconstruction
- No production database, queue, object storage, or authentication
- No verified Minecraft/WorldEdit or browser/GPU compatibility matrix

See [`docs/implementation-status.md`](docs/implementation-status.md) for detailed implementation evidence.
