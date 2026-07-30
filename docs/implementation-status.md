# 3Craft Implementation Status and Validation Evidence

> Baseline date: 2026-07-30
> Implementation assessment: **Executable end-to-end local MVP vertical slice complete**
> Release assessment: **Not a production or beta release**

This document maps the goals in [`plan/README.md`](plan/README.md) to current code. It does not claim completion of every production milestone. It distinguishes implemented and exercised local behavior from unimplemented or unverified production scope.

## 1. Completed local vertical slice

```text
supplied PNG/JPEG/WebP, when present
otherwise deterministic-dev generated image from prompt/default
  → SHA-256 provenance and evidence class
  → canonical RGBA PNG + matte/depth SensePack
  → route-aware fail-closed sufficiency
  → deterministic 2.5D relief
  → 16/32/64 surface/hollow/solid voxels
  → versioned safe full-cube palette + BOM
  → Sponge Schematic v3 / DataVersion 3700
  → semantic round-trip delivery gates
  → local asynchronous job API
  → React/Three.js preview + `.schem` download
```

Implemented boundaries:

| Area | Current implementation |
|---|---|
| Source selection | Supplied bytes always win; generate only when bytes are absent; invalid supplied bytes never fall back |
| Input | PNG/JPEG/WebP magic, decode, MIME, byte/pixel/frame limits, EXIF orientation, canonical PNG |
| Evidence | upload=`observed`, generated=`design-intent`; generated/edited cannot be promoted to observed |
| Sense/sufficiency | Alpha or corner-background matte, depth proxy, diagnostics, `continue/ask/abort` |
| Generation | Local-only `deterministic-dev` procedural illustration and fail-closed `null` provider |
| Form | Deterministic 2.5D relief; no real single-image AI mesh |
| Voxel | Maximum axis 16/32/64, surface/hollow/solid, semantic hash |
| Palette/export | `java-safe-v1` concrete palette, Lab/CIE76 mapping, BOM, gzip NBT Sponge v3 |
| Validation | Built-in NBT reader plus independent `nbtlib==2.0.4`, DataVersion/semantic/BOM gates |
| Backend | FastAPI, process-local `ThreadPoolExecutor`, idempotency, polling/cancel, private local artifacts |
| Frontend | React 19, strict TypeScript, Vite, lazy Three.js viewer, palette-grouped `InstancedMesh`, layer control |
| CLI | Image-first `build`, explicit `convert`/`generate`, loopback `serve` |
| Agent workflow | Root OpenAI/Agent Skills-compatible `SKILL.md` with local-only fail-closed instructions |
| Runtime | Loopback-only API/Web launcher; runtime directories `0700`, files `0600` |

### 1.1 Source-resolution contract

`ThreeCraftPipeline.resolve_source`, `POST /api/v1/sources`, `threecraft build`, and the unified Web form share these invariants:

1. `image_data is not None` always selects upload/canonicalization, even if a prompt exists.
2. `None` means no image; `b""` means an invalid supplied image.
3. Invalid/corrupt/unsupported supplied input reports a validation failure and never invokes generation.
4. A nonblank prompt is used only without an image; blank or omitted prompts use a deterministic documented default.
5. `NullImageProvider` still permits supplied-image conversion and returns 503 only for generation fallback.
6. No arbitrary URL is fetched, and no user image is transmitted to an external provider.

Legacy `/api/v1/assets`, `/api/v1/image-generations`, `convert`, and `generate` interfaces remain available for explicit workflows.

## 2. Planning-milestone mapping

Status describes progress of the current local adapter, not completion of each entire production milestone.

| Milestone | Status | Completed portion | Principal remaining work |
|---|---|---|---|
| M0 Bootstrap | Partially complete | Python/Node skeleton, exact direct dependencies, npm lockfile, test/build scripts, Java 1.20.4/DataVersion 3700 decision, English repository documentation | Postgres/Redis/S3 local stack, generated contract package, remaining Accepted ADRs |
| M1 Deterministic slice | Local complete | Provenance → SensePack → relief → voxel → Sponge v3 → parser → viewer, deterministic hashes, no AI/GPU | Browser visual golden/capture |
| M2 Intake/sufficiency | Local partially complete | Unified image-first source contract, canonicalization, private filesystem, heuristic matte/depth, fail-closed sufficiency | Signed upload, owner scope, production segmentation/provider, retention |
| M3 Reconstruction model | Not implemented | Relief baseline and provider boundaries only | Model/license/VRAM corpus spike, mesh intake/repair, primary/fallback ADR |
| M4 Voxel/export | Local partially complete | 16/32/64 × three modes, safe palette, BOM JSON, Sponge v3, semantic gates | Binary/RLE TypeScript codec, CSV, broader morphology/dithering, actual WorldEdit matrix |
| M5 Durable jobs | Local adapter only | State/progress, request hash/idempotency, terminal persistence, safe download gate, polling/cancel | Database/outbox/Redis, leases/fencing/recovery, SSE, authentication, retention, observability |
| M6 Product UI/viewer | Local partially complete | Unified source form, sufficiency, settings, polling, viewer/BOM/download, instancing, layers/camera, disposal/fallback | Web Worker/binary codec, persisted reconnect, canonical capture, browser/FPS/accessibility matrix |
| M7 Security/operations | Not implemented | Loopback binding, CORS allowlist, input/path limits, private permissions | Auth/CSRF/IDOR/quota/sandbox, containers/staging, alerts/backup/rollback |
| M8 Beta hardening | Not implemented | Local automated regression and one fixture benchmark | Full corpus/golden/browser/Minecraft/load/incident/release matrix |

