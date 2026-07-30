# Testing Strategy and Quality Gates

## 1. Quality principles

- Tests are completion criteria, not an appendix written after implementation.
- Separate ML quality, deterministic geometry, export validity, and service reliability.
- An attractive preview cannot make an invalid schematic pass.
- Metrics are necessary conditions; subjective appeal cannot bypass a hard gate.
- Verify freshness of input, artifact, and review hashes.
- Default to fail-closed rather than fail-open.
- A supplied image must win in every interface, and an invalid supplied image must never invoke fallback generation.

## 2. Test pyramid

```text
                 Human/Model Quality Eval
             Browser + Minecraft Compatibility E2E
          API/Queue/Worker/Storage Integration
       Contract/Geometry/Voxel/Exporter Unit & Golden
```

### 2.1 Unit

- canonical JSON/hash;
- evidence classification;
- source resolution (`None` versus empty bytes);
- transform chain/reverse mapping;
- sufficiency policy;
- state transitions;
- idempotency hashes;
- coordinates/scale;
- primitive voxelization;
- components/morphology;
- color distance/palette filters;
- RLE/binary codecs;
- BOM;
- schematic primitives/VarInt helpers;
- error redaction;
- retention calculations.

### 2.2 Contract

- valid/invalid JSON Schema fixtures;
- TypeScript/Python fixture parity;
- previous-schema read compatibility;
- unknown-enum fail-fast behavior;
- OpenAPI example validation;
- binary Python writer ↔ TypeScript reader;
- upload=`observed` and generated=`design-intent` provenance.

### 2.3 Integration

Production target:

- API + Postgres;
- API + private object storage;
- outbox + queue;
- queue + worker lease;
- stage-manifest recovery;
- fake/timeout provider;
- signed-URL owner/expiry;
- cleanup/retention.

Current local integration:

- FastAPI + private local store + process-local job manager;
- unified multipart `/api/v1/sources`;
- schematic writer + built-in and independent parsers;
- idempotency and fail-closed terminal job persistence.

### 2.4 E2E

- supplied image → conversion → viewer → download;
- prompt-only generated fallback → conversion;
- supplied image plus prompt still uses upload and does not call generation;
- invalid supplied bytes fail without fallback;
- blank/no prompt selects the deterministic default only when no image exists;
- refresh/SSE reconnect in production;
- cancellation/retry;
- reconstruction failure/allowed fallback;
- export-validation failure;
- cross-owner access in production;
- browser resource lifecycle.

### 2.5 Evaluation

- reconstruction-model comparison;
- voxel recognizability;
- block-palette impression;
- hidden-surface plausibility;
- failure taxonomy by input challenge.

## 3. Fixture structure

```text
tests/fixtures/
├── images/
│   ├── valid/
│   ├── challenging/
│   ├── invalid/
│   └── generated/
├── references/
├── sense-packs/
├── meshes/
│   ├── primitives/
│   ├── valid/
│   └── malformed/
├── voxel/
├── palettes/
├── schematics/
└── jobs/

tests/golden/
├── relief/
├── mesh-to-voxel/
├── voxel-codec/
├── schematic-roundtrip/
├── browser-captures/
└── benchmark-manifests/
```

Every external fixture manifest records:

- source;
- license;
- checksum;
- intended use;
- challenge tags;
- expected route/gate;
- redistribution permission.

Use Git LFS or a versioned fixture archive for large binaries, with checksums and fetch procedures in the repository.

## 4. Input test matrix

| Fixture | Expected result |
|---|---|
| transparent PNG | Prefer alpha, pass |
| EXIF-rotated JPEG | Canonical orientation |
| WebP | Decode/canonicalize |
| extension spoof | Reject |
| corrupt/truncated | Reject |
| huge dimensions | Reject before/early in decode |
| animated image | Policy rejection |
| empty alpha | Foreground blocker |
| tiny subject | Ask/abort |
| cropped object | Route-aware issue |
| multiple subjects | Warning/ask |
| thin structure | Risk warning |
| generated source | `design-intent` provenance |
| generated as observed | Schema failure |
| image + prompt | Image wins; provider not called |
| empty bytes + prompt | Reject; provider not called |
| no image + blank prompt | Deterministic documented default |
| no image + null provider | 503 capability unavailable |

