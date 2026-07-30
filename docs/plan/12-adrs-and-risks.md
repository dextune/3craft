# Architecture Decisions and Risk Register

## 1. ADR status

- Proposed: documented default that requires approval before production adoption
- Accepted: adopted with spike/test evidence
- Deprecated: prohibited for new use
- Superseded: replaced by another ADR

When changing an ADR to Accepted, add date, owner, evidence links, and dependency versions. Several Proposed decisions below are already local-MVP implementation defaults but still require broader production evidence described in their review conditions.

## 2. ADR-001: Use a block sculpture as the product result

- Status: Proposed
- Decision: Create a voxel/block structure placeable in a world.
- Alternatives: resource-pack item/entity, generic GLB, procedural Three.js source
- Rationale: The image → voxel → schematic value is clear and directly connected to Minecraft workflows.
- Consequence: Palette, BOM, placement, and export become core domains.
- Revisit: If user research strongly favors Blockbench/resource-pack output.

## 3. ADR-002: Java Edition Sponge `.schem` first

- Status: Proposed for production support; implemented for the local MVP
- Decision: The first delivery format is Java Edition Sponge v3 `.schem`.
- Alternatives: `.litematic`, Bedrock `.mcstructure`, command functions
- Rationale: WorldEdit-based validation and placement workflows are mature.
- Cost: Manage DataVersion, block states, and WorldEdit compatibility.
- Revisit: If target users strongly favor Bedrock or parser compatibility becomes untenable.

## 4. ADR-003: Image → mesh → voxel pipeline

- Status: Proposed
- Decision: Use a mesh as the canonical intermediate between AI and the Minecraft domain.
- Alternatives: direct image → voxel, procedural primitive blueprint, pure depth relief
- Rationale: Supports provider replacement, geometry inspection, color transfer, and multiple exports.
- Consequence: Requires mesh repair and coordinate contracts.
- Exception: Keep relief as a separate deterministic route. The current local MVP uses this exception directly.
- Revisit: If a direct voxel model is clearly superior in license, quality, and cost.

## 5. ADR-004: Keep relief as baseline/fallback

- Status: Proposed for production; implemented as the current local route
- Decision: Provide 2.5D relief as the first vertical slice and a user-selectable route.
- Rationale: Validates the complete system without a GPU, suits front-view images, and can remain available during provider outages.
- Consequence: UI and manifests must prevent users from mistaking it for complete 3D.
- Revisit: Scope may shrink, but the deterministic baseline remains useful.

## 6. ADR-005: React/Vite plus imperative Three.js

- Status: Proposed for production; implemented in the local viewer
- Decision: Build product UI in React and viewer runtime with an explicit Three.js lifecycle.
- Alternatives: all-vanilla Vite, React Three Fiber, Babylon.js
- Rationale: Adapts gpthreejs renderer/resource patterns and directly controls ownership of many instances.
- Consequence: React state and scene state must remain separate.
- Revisit: If an R3F spike is superior in performance, disposal, and developer experience.

## 7. ADR-006: Python API and Python worker

- Status: Proposed for production; implemented process-locally
- Decision: Keep the AI/geometry pipeline and API in the Python ecosystem.
- Alternatives: TypeScript API + Python worker, all TypeScript
- Rationale: Matches gpthreejs Python patterns and ML/mesh libraries while sharing contracts.
- Cost: Generate/synchronize frontend types and isolate API versus GPU-worker dependencies.
- Revisit: If an organizational platform or TypeScript API offers greater benefit than integration.

## 8. ADR-007: Asynchronous durable jobs

- Status: Proposed; asynchronous shape implemented, durability not implemented
- Decision: Conversion and production image generation are queued jobs.
- Rationale: They can take seconds or minutes and need timeout, retry, cancel, progress, and cost controls.
- Consequence: Production requires Postgres state, Redis queue, outbox, and worker leases.
- Revisit: None. Only local fixture adapters may execute synchronously.

## 9. ADR-008: S3-compatible private artifact storage

- Status: Proposed
- Decision: Store metadata in the database and binaries in private object storage.
- Rationale: Supports size, lifecycle, signed URLs, and API/worker separation.
- Consequence: Requires owner authorization, orphan cleanup, and checksums.
- Revisit: If the product becomes offline-desktop only.

The local MVP instead uses a private filesystem store with restrictive permissions and opaque validated IDs.

## 10. ADR-009: Evidence classes and immutable lineage

