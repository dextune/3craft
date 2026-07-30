# Implementation Roadmap and Backlog

> Current implementation status and concrete evidence are tracked in [`../implementation-status.md`](../implementation-status.md). This document also includes the remaining production roadmap.

## 1. Planning principles

- Build a thin end-to-end vertical slice first.
- Prove schematic round-trip before polishing the UI.
- Develop in parallel with fixtures/fake adapters instead of waiting for a real reconstruction model.
- Spike the highest-uncertainty areas—models, Minecraft formats, and viewer performance—early.
- Every milestone requires test evidence and gates before completion.
- Estimates are person-day ranges, not schedule commitments.

Original production-team assumptions:

- one full-stack/graphics engineer;
- one ML/geometry engineer;
- part-time infrastructure/QA support;
- estimated 7–11 weeks for two people working in parallel;
- subject to actual provider, license, and VRAM findings.

The current repository demonstrates a smaller, honest local MVP and does not imply completion of every production milestone below.

## 2. M0: Bootstrap and decision gates

Estimate: 3–5 person-days

### Work

- `BOOT-001`: monorepo/directory skeleton
- `BOOT-002`: pin Node/Python runtimes
- `BOOT-003`: exact dependencies and lockfiles
- `BOOT-004`: lint/type/test/build scripts
- `BOOT-005`: local Postgres/Redis/S3-compatible environment for the production target
- `BOOT-006`: contract package and schema CI
- `BOOT-007`: MIT attribution and third-party inventory
- `DEC-001`: target Minecraft/WorldEdit/DataVersion
- `DEC-002`: API framework/queue implementation
- `DEC-003`: anonymous/authenticated alpha policy
- `DEC-004`: source/artifact retention defaults

### Completion criteria

- install/test/build from a clean checkout;
- local service health;
- Web → API hello contract;
- Python/TypeScript schema-fixture parity;
- core ADRs in [12-adrs-and-risks.md](12-adrs-and-risks.md) Accepted.

## 3. M1: Deterministic vertical slice

Estimate: 6–9 person-days

Goal:

```text
fixture PNG → provenance/sense → relief → 32 voxels → stone/safe palette → `.schem` → parser → viewer
```

### Pipeline

- `REF-001`: EvidenceAsset/ReferenceSet
- `REF-002`: canonical JSON/hash
- `REF-003`: PNG/JPEG/WebP decode/normalize
- `REF-004`: alpha/heuristic matte
- `REF-005`: minimal SensePack
- `REL-001`: deterministic depth/height relief
- `MESH-001`: canonical coordinates/primitive validation
- `VOX-001`: surface occupancy
- `PAL-001`: minimal curated palette
- `EXP-001`: one-block and primitive schematic writer
- `EXP-002`: independent parser round-trip

### Web/backend

- `API-001`: local direct asset adapter
- `API-002`: fixture conversion command/job skeleton
- `VIEW-001`: viewer runtime/instanced blocks
- `VIEW-002`: binary/JSON debug preview

### Completion criteria

- Run the deterministic slice with one command/test.
- Round-trip one-block and asymmetric-axis fixtures.
- Display fixtures in the browser.
- Produce the same semantic hash for the same input.
- Require no external AI or GPU.

The current local MVP substantially implements this slice using direct 2.5D voxel relief rather than a general relief mesh intermediate.

## 4. M2: Production intake and sufficiency

Estimate: 6–9 person-days

- `SRC-001`: unified image-first resolver; supplied bytes override prompt
- `SRC-002`: invalid supplied bytes fail without generated fallback
- `ASSET-001`: upload session/signed upload
- `ASSET-002`: server signature/decode/pixel limits
- `ASSET-003`: canonical re-encode/EXIF/color
- `ASSET-004`: private storage/owner
- `SENSE-001`: segmentation adapter
- `SENSE-002`: matte confidence/edges/depth/palette
- `SENSE-003`: transform chain/reverse mapping
- `SUF-001`: route-aware issue policy
- `SUF-002`: pass/conditional/reject action
- `SUF-003`: user messages/remedies
- `GEN-001`: image-provider port/null adapter
- `GEN-002`: generated provenance
- `SEC-001`: malformed/adversarial upload fixtures

Completion criteria:

- Upload and generated assets use the same downstream contract.
- Supplied images always take precedence.
- Invalid supplied images never invoke generation.
- Generated assets cannot be marked observed.
- Blockers prevent production queue creation.
- Original/canonical/derived lineage exists.
- UI provides matte/sufficiency review.