## 5. Reconstruction benchmark

### 5.1 Corpus

Use the minimum 24 inputs from [06-reconstruction-and-mesh-pipeline.md](06-reconstruction-and-mesh-pipeline.md). Do not select only training or marketing examples; include expected transparent, reflective, and thin-structure failures.

### 5.2 Quantitative metrics

- source-view silhouette IoU;
- canonical-render edge overlap;
- component count;
- non-manifold/open boundaries;
- watertight rate;
- repair delta;
- 32/64 voxel silhouette loss;
- inference p50/p95;
- peak VRAM/RAM;
- failure/OOM rate;
- cost per job.

### 5.3 Qualitative rubric (1–5)

- subject recognizability;
- overall proportions;
- source silhouette;
- side/back plausibility;
- major features;
- thin/concave structures;
- texture/color;
- suitability of the Minecraft result.

Prefer blind comparison with model names hidden. Record evaluator disagreement.

## 6. Golden tests

### 6.1 Model → voxel

Do not freeze AI inference bytes as golden output. Use curated geometry/relief fixtures to freeze:

- dimensions;
- occupancy/block coordinates;
- component count;
- palette indices;
- BOM;
- semantic hash;
- canonical-render metrics.

An algorithm change that updates a golden requires a diff summary, rationale, expected improvement, and regression review.

### 6.2 Voxel codec

- Python encode/decode;
- TypeScript decode;
- truncated/length overflow;
- invalid palette index;
- decompression-bomb limit;
- random round-trip/property tests.

### 6.3 Schematic

- writer output independently parsed;
- parser result semantically compared with the internal model;
- BOM comparison;
- target-version/block validity;
- corruption fixtures;
- deterministic semantic hash.

## 7. Property and fuzz tests

Targets:

- dimension/linear-index round-trip;
- identity after four axis rotations;
- RLE encode/decode;
- palette reindex preserves meaning;
- sparse/random occupancy;
- NBT/VarInt boundaries;
- malformed preview headers;
- arbitrary filenames/download headers;
- illegal state-machine transitions.

Run fuzz input under size/time limits; minimize crash artifacts into regression fixtures.

## 8. Job and recovery tests

Required for the production target:

1. Same idempotency key/body → same job.
2. Same key/different body → conflict.
3. Duplicate queue delivery → one lease.
4. Worker crash after artifact upload but before database commit.
5. Worker crash after database candidate but before acknowledgment.
6. Stale-worker fencing.
7. Provider timeout/rate limit.
8. Transient storage error.
9. Cancellation during reconstruction.
10. Cancel-versus-complete race.
11. Retry-budget exhaustion.
12. Completed job cannot be reprocessed.
13. Only published artifacts can be downloaded.

Each scenario verifies final database state, orphaned objects, events, and cost counts. The local MVP covers the applicable idempotency, cancellation safety, terminal failure, and artifact-readiness contracts without claiming durable crash recovery.

## 9. Browser tests

Extend the Vite/Playwright preflight, runtime smoke, capture smoke, and disposal principles from gpthreejs.

Required target matrix:

- clean install/typecheck/build;
- zero console/page errors;
- WebGL canvas ready;
- 32/64 fixture loading;
- deterministic canonical capture;
- malformed-preview error;
- WebGL-unavailable fallback;
- resize/DPR;
- ten viewer create/load/dispose cycles;
- stable `renderer.info` geometry/texture counts;
- source/result switching;
- keyboard flow;
- SSE disconnect/poll fallback.

Do not use one exact beauty-PNG hash across OS/GPU combinations. Combine exact hashes in one environment with alpha/semantic/perceptual tolerance across environments.

## 10. Performance benchmarks

### 10.1 Intake

- decode/normalize/matte/depth time;
- peak memory;
- results by image size.

### 10.2 Reconstruction

- cold/warm load;
- inference/repair;
- VRAM/RAM;
- provider network.

### 10.3 Voxel/export

Combinations:

- 16/32/64/128 experimental;
- surface/hollow/solid;
- small/large palette;
- manifold/non-manifold;
- texture/no texture.

Measure:

- voxelization;
- mapping;
- preview encoding;
- schematic export/parse;
- output size.