- Status: Proposed for production; core invariant implemented
- Decision: Adapt gpthreejs `observed`, `design-intent`, `design-hypothesis`, and `inferred` classes with SHA-256 provenance.
- Rationale: Transparently manages trust in generated images and hidden geometry.
- Consequence: Manifests, schemas, and UI carry evidence classes.
- Revisit: The names may change only through schema migration; the distinction remains.

## 11. ADR-010: Fail-closed delivery

- Status: Proposed for production; core gates implemented
- Decision: Publish artifacts only after input, reconstruction, voxel, and export hard gates pass.
- Alternative: Attach warnings and allow every result to download.
- Rationale: Prevent invalid schematics, invalid block states, and private-data leakage.
- Consequence: Separate candidate and published artifact states in production.
- Revisit: Hard/soft classification can change, but parse and authorization gates cannot be weakened.

## 12. ADR-011: Safe full-cube palette first

- Status: Proposed for production; `java-safe-v1` implemented
- Decision: Default to opaque full cubes excluding block entities, gravity blocks, and liquids.
- Rationale: Stable placement and schematic meaning.
- Consequence: Reduced color range.
- Revisit: Expand profiles after placement validation and compound-block support.

## 13. ADR-012: Canonical semantic hashes

- Status: Proposed for production; implemented in core contracts
- Decision: Separate canonical JSON, raw-byte hashes, and semantic hashes.
- Rationale: Reliable caches, stale-report prevention, and deterministic post-processing checks.
- Consequence: Strictly maintain exclusions for hash fields and volatile fields.
- Revisit: Preserve the semantic contract under any new serialization.

## 14. ADR-013: Supplied image is authoritative

- Status: Accepted
- Date: 2026-07-30
- Owner: 3Craft core
- Decision: Non-`None` supplied image bytes always select upload processing. Generate only when image bytes are absent.
- Invariant: `None` means absent; `b""` means a supplied invalid image.
- Provenance: upload=`observed`; generated fallback=`design-intent`.
- Alternatives: prompt overrides attachment, automatic generation after upload failure, separate ambiguous UI tabs
- Rationale: Preserves user intent, provenance, privacy, and fail-closed validation.
- Consequence: A user must explicitly remove or replace an invalid supplied image before generation can run.
- Evidence: `tests/test_pipeline.py`, `tests/test_api.py`, `tests/test_cli.py`, unified Web source form, `SKILL.md`
- Revisit: Do not weaken precedence. New source kinds require an explicit versioned decision.

## 15. Open questions

| Question | Default | Decision point | Required evidence |
|---|---|---|---|
| API framework | Python ASGI candidate | M0 | Types/schemas, operations, ecosystem |
| Queue library | Redis-backed candidate | M0 | Retry/lease/outbox/monitoring |
| Target MC/DataVersion | One supported version | M0/M1 | Parser/WorldEdit smoke |
| Primary reconstruction | Undecided | M3 | License + 24-input benchmark |
| Segmentation provider | Local/hosted adapter | M2 | Mask quality/latency/cost |
| Authentication | Anonymous alpha session | M0 | Product deployment model |
| Source retention | Proposed 24 h | M0/M7 | Privacy/cost |
| Default fill | Hollow or surface | M4 | Recognizability/block count |
| Color metric | Perceptual candidate | M4 | Palette benchmark |
| Texture-derived palette | Deferred | M4 | License review |
| R3F use | Imperative default | Viewer spike | 64-axis performance/disposal |
| Self-hosted GPU | Environment-dependent | M3/M7 | Cost/latency/operations |

The executable local target is currently fixed to Java 1.20.4, DataVersion 3700, Sponge v3, hollow default, and the imperative viewer; production support claims still require their stated evidence.

## 16. Risk assessment

- Probability: Low/Medium/High
- Impact: Low/Medium/High/Critical
- Signal: Early indication that the risk is becoming real
- Mitigation: Preventive action
- Response: Action after occurrence

## 17. Risk register

### RISK-001: Inaccurate hidden surfaces from one image

- Probability: High
- Impact: High
- Signal: side/back blind score, reconversion, complaints
- Mitigation: evidence labels, input guide, relief, multi-view backlog
- Response: warning, route change, request side view
- Owner: Product/ML

### RISK-002: Loss of thin, transparent, or reflective objects

- Probability: High
- Impact: High
- Signal: matte confidence, component removal, silhouette loss
- Mitigation: diagnostics, minimum thickness, challenge corpus
- Response: 64-axis suggestion, different image, manual mask, unsupported notice
- Owner: Vision/Geometry

### RISK-003: Reconstruction-model license is unusable