The local MVP implements source precedence, bounded decode/canonicalization, heuristic SensePack, provenance, and fail-closed relief sufficiency. Signed uploads, owner isolation, and advanced review remain production work.

## 5. M3: Reconstruction-model selection

Estimate: 8–13 person-days

### Research/spike

- `ML-001`: candidate licenses/data policies
- `ML-002`: common adapter/capabilities
- `ML-003`: candidate A
- `ML-004`: candidate B
- `ML-005`: hosted candidate if needed
- `ML-006`: 24-input corpus benchmark
- `ML-007`: VRAM/latency/cost/failure measurements
- `ML-008`: blind quality evaluation
- `ML-009`: primary/fallback ADR

### Mesh

- `MESH-002`: raw-intake sandbox
- `MESH-003`: finite/degenerate/component report
- `MESH-004`: normals/holes/repair
- `MESH-005`: coordinate/ground normalization
- `MESH-006`: texture/color handoff
- `MESH-007`: simplification benchmark

Completion criteria:

- Pass hard license gates.
- Pin selected model/profile versions.
- Block invalid output downstream.
- Produce raw/repaired artifacts and reports.
- Define primary/fallback/relief policy.

None of this milestone is claimed by the current local MVP.

## 6. M4: Voxel, palette, and export core

Estimate: 10–15 person-days

- `VOX-002`: solid occupancy
- `VOX-003`: hollow/shell
- `VOX-004`: components/morphology/thin features
- `VOX-005`: deterministic semantic hash
- `COL-001`: UV/vertex/material color sampling
- `PAL-002`: versioned safe-basic data
- `PAL-003`: target block validator
- `PAL-004`: perceptual mapper
- `PAL-005`: regularization/dithering
- `BOM-001`: JSON/CSV
- `CODEC-001`: production voxel binary/RLE
- `CODEC-002`: TypeScript decoder golden
- `EXP-003`: complete Sponge v3 adapter
- `EXP-004`: BOM/coordinate semantic validation
- `EXP-005`: delivery-bundle/leak gate
- `EXP-006`: actual WorldEdit smoke matrix

Completion criteria:

- 16/32/64 surface/hollow/solid fixtures;
- target-validated safe palette;
- Python/TypeScript codec parity;
- all export gates;
- actual WorldEdit import.

The local MVP implements deterministic 16/32/64 relief modes, curated palette, BOM JSON, Sponge v3 writing, built-in semantic validation, and independent `nbtlib` parsing. Production binary/CSV, broader palette validation, and actual WorldEdit smoke remain incomplete.

## 7. M5: Durable jobs and backend

Estimate: 8–12 person-days

- `DB-001`: owners/assets/references/jobs/attempts/artifacts/events
- `DB-002`: migrations/test fixtures
- `JOB-001`: state machine
- `JOB-002`: idempotency/request hash
- `JOB-003`: outbox/queue publication
- `JOB-004`: leases/heartbeats/fencing
- `JOB-005`: stage manifests/reuse
- `JOB-006`: retries/backoff/dead-letter
- `JOB-007`: cancellation/races
- `API-003`: jobs/SSE/polling
- `API-004`: artifact-download authorization
- `STORE-001`: candidate/validated/published states
- `STORE-002`: retention/deletion
- `OBS-001`: logs/metrics/traces

Completion criteria:

- single execution/publication after duplicate queue delivery;
- worker-termination recovery;
- cancel/complete race handling;
- owner scoping;
- candidates cannot be downloaded;
- retention tests.

The current process-local manager provides an asynchronous API shape, idempotency, monotonic progress, bounded workers, terminal errors, and completed-only downloads. It is not durable across process restarts.

## 8. M6: Product UI and viewer

Estimate: 8–12 person-days

- `WEB-001`: application shell/routes/design tokens
- `WEB-002`: unified image-first source form
- `WEB-003`: mask/sufficiency review
- `WEB-004`: settings/validation
- `WEB-005`: job progress/SSE/polling
- `WEB-006`: errors/retry/cancel
- `WEB-007`: result/BOM/download
- `VIEW-003`: production binary/Web Worker
- `VIEW-004`: palette instancing
- `VIEW-005`: camera/grid/orientation
- `VIEW-006`: layer clipping/selection
- `VIEW-007`: canonical capture
- `VIEW-008`: disposal/leak probe
- `A11Y-001`: keyboard/text alternative

Completion criteria:

- image-first and generated-fallback E2E;
- refresh/reconnect in the production architecture;
- 64-axis performance;
- repeated disposal;
- keyboard core flow;
- WebGL fallback.

