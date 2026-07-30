# 3Craft

[![CI](https://github.com/dextune/3craft/actions/workflows/ci.yml/badge.svg)](https://github.com/dextune/3craft/actions/workflows/ci.yml)
[MIT License](LICENSE)

3Craft is an executable local MVP that converts an image into a **Minecraft Java Edition block sculpture** and provides a browser preview, bill of materials (BOM), and Sponge Schematic v3 `.schem` file.

> [!IMPORTANT]
> The current implementation is a deterministic **2.5D relief pipeline**. It does not claim to perform real AI image generation or single-image 360° mesh reconstruction. The `deterministic-dev` fallback is a local procedural fixture provider, not an external AI service.

## Source policy and pipeline

A supplied image is always authoritative. Generation runs only when no image is supplied; an empty, corrupt, or unsupported supplied image fails validation instead of silently triggering fallback content.

```text
supplied PNG/JPEG/WebP, when present
otherwise deterministic-dev generated image
  → SHA-256 provenance and observed/design-intent classification
  → canonical RGBA PNG + matte/depth SensePack
  → route-aware fail-closed sufficiency
  → 16/32/64 relief voxel (surface/hollow/solid)
  → Java-safe full-cube palette + BOM
  → Sponge Schematic v3 / DataVersion 3700
  → built-in reader + independent nbtlib semantic validation
  → FastAPI asynchronous local job + React/Three.js preview
```

| Area | Implementation |
|---|---|
| Input | PNG/JPEG/WebP magic, MIME, decode, EXIF, byte/pixel/frame validation |
| Source resolution | Supplied bytes first; deterministic generation only when bytes are absent |
| Provenance | upload=`observed`, generated=`design-intent`, canonical SHA-256 |
| Voxel | 16/32/64 maximum axis, surface/hollow/solid, deterministic semantic hash |
| Minecraft | Java 1.20.4, DataVersion 3700, Sponge Schematic v3 |
| Backend | FastAPI, process-local worker, private local artifact store |
| Frontend | React, strict TypeScript, lazy Three.js `InstancedMesh` viewer |
| Interfaces | Web UI, CLI, API/OpenAPI, ChatGPT/OpenAI skill, BOM, `.schem` download |

See [Implementation Status and Validation Evidence](docs/implementation-status.md) for milestone coverage and concrete validation output.

## Quick start

### Requirements

- Python 3.12+
- Node.js 20.19+, 22.12+, or 24+
- npm
- Linux/macOS shell for `scripts/dev.sh` (the validated environment is Linux)

### Install

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
npm --prefix apps/web ci
```

### Run

```bash
./scripts/dev.sh
```

- Web: <http://127.0.0.1:5173>
- API/OpenAPI: <http://127.0.0.1:8000/docs>
- Health: <http://127.0.0.1:8000/api/v1/health>

The API and Web app bind only to loopback. If port 5173 or 8000 is occupied, the launcher fails instead of selecting another port, and it cleans up both child processes on exit.

> [!WARNING]
> The current API has no production authentication, tenant isolation, or rate limiting. Do not expose it to the Internet or an untrusted LAN. See the [Security Policy](SECURITY.md).

Run services separately when needed:

```bash
.venv/bin/python -m uvicorn services.api.main:app --host 127.0.0.1 --port 8000
npm --prefix apps/web run dev
```

Runtime artifacts are stored under `.threecraft-data/` by default, with directory mode `0700` and file mode `0600`, and are excluded from Git.

## Usage

### One-command image-first build

With an image, that image wins even when a prompt is also provided:

```bash
.venv/bin/threecraft build \
  --image provided.png \
  --prompt "blue crystal guardian" \
  --max-axis 32 \
  --fill hollow \
  --out threecraft-output
```

Without an image, the local deterministic provider uses the prompt. A built-in deterministic default is used when the prompt is blank or omitted:

```bash
.venv/bin/threecraft build \
  --prompt "blue crystal guardian" \
  --out threecraft-output
```

The output directory contains `model.schem`, `preview.json`, `blocks.json`, and `delivery.json`. CLI JSON output reports `sourceAssetId` and `sourceOrigin` (`upload` or `generated`).

### Legacy explicit commands

Convert an existing image directly:

```bash
.venv/bin/threecraft convert image.png \
  --max-axis 32 \
  --fill hollow \
  --out threecraft-output
```

Create a deterministic development fixture:

```bash
.venv/bin/threecraft generate \
  "blue crystal guardian" \
  --out generated-dev.png
```

Run the API from the CLI:

```bash
.venv/bin/threecraft --data-dir .threecraft-data serve
```

See [`.env.example`](.env.example) for environment variables. Set `THREECRAFT_IMAGE_PROVIDER=null` to disable generated fallback while keeping supplied-image processing available.

## ChatGPT/OpenAI skill

The root [`SKILL.md`](SKILL.md) follows the OpenAI/Agent Skills format. When the repository is mounted as a skill, it instructs the agent to:

1. select an explicitly referenced or supplied PNG/JPEG/WebP;
2. use generation only when no supported image exists;
3. fail closed rather than replacing an invalid supplied image;
4. run the one-command build locally;
5. verify delivery gates, BOM totals, semantic hash, and output files;
6. return the `.schem`, preview, BOM, and delivery manifest without overstating 2.5D capabilities.

The workflow does not fetch arbitrary URLs or upload user images to third parties.

## API overview

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Service health |
| `GET` | `/api/v1/capabilities` | Supported strategies, provider, and target |
| `POST` | `/api/v1/sources` | Unified optional-file/optional-prompt source resolution; file wins |
| `POST` | `/api/v1/assets` | Legacy image upload and canonicalization |
| `GET` | `/api/v1/assets/{id}` | Provenance, SensePack, and sufficiency |
| `GET` | `/api/v1/assets/{id}/image` | Private canonical source image |
| `POST` | `/api/v1/image-generations` | Legacy deterministic-dev image generation |
| `POST` | `/api/v1/conversions` | Create an asynchronous conversion |
| `GET` | `/api/v1/jobs/{id}` | Poll progress or terminal state |
| `POST` | `/api/v1/jobs/{id}/cancel` | Attempt safe cancellation |
| `GET` | `/api/v1/jobs/{id}/{preview\|bom\|schematic}` | Retrieve a validated artifact |

The running OpenAPI document contains the exact request and response schemas.

## Validation

```bash
make check
```

Or run the principal checks separately:

```bash
.venv/bin/python -m pytest -q
npm --prefix apps/web run build
```

The current baseline is **33 Python tests**, a clean `npm ci`, a strict TypeScript/Vite build, real local HTTP and CLI smoke tests, and an independent `nbtlib` parse. CI runs the Python tests and Web build on pushes and pull requests.

## Repository layout

```text
threecraft/                    Python domain, pipeline, API, and export
services/api/                  ASGI entry point
apps/web/                      React/Vite/Three.js frontend
tests/                         Unit, integration, API, and CLI tests
docs/implementation-status.md Current implementation scope and evidence
docs/plan/                     Product, technical, and operations roadmap
scripts/dev.sh                 Loopback-only local launcher
SKILL.md                       ChatGPT/OpenAI skill workflow
```

## Documentation

- [Implementation status and concrete validation evidence](docs/implementation-status.md)
- [Complete product and technical plan](docs/plan/README.md)
- [Changelog](CHANGELOG.md)
- [Contribution Guide](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)

## Current limitations

- Real AI image generation and 360° mesh reconstruction are not connected.
- There is no Postgres, Redis, S3, durable retry/recovery, or production authentication.
- A manual Minecraft/WorldEdit import compatibility matrix remains production backlog.
- Browser/GPU-specific WebGL quality and FPS automation and an independent security review have not been completed.
- The only target is Java Edition 1.20.4/DataVersion 3700 with the safe concrete full-cube palette.

The [planning documents](docs/plan/README.md) and [implementation status](docs/implementation-status.md) describe the production roadmap explicitly.

## Contributing and license

Read [CONTRIBUTING.md](CONTRIBUTING.md) before contributing. Report vulnerabilities through the private process in [SECURITY.md](SECURITY.md), not a public issue.

3Craft is distributed under the [MIT License](LICENSE). Minecraft is a trademark of Microsoft Corporation. 3Craft is not affiliated with or endorsed by Mojang Studios or Microsoft.