- Probability: Medium
- Impact: Critical
- Signal: non-commercial terms or weight/API-data restrictions
- Mitigation: hard license gate, multiple candidates
- Response: replace candidate or limit service to relief
- Owner: Technology/Product

### RISK-004: GPU cost or queue delay

- Probability: Medium
- Impact: Critical
- Signal: GPU-seconds, oldest age, cancellation, cost/job
- Mitigation: default 32, quotas, benchmark, admission control, cache
- Response: restrict 64, change provider/model, scale capacity
- Owner: Platform

### RISK-005: Invalid/non-manifold mesh

- Probability: High
- Impact: High
- Signal: repair failure, solid-route failure
- Mitigation: raw validation, surface fallback, mesh corpus
- Response: downgrade with consent, relief, model change
- Owner: Geometry

### RISK-006: Schematic coordinate/format incompatibility

- Probability: Medium
- Impact: Critical
- Signal: parser/WorldEdit failure, BOM mismatch
- Mitigation: M1 primitive export, independent parser, actual smoke
- Response: roll back/disable exporter, unpublish affected artifacts
- Owner: Export

### RISK-007: Minecraft palette-asset licensing

- Probability: Medium
- Impact: High
- Signal: unclear texture redistribution/derived-data rights
- Mitigation: curated values, source/license records, legal review
- Response: switch to a texture-free manual palette
- Owner: Product

### RISK-008: Viewer memory/FPS

- Probability: Medium
- Impact: High
- Signal: 64-axis frame p95, context loss, resource growth
- Mitigation: instancing, interior skipping, worker decode, disposal gate
- Response: exposed-face/greedy mesh, resolution/device fallback
- Owner: Frontend

### RISK-009: Duplicate queue execution/cost

- Probability: Medium
- Impact: High
- Signal: simultaneous attempts/provider calls for one job
- Mitigation: leases, fencing, idempotent stages, provider correlation
- Response: stop stale attempt, audit cost, adjust retry
- Owner: Backend

### RISK-010: User-asset exposure

- Probability: Low
- Impact: Critical
- Signal: IDOR, public bucket, leaked signed URL
- Mitigation: private storage, owner scope, security tests
- Response: revoke access, rotate keys, apply incident/deletion/notification policy
- Owner: Security

### RISK-011: Provider outage or retention-policy change

- Probability: Medium
- Impact: High
- Signal: error/rate spike, policy notice
- Mitigation: adapters, null mode, allowed fallback, circuit breaker, policy inventory
- Response: disable/replace provider, capability-specific status notice
- Owner: Platform

### RISK-012: Artifact/schema drift

- Probability: Medium
- Impact: High
- Signal: old-job read failure, TypeScript/Python mismatch
- Mitigation: schema source, generated types, previous-fixture CI
- Response: compatibility reader/migration, stop rollout
- Owner: Architecture

### RISK-013: Incorrect direct copying from gpthreejs

- Probability: Medium
- Impact: Medium
- Signal: character/`THREE.Group` contracts enter voxel core
- Mitigation: classification and review in [01-gpthreejs-analysis.md](01-gpthreejs-analysis.md)
- Response: refactor behind adapters and remove irrelevant code
- Owner: Technology Lead

### RISK-014: Automatic repair damages identity

- Probability: Medium
- Impact: High
- Signal: sharp silhouette/volume changes before versus after repair
- Mitigation: change thresholds, raw preservation, canonical comparison
- Response: less aggressive repair, surface route, ask
- Owner: Geometry

### RISK-015: Scope creep

- Probability: High
- Impact: High
- Signal: Bedrock/mod/gallery/editor work enters the MVP critical path
- Mitigation: non-goals in [02-product-requirements.md](02-product-requirements.md) and P1/P2 backlog
- Response: move to backlog and prioritize the vertical slice
- Owner: Product

### RISK-016: Silent fallback replaces a supplied image

- Probability: Low after ADR-013 controls
- Impact: Critical
- Signal: generated origin after a request containing file bytes; provider called after upload validation error
- Mitigation: one resolver contract, explicit `None` semantics, provider spies, API/CLI/Web regression tests, skill instructions
- Response: disable affected source path, preserve failing request evidence without user content, patch and add a regression fixture
- Owner: Core/API

## 18. Decision review cadence

- M0: ADR-001/002/005/006/007/008
- M1: axes, schemas, exporter target, hashes
- M2: ADR-013 and source/provenance policy
- M3: primary model/provider
- M4: default fill/palette/color
- M7: authentication/retention/deployment/cost
- Beta: performance budgets and support matrix

Never mark a decision Accepted merely because it is familiar; require benchmark, test, and operational evidence.