The local MVP has a unified English source form, settings, polling, lazy instanced viewer, layer control, BOM, and downloads. Full routing, persistence, browser E2E matrix, and accessibility audit remain backlog.

## 9. M7: Security, operations, and staging

Estimate: 6–10 person-days

- `SEC-002`: authentication/session/CSRF/CORS
- `SEC-003`: IDOR/owner integration
- `SEC-004`: rate/quota/admission
- `SEC-005`: worker sandbox/egress/resources
- `SEC-006`: secret/dependency/model scanning
- `OPS-001`: production containers
- `OPS-002`: staging topology
- `OPS-003`: dashboards/alerts
- `OPS-004`: backup/restore
- `OPS-005`: provider circuit breaker
- `OPS-006`: cost telemetry
- `OPS-007`: release/rollback rehearsal

Completion criteria:

- [13-operations-and-release.md](13-operations-and-release.md) smoke;
- zero critical security defects;
- alerts actually tested;
- restore and rollback evidence;
- quota/cost protection.

## 10. M8: Beta hardening

Estimate: 7–12 person-days

- `QA-001`: complete fixture/golden regression
- `QA-002`: reconstruction benchmark rerun
- `QA-003`: browser compatibility
- `QA-004`: Minecraft/WorldEdit matrix
- `QA-005`: load/soak
- `QA-006`: provider outage/OOM/storage incident drills
- `QA-007`: UX copy/known limitations
- `QA-008`: privacy/retention UI
- `QA-009`: release candidate
- `QA-010`: canary/rollback

Completion requires every MVP release condition in [10-testing-and-quality-gates.md](10-testing-and-quality-gates.md).

## 11. Parallelization

### Track A: Contracts/backend

M0 → M1 contracts → assets/jobs/storage → operations

### Track B: Geometry/ML

fixtures → relief → model benchmark → mesh → voxel/palette/export

### Track C: Web/viewer

gpthreejs viewer-pattern analysis → fixture viewer → create/job UI → production viewer

Synchronization points:

- M1 VoxelModel/preview contract;
- M2 ReferenceSet/SufficiencyReport;
- M3 ReconstructionResult/MeshMetadata;
- M4 DeliveryManifest;
- M5 JobEvent/API.

Do not create temporary incompatible shapes on both sides before contract fixtures merge.

## 12. Critical path

```text
Choose target schematic
→ primitive export round-trip
→ fix VoxelModel/axes
→ reconstruction adapter/mesh normalization
→ color/palette
→ durable jobs
→ product E2E
→ staging/compatibility
```

Deferring Minecraft export until the end would force coordinate and palette redesign. This is why M1 includes a minimal exporter.

## 13. MVP P0/P1/P2 backlog

### P0

- source/upload/generated provenance;
- image-first precedence and fail-closed invalid-image handling;
- fail-closed sufficiency;
- relief plus primary reconstruction in the production target;
- 16/32/64;
- surface/hollow/solid;
- safe palette;
- viewer/BOM;
- Java `.schem` round-trip;
- private storage/job recovery;
- security/release gates.

### P1

- generated multi-view;
- custom mask editor;
- color-rich/natural/survival profiles;
- advanced layer viewer;
- GLB/imported mesh;
- result library/authentication;
- `.litematic`.

### P2

- Bedrock `.mcstructure`;
- custom/mod palette;
- build order/instructions;
- block-replacement editor;
- public gallery/sharing;
- batch/public API;
- direct server/world integration.

## 14. Definition of Ready

- requirement, risk, and owner;
- input/output contract;
- dependencies and prerequisites;
- tests and acceptance;
- security/privacy/cost effect;
- feature-flag/rollback need;
- fixtures ready.

## 15. Definition of Done

- code review;
- unit/contract/integration tests;
- lint/type/build;
- failure/cancel/loading handling;
- telemetry;
- secret/user-content review;
- documentation/schema updates;
- migration/compatibility;
- acceptance evidence;
- rollback or safe disable.

## 16. Initial two-week execution plan

### Days 1–2

- M0 skeleton/runtime/dependency pins;
- choose target `.schem`/DataVersion;
- contract schema and CI.

### Days 3–5

- canonical hash/ReferenceSet;
- primitive mesh/VoxelModel;
- one-block/asymmetric schematic round-trip.

### Days 6–7

- relief mesh;
- 32-axis surface voxels;
- safe-palette subset/BOM.

### Days 8–10

- fixture job/API;
- React page + instanced viewer;
- browser smoke;
- first end-to-end demo.

The two-week objective is a validated schematic and reproducible vertical slice, not a polished UI.