## 3. Validation evidence

### 3.1 Python, API, and CLI

The image-first implementation added four tests to the previous 29-test baseline, for a total of **33 Python tests**. The focused source-selection set produced:

```text
...........                                                              [100%]
11 passed
```

The full release validation after the English conversion produced:

```text
.................................                                        [100%]
33 passed, 1 third-party deprecation warning
```

Covered behavior includes:

- canonical JSON/hashes, evidence invariants, and settings validation;
- supplied-image precedence with prompt present;
- prompt/default generation only without image;
- no fallback after empty/corrupt supplied bytes;
- null-provider upload success and prompt-only 503;
- corrupt, MIME-mismatched, tiny, and empty-image fail-closed behavior;
- 16/32/64 and surface/hollow/solid semantics and determinism;
- VarInt boundaries, deterministic Sponge v3 writer, and corrupt input;
- built-in reader and independent `nbtlib` semantic parse;
- delivery gates and BOM/semantic-hash equality;
- job completion/failure persistence, idempotency conflicts, and immediate missing-asset rejection;
- API source/upload/generation/conversion/poll/artifact paths and private response headers;
- malformed IDs, path escape, filesystem permissions;
- CLI image-first and prompt-only builds through schematic output.

The only known test warning is a third-party Starlette TestClient deprecation recommending its newer HTTP backend. It is not a product-code warning or test failure.

### 3.2 Frontend

The unified English image-first flow passes a clean lockfile install, strict TypeScript checking, Vite production build, and runtime dependency audit:

```text
npm ci: added 39 packages; audited 40 packages
initial app JavaScript: 202.41 kB (gzip 64.02 kB)
lazy VoxelViewer JavaScript: 551.65 kB (gzip 137.84 kB)
npm audit --omit=dev: 0 vulnerabilities
```

The Three.js chunk loads through `React.lazy` only when a result exists. This build validates types and production bundling, not GPU-specific visual quality or FPS. Those browser/hardware gates remain explicit backlog.

### 3.3 Real process/HTTP and CLI E2E

The original local smoke ran Uvicorn and Vite through `./scripts/dev.sh` and exercised:

```text
deterministic generation → canonical source image
→ 16-axis hollow conversion → asynchronous polling completed
→ preview/BOM/schematic download → independent nbtlib parse
```

Observed fixture values:

| Item | Result |
|---|---:|
| Dimensions | 11×16×4 |
| Occupied blocks | 265 |
| Block types | 9 |
| `.schem` bytes | 547 |
| Schematic version | 3 |
| DataVersion | 3700 |
| Preview/schematic privacy | `Cache-Control: private, no-store`, `nosniff` |
| Vite binding | `127.0.0.1:5173`, strict port |
| Web root | HTTP 200 with React root |
| Launcher shutdown | Both listeners and child processes released |

The final release validation also exercised the installed CLI and a real loopback Uvicorn process:

| Path | Observed result |
|---|---|
| CLI image + prompt | `sourceOrigin=upload`, 408 occupied, 4 block types |
| CLI prompt only | `sourceOrigin=generated`, 114 occupied, 7 block types |
| HTTP image + prompt | `201`, upload/observed; supplied file remained authoritative |
| HTTP prompt only | `201`, generated/design-intent via `deterministic-dev` |
| HTTP invalid image + prompt | `400 IMAGE_DECODE_FAILED`; fallback not used |
| HTTP upload conversion | completed, 440 occupied, 3 block types |

Both CLI schematics and the HTTP schematic passed built-in semantic checks and independent `nbtlib` parsing as Sponge version 3/DataVersion 3700. HTTP artifacts retained private/no-store/nosniff headers, and the semantic hash matched the BOM and decoded model.

### 3.4 Baseline benchmark

Environment: Python 3.12.3, Linux 6.8 x86_64, 16 logical CPUs. This is a local diagnostic from one deterministic fixture with `tracemalloc`, not an SLA.

