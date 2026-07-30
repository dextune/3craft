# 3Craft Development Plan

> Status: Living plan — local MVP implemented; production roadmap in progress
> Baseline date: 2026-07-30
> Public repository: [dextune/3craft](https://github.com/dextune/3craft)
> Design reference: [dextune/gpthreejs](https://github.com/dextune/gpthreejs) 0.2.0 (MIT)
> Current implementation and validation: [`../implementation-status.md`](../implementation-status.md)

## 1. Purpose

This directory defines the product, technical, and execution plan for **3Craft**, which converts a supplied image—or a generated fallback only when no image exists—into a Minecraft block sculpture. An implementer should be able to discover scope, contracts, work order, quality gates, and operational standards from this document set without separate verbal context.

The MVP is summarized as:

> Accept a single-object image, record evidence and limitations, reconstruct or use a relief route, voxelize deterministically, and provide a validated `.schem` importable into Minecraft Java Edition together with a browser preview and block bill of materials.

The current executable local MVP implements the deterministic 2.5D relief subset. It does not implement real AI image generation or 360° reconstruction.

## 2. Established direction

| Area | MVP default | Notes |
|---|---|---|
| Source precedence | Supplied image first | Generate only when no image bytes exist; invalid supplied input fails closed |
| Result | World-placeable block sculpture | Resource-pack/Blockbench models are out of scope |
| Edition | Minecraft Java Edition | Bedrock is a later adapter |
| Primary export | Sponge `.schem` v3 | Current target: Java 1.20.4, DataVersion 3700 |
| Input | PNG/JPEG/WebP; generated fallback | Internal processing uses canonical PNG/manifests |
| Subject | One object distinct from background | Scenes, buildings, and multiple objects come later |
| Size | Maximum axis 16/32/64 | 32 default; 128 is experimental backlog |
| Reconstruction | Relief baseline + future single-image mesh adapter | Multi-view is an extension route |
| Voxel modes | surface/hollow/solid | Meanings are fixed by contract |
| Palette | Safe full-cube Java block palette | Excludes gravity, block entities, and liquids by default |
| Web | React + TypeScript + Vite | New UI informed by, not copied from, gpthreejs |
| Viewer | Imperative Three.js inside React | No React component per block; use instancing |
| Server | Python API + Python worker | Current worker is process-local; durable production worker is roadmap |
| Production async target | Postgres + Redis queue + S3-compatible storage | Implementation requires an ADR and exact version pins |
| Quality policy | Fail closed | Do not expose downloads after required artifact/gate failure |
| Agent workflow | Root `SKILL.md` | OpenAI/Agent Skills-compatible local build and artifact validation |

## 3. What is and is not adopted from gpthreejs

`gpthreejs` is not photogrammetry software; it is a code-first pipeline that creates editable procedural `THREE.Group` code from reference evidence. 3Craft outputs voxels and schematics, so it does not reuse that generated code directly. It adapts these validated patterns:

- `ReferenceSet` and `observed`/`design-intent`/`design-hypothesis`/`inferred` evidence classes;
- source SHA-256, canonical JSON, and content hashes that exclude self fields;
- reversible normalization that does not alter the source;
- Sense Packs containing matte, edges, depth proxy, and palette;
- `pass | conditional | reject` plus `continue | ask | abort` sufficiency contracts;
- provider and compute budgets;
- stage artifacts and provenance;
- fail-closed behavior after insufficient input, cast failure, or review failure;
- deterministic rendering/metrics and golden fixtures;
- browser runtime/capture smoke tests and resource disposal;
- portable delivery bundles and manifests.

It does not directly reuse:

- character-specific Blueprint v2 anatomy/attachment rules;
- procedural geometry builders or the `createXxxForm.ts` emitter;
- fixed camera, lighting, or decoration from the knight demo;
- Three.js form-handle, pivot, or socket contracts;
- the cast stage that generates source code from image evidence.

See [01-gpthreejs-analysis.md](01-gpthreejs-analysis.md) for detailed rationale.

## 4. Document map

| Document | Implementation question |
|---|---|
| [Implementation status and validation evidence](../implementation-status.md) | Which milestones are implemented and verified now, and what remains? |
| [01-gpthreejs-analysis.md](01-gpthreejs-analysis.md) | What is reused, adapted, referenced, or rejected from the reference repository? |
| [02-product-requirements.md](02-product-requirements.md) | Who is the product for, and what is in scope? |
| [03-system-architecture.md](03-system-architecture.md) | How are service and pipeline boundaries defined? |
| [04-contracts-and-data-model.md](04-contracts-and-data-model.md) | What JSON, binary, and database contracts connect stages? |
| [05-image-intake-generation-sufficiency.md](05-image-intake-generation-sufficiency.md) | How are supplied/generated sources and sufficiency handled? |
| [06-reconstruction-and-mesh-pipeline.md](06-reconstruction-and-mesh-pipeline.md) | How will an image become a mesh suitable for voxelization? |
| [07-voxel-palette-schematic.md](07-voxel-palette-schematic.md) | How does a model become blocks and `.schem`? |
| [08-frontend-viewer-ux.md](08-frontend-viewer-ux.md) | How are the user flow and Three.js viewer implemented? |
| [09-backend-jobs-storage-security.md](09-backend-jobs-storage-security.md) | What are the API, queue, storage, authorization, and recovery contracts? |
| [10-testing-and-quality-gates.md](10-testing-and-quality-gates.md) | Which tests and metrics block release? |
| [11-roadmap-and-backlog.md](11-roadmap-and-backlog.md) | In what order and under which completion criteria is work delivered? |
| [12-adrs-and-risks.md](12-adrs-and-risks.md) | What are the decisions, alternatives, risks, and open questions? |
| [13-operations-and-release.md](13-operations-and-release.md) | How do deployment, observability, incidents, and rollback work? |
| [`../../SKILL.md`](../../SKILL.md) | How does a ChatGPT/OpenAI agent run the safe local image-to-schematic workflow? |

## 5. Target repository structure

3Craft was greenfield when planning began. A local vertical slice now exists; consult the [implementation status](../implementation-status.md) for actual structure and evidence. The target structure including production expansion is:

```text
3craft/
├── apps/
│   └── web/                       # React + TypeScript + Vite
├── services/
│   ├── api/                       # Python HTTP API
│   └── worker/                    # asynchronous conversion worker
├── packages/
│   ├── contracts/                 # JSON Schema/OpenAPI/generated TS/Python types
│   ├── viewer/                    # imperative Three.js voxel viewer
│   └── minecraft-data/            # versioned palette and block metadata
├── threecraft/
│   ├── reference/                 # provenance, normalization, sufficiency
│   ├── reconstruction/            # relief/model adapters/mesh repair
│   ├── voxel/                     # occupancy, cleanup, material mapping
│   ├── export/                    # schematic/BOM/preview adapters
│   └── runtime/                   # budgets, artifacts, stage manifests
├── tests/
│   ├── fixtures/
│   ├── golden/
│   ├── integration/
│   └── e2e/
├── docs/plan/
├── SKILL.md
└── infra/                         # local compose and deployment definitions
```

If monorepo tooling delays the first vertical slice, start with `apps/web` and one Python package. Keep contract, artifact, and viewer boundaries compatible with the target structure.

## 6. Complete pipeline

```text
explicitly supplied PNG/JPEG/WebP, when present
otherwise generated fallback from prompt/default
  → SourceAsset + ReferenceSet + provenance
  → decode / canonicalize / reversible normalization
  → Sense Pack (matte, edges, depth proxy, palette, diagnostics)
  → sufficiency gate
      reject/ask → improve input or stop; never silently generate for invalid supplied bytes
      continue   → select reconstruction route
  → relief | future single-image mesh | future multi-view mesh
  → mesh/model validation / repair / normalization as applicable
  → surface | hollow | solid voxelization
  → Minecraft palette mapping / structural diagnostics
  → deterministic preview render / silhouette and integrity review
  → `.schem` + BOM + preview artifact export
  → semantic round-trip and delivery gates
  → private validated download
```

## 7. Documentation conventions

Keywords use RFC-style meaning:

- **MUST**: required for the applicable MVP release;
- **SHOULD**: strong default requiring rationale to change;
- **MAY**: optional or later scope;
- **Proposed**: decision requiring validation before production adoption;
- **Accepted**: decision validated and approved by the team.

Identifier prefixes:

- `FR`: functional requirement
- `NFR`: non-functional requirement
- `CON`: contract invariant
- `GATE`: quality/delivery gate
- `SEC`: security requirement
- `OPS`: operational requirement
- `ADR`: architecture decision
- `RISK`: risk

## 8. Implementation entry gates

Before beginning production implementation:

1. Approve the product definition as a block-sculpture generator.
2. Select one Java `.schem` target and independent validation tool.
3. Spike reconstruction candidates for license, VRAM, and inference time.
4. Plan MIT attribution and change history for any adopted gpthreejs code.
5. Record origin and usage rights for at least 20 benchmark fixtures.
6. Complete a relief-based end-to-end technical spike.
7. Pin exact target dependency versions and create lockfiles.
8. Approve upload, retention, and external-provider transmission policies.

The local MVP satisfies selected technical entry gates but not the production security, model, infrastructure, and compatibility gates.

## 9. Priority between documents and code

Resolve conflicts in this order:

1. Accepted ADRs and security policy;
2. product requirements and public API contracts;
3. artifact/schema invariants;
4. pipeline and viewer details;
5. backlog estimates.

When intended code behavior differs from the documentation, update both in the same change. A change to algorithmic output requires a golden-fixture diff and pipeline-version review.