### 10.4 Viewer

- fetch/decode/build;
- first render;
- frame p50/p95;
- draw calls/triangles/instances;
- GPU-memory proxy;
- post-disposal stability.

## 11. Provisional performance budgets

| Metric | Initial target |
|---|---|
| Ordinary API p95 | ≤500 ms |
| Progress/event delay | ≤2 s |
| 32-axis preview decode + build | Target ≤2 s after download |
| 64-axis viewer | ≥30 FPS on recommended desktop |
| Export round-trip | A few seconds for 32-axis |
| Worker OOM for supported settings | 0 |
| Client long tasks | Avoid repeated work ≥100 ms |
| Stage-manifest overhead | Negligible relative to total job |

Do not turn thresholds into release claims before measuring a baseline. Record CI-machine and production-hardware metadata.

## 12. Quality and delivery gates

### Input

- `GATE-IN-001`: asset validated
- `GATE-IN-002`: provenance/hash valid
- `GATE-IN-003`: route sufficiency is not reject
- `GATE-IN-004`: supplied-image precedence and no invalid-image fallback

### Reconstruction

- `GATE-REC-001`: output parses and is finite/non-empty
- `GATE-REC-002`: canonical coordinates/bounds
- `GATE-REC-003`: route topology capability
- `GATE-REC-004`: license/model provenance

### Voxel

- `GATE-VOX-001`: schema/semantic hash
- `GATE-VOX-002`: dimensions/count
- `GATE-VOX-003`: palette valid
- `GATE-VOX-004`: structural-diagnostics policy

### Review

- `GATE-REV-001`: canonical renders present/fresh
- `GATE-REV-002`: silhouette loss within route threshold
- `GATE-REV-003`: no critical regression

### Export

- `GATE-EXP-001`: parser round-trip
- `GATE-EXP-002`: coordinate/block equality
- `GATE-EXP-003`: BOM equality
- `GATE-EXP-004`: target compatibility
- `GATE-EXP-005`: no private path/content leak

### Runtime

- `GATE-RUN-001`: Web build/browser smoke
- `GATE-RUN-002`: resource disposal
- `GATE-RUN-003`: worker recovery
- `GATE-RUN-004`: authorization

Acceptance is forbidden when a required gate is missing or stale.

## 13. CI pipeline

Current CI:

1. install pinned Python dependencies;
2. run the Python regression suite;
3. clean-install Web dependencies;
4. run strict TypeScript/Vite build.

Target pull-request pipeline:

1. formatting/lint;
2. Python/TypeScript typecheck;
3. unit/contract tests;
4. schema-generation drift;
5. frontend/backend build;
6. service integration;
7. voxel/schematic golden tests;
8. browser E2E with fixture provider;
9. container build;
10. dependency/license/secret scan.

Scheduled:

- actual GPU-model smoke;
- reconstruction benchmark subset/full;
- performance regression;
- cross-browser;
- retention/backup restore;
- vulnerability/model-checksum checks.

Release candidate:

- staging real provider;
- 20+ corpus;
- actual WorldEdit compatibility;
- load/soak;
- rollback rehearsal.

## 14. Requirement traceability

Include requirement IDs in test names or metadata:

```text
FR-EXP-003_schematic_semantic_roundtrip
FR-JOB-005_duplicate_delivery_single_publish
FR-ASSET-010_supplied_image_precedes_prompt
NFR-PERF-003_viewer_64_axis
SEC-AUTH_cross_owner_artifact_denied
```

A critical requirement without a test needs an explicit exception and owner in the release checklist.

## 15. MVP release quality conditions

Current local baseline is 33 Python tests plus strict TypeScript/Vite build, independent `nbtlib` parsing, real local CLI/HTTP smoke tests, package checks, and documentation/configuration validation. These prove the local deterministic scope only.

A production release additionally requires:

- zero blocker/critical defects;
- successful supported-input E2E;
- 100% schematic semantic round-trip;
- actual WorldEdit smoke success;
- cross-owner authorization success;
- no OOM at supported resolutions;
- zero browser runtime/page errors;
- resource-leak gate success;
- recorded model/palette/exporter versions and licenses;
- known limitations shown in UI/docs;
- rollback-capable images/artifacts.