| Axis | Fill | Time | Python peak | Blocks | Schematic |
|---:|---|---:|---:|---:|---:|
| 16 | surface | 50.47 ms | 0.37 MiB | 118 | 505 B |
| 16 | hollow | 71.71 ms | 0.35 MiB | 265 | 547 B |
| 16 | solid | 81.55 ms | 0.36 MiB | 350 | 524 B |
| 32 | surface | 131.50 ms | 0.81 MiB | 468 | 696 B |
| 32 | hollow | 255.81 ms | 0.82 MiB | 1,158 | 861 B |
| 32 | solid | 478.35 ms | 1.38 MiB | 2,587 | 775 B |
| 64 | surface | 573.66 ms | 5.51 MiB | 1,908 | 1,459 B |
| 64 | hollow | 1,244.03 ms | 6.14 MiB | 4,961 | 1,944 B |
| 64 | solid | 3,727.19 ms | 10.24 MiB | 20,383 | 1,726 B |

All nine combinations passed the five delivery gates without worker OOM. This does not replace a fixture/hardware benchmark corpus.

## 4. Issues found and fixed by local audit

The audit was conducted directly by one agent; it did not include an independent reviewer. It combined source-scoped risk searches, lifecycle/API review, clean installation, and process smoke tests.

- Vite bound to `0.0.0.0` → loopback only.
- Occupied port silently selected 5174 → strict port.
- Parent npm exit left an orphan Vite process → direct process ownership and verified cleanup.
- Direct Vite execution used the wrong root → explicit `apps/web` root.
- `GridHelper` and per-rebuild `InstancedMesh` resources leaked → explicit disposal.
- API module import created duplicate apps/job managers → factory called once from the entry point.
- Missing source asset failed only after job creation → synchronous 404 before enqueue.
- Existing artifact root could retain permissive mode → force `0700` on startup.
- Unexpected worker exceptions lost tracebacks → server-side exception logging.
- Preview/BOM/schematic lacked privacy headers → private/no-store/nosniff.
- Separate source tabs allowed ambiguous intent → one source resolver with explicit file precedence.
- Invalid supplied content could be mistaken for absence in future interfaces → explicit `None` versus empty-bytes contract and regression tests.

No application Python/TypeScript source pattern was found for TODO/FIXME, dynamic `eval`/`exec`, shell execution, DOM injection, or credential storage. This does not replace professional penetration testing or independent security review.

## 5. Local delivery gates that pass

- Conversion requires successful decode, canonicalization, provenance, and sufficiency.
- Supplied bytes take precedence in pipeline, API, CLI, Web, and skill instructions.
- Invalid supplied content cannot trigger generated fallback.
- Contracts allow only supported resolutions and fill modes.
- Palette index 0 is air and cannot represent an occupied block.
- Coordinate bounds and semantic-hash invariants are validated.
- Sponge root/version/DataVersion/palette/VarInt/index order parse successfully.
- Writer → reader semantic hash and BOM agree.
- Only completed jobs whose gates pass expose artifacts.
- Malformed identifiers and path escape are rejected.
- Generated assets cannot be labeled observed.
- Agent workflow remains local, rejects arbitrary URL fetching, and returns only validated delivery artifacts.

## 6. Release gates not completed

The following remain, so this repository must not be interpreted as production-ready or as completion of the full plan:

1. Real AI image generation and single-image/multi-view mesh reconstruction.
2. Model license/data-policy review, 20–24-input corpus, and VRAM/quality benchmark.
3. Postgres/Redis/S3, leases/fencing/retry/recovery, and multi-process durability.
4. Authentication, tenant ownership, signed upload/download, quota/rate limits, and retention.
5. SSE, binary voxel codec, Web Worker, and persisted reconnect.
6. Automated real-browser/WebGL GPU, accessibility, FPS, and leak matrix.
7. Manual Minecraft Java 1.20.4 + WorldEdit import matrix.
8. Production containers, staging, observability, backup/restore, rollback, load, and incident drills.
9. Independent code/security review and release sign-off.

## 7. Reproduction commands

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
npm --prefix apps/web ci
make check
./scripts/dev.sh
```

Preferred image-first CLI smoke:

```bash
.venv/bin/threecraft build \
  --image provided.png \
  --prompt "this prompt is ignored because an image exists" \
  --max-axis 16 \
  --fill hollow \
  --out output-from-image

.venv/bin/threecraft build \
  --prompt "blue crystal guardian" \
  --max-axis 16 \
  --fill hollow \
  --out output-from-prompt
```

Each output contains `model.schem`, `preview.json`, `blocks.json`, and `delivery.json`. The CLI result identifies `sourceOrigin` so precedence is observable.

## 8. ChatGPT/OpenAI skill

The repository root contains exactly one [`SKILL.md`](../SKILL.md) with required `name` and `description` frontmatter. It instructs an agent to:

- select an explicitly referenced or most relevant supplied PNG/JPEG/WebP;
- use generation only when no supported image exists;
- fail closed rather than replacing invalid supplied input;
- keep user files local and avoid arbitrary URL fetches;
- run `threecraft build` in a fresh output directory;
- verify delivery status, every gate, BOM totals, semantic hash, and output paths;
- report the deterministic 2.5D limitation accurately.
