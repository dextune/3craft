# gpthreejs Analysis and 3Craft Adoption Strategy

## 1. Scope and conclusions

This analysis covers [dextune/gpthreejs](https://github.com/dextune/gpthreejs) 0.2.0. It reviewed the repository README, Python engine, Vite/Three.js demo, core playbook, CI, and tests.

Key conclusions:

1. `gpthreejs` is not a photogrammetry product that infers a mesh from an image.
2. Its output is a verifiable TypeScript `THREE.Group` factory, and it emphasizes evidence-based procedural modeling.
3. 3Craft produces voxel models and schematics, so directly reusing the blueprint/cast implementation would create a domain mismatch.
4. Reference provenance, sufficiency, canonical artifacts, budgets, reviews, delivery gates, and runtime-disposal patterns are highly applicable to 3Craft.
5. Therefore, **3Craft adopts contracts and the fail-closed operating model instead of copying the implementation**, and builds new reconstruction, voxel, and Minecraft layers.

## 2. Actual repository structure

```text
gpthreejs/
├── engine/
│   ├── reference/       # ReferenceSet, view, normalization, provider
│   ├── sense/           # matte, edges, depth proxy, palette, sufficiency
│   ├── blueprint/       # hierarchical procedural form specification
│   ├── geometry/        # discriminated geometry kinds and builders
│   ├── cast/            # TypeScript factory emitter and surface maps
│   ├── critique/        # render, metrics, review, iteration
│   ├── orchestration/   # production stage orchestration
│   ├── delivery/        # hard gates and portable bundle
│   ├── runtime/         # compute budget, portability, disposal
│   └── shared/          # PNG, canonical JSON, artifact hashes
├── demo/                # Vite + TypeScript + vanilla Three.js
├── tests/               # unit/integration/golden/production-gate tests
├── playbook/            # sufficiency, fidelity, surface/detail principles
└── docs/planning/       # quality-improvement and delivery plans
```

According to `pyproject.toml`, the Python core supports Python 3.10+ and has no required runtime dependency. The demo uses Vite, TypeScript, Three.js, and Playwright. CI separates Python 3.11/3.12 tests, demo typecheck/build/runtime smoke tests, and wheel-portability checks.

## 3. Pipeline analysis

The README declares this flow:

```text
image or concept
  → Sense Pack / Reference Prep
  → sufficiency gate
  → Intake Brief + Fidelity Pact
  → Feature Ledger
  → Form Blueprint
  → strict validation
  → cast layers
  → deterministic render + orbit views
  → metrics and critique
  → accept | replan | recode | ask | abort
```

The important property is that it does not produce an output unconditionally. It returns `ask` or `abort` for insufficient input and blocks production delivery without required evidence. Likewise, 3Craft must not expose a `.schem` merely because reconstruction executed.

## 4. Detailed analysis by area

### 4.1 ReferenceSet and provenance

`engine/reference/reference_set.py` requires each reference to contain:

- `id`
- `path`
- `assetHash`
- `declaredView`
- `evidenceClass`

Evidence classes are `observed`, `design-intent`, `design-hypothesis`, and `inferred`. Validation prevents generated or edited assets from being promoted to `observed`. It also records file SHA-256 values and a content hash for the complete manifest.

Application to 3Craft:

- A user-uploaded photograph is `observed`.
- A prompt-generated image is `design-intent` and has a distinct `generated` origin.
- Model-generated backs, depth, and meshes are `inferred`.
- Selecting a generated image does not make it an observed photograph.
- Every source, mask, mesh, voxel model, and schematic carries lineage.

### 4.2 Reversible normalization

`engine/reference/normalize.py` creates a new padded PNG and a transform instead of overwriting the original. It records the source hash, canvas, offset, source size, and `reversible=true`, and provides an inverse transform.

Application to 3Craft:

- Record EXIF rotation, crop, padding, resize, alpha generation, and model-specific normalization as a transform chain.
- Distinguish the coordinates seen by the user from model-input coordinates.
- Use the same transform for segmentation edits, silhouette metrics, and preview overlays.
- Retain the original bytes as an immutable source artifact.

### 4.3 Sense Pack

`engine/sense/pack.py` produces a matte, edges, a depth proxy, a palette, and a 3×3 part grid. Quality modes adjust the computation budget.

Application to 3Craft:

- matte: background removal, foreground ratio, and clipping detection;
- edges: diagnosis of thin structures and detail budgets;
- depth proxy: relief baseline, route selection, and quality comparison;
- palette: comparison between Minecraft palette candidates and input colors;
- diagnostics: blur, exposure, transparency/reflection risk, and multiple components.

3Craft defines a new schema version instead of copying the existing Sense Pack format unchanged.

### 4.4 Sufficiency gate

`engine/sense/sufficiency.py` evaluates the image, sense data, brief, ledger, and blueprint, and returns:

- `verdict`: `pass | conditional | reject`;
- `sufficient`;
- `score`;
- `agentAction`: `continue | ask | abort`;
- issues and severities;
- user messages and next steps.

Application to 3Craft:

- File-decode failure or an empty foreground produces `abort`.
- Hidden-side uncertainty from a single image produces `ask` or `conditional`, depending on purpose and quality settings.
- A user who selected relief may continue without a side view.
- High-fidelity mesh or 64-axis requests apply stricter input requirements.
- Store the gate result and any allowed override reason in the job manifest.

### 4.5 Providers and budgets

`engine/reference/provider.py` separates provider protocols from `ProviderBudget`. When no implementation exists, `NullImageProvider` does not invent pixels and returns a clear `ask`. It records generation count, edit count, and wall-time budgets.

Application to 3Craft:

- Define separate provider ports for image generation, segmentation, and reconstruction.
- An unconfigured provider fails with a clear remedy.
- Separate user quota from per-job provider/compute budgets.
- Prevent retries from consuming provider cost without limit.
- Never expose a provider's raw response as the public API contract.

### 4.6 Canonical artifact hashes

`engine/shared/artifacts.py` hashes canonical JSON with sorted keys, compact separators, UTF-8, no NaN, and a trailing newline. It also defines how to omit a self-referential `contentHash`.

Application to 3Craft:

- Use canonical hashes for schema JSON, settings, manifests, and BOMs.
- Use raw-byte SHA-256 for binary artifacts.
- Build cache keys from source hash, contract version, settings, and model/palette version.
- Exclude fields unrelated to output meaning, such as filesystem paths, signed URLs, and timestamps, from semantic hashes.
- Verify deterministic mesh-to-voxel conversion with golden tests.

### 4.7 Blueprint, geometry, and cast

`engine/blueprint` manages character hierarchy, material profiles, attachments, and revisions. `engine/geometry` validates required fields by discriminated geometry kind. `engine/cast` emits a TypeScript factory.

3Craft adoption decision:

- character/anatomy hierarchy: do not use;
- geometry-kind implementation: do not use directly;
- discriminated unions and fail-fast unknown kinds: reuse as patterns;
- strict schemas, explicit migration, and revision hashes: reuse;
- prohibition on silent fallback to a box: apply to voxel/export adapters.

3Craft defines `ReconstructionResult`, `MeshArtifact`, `VoxelModel`, `BlockPalette`, and `SchematicExport` as discriminated contracts.

### 4.8 Rendering, metrics, and critique

`engine/critique` provides deterministic software rendering, silhouette IoU, edge/part metrics, render-set freshness, reviewer policy, and iteration budgets. Metrics are necessary for acceptance, and reviewer judgment cannot bypass a hard failure.

Application to 3Craft:

- Generate canonical front, side, and isometric voxel renders.
- Measure front silhouette IoU against the source matte.
- Compare occupancy and silhouette loss from mesh to voxel.
- Quantify disconnected components, floating blocks, and palette errors.
- Never approve an invalid schematic solely because it has a high aesthetic score.
- Record the best result and regressions across setting retries.

### 4.9 Delivery gates and portable bundles

`engine/delivery/export.py` creates a bundle only after a production run and all hard gates pass. On failure, it leaves a checklist and failure report rather than a successful bundle. Its manifest includes the toolchain, file list, and content hash.

Application to 3Craft:

- Do not expose a download when `.schem` parsing or round-trip validation fails.
- Fail when BOM and schematic block counts differ.
- Fail on invalid block states, dimension mismatches, or missing target versions.
- A successful bundle includes the schematic, BOM, preview, manifest, and warnings.
- Run a leak gate so source images and signed URLs cannot enter the bundle.

### 4.10 Three.js demo and resource lifecycle

`demo/src/app` separates renderer, scene, animation, references, and resources. The renderer caps DPR and configures sRGB and ACES tone mapping. `RuntimeResources` disposes geometry, materials, renderer, and controls. Playwright smoke tests exercise browser runtime and capture.

Application to 3Craft:

- Separate renderer, scene, and viewer lifecycles.
- Release every GPU resource when the canvas unmounts or a job result changes.
- Generate preview regressions with a fixed capture profile.
- Treat WebGL context errors, console errors, and page errors as release gates.
- Use shared geometry and `InstancedMesh`, not one object per block.

## 5. Reuse classification

| gpthreejs area | Classification | 3Craft treatment |
|---|---|---|
| ReferenceSet evidence/provenance | ADAPT | Extend into the 3Craft AssetSet contract |
| SHA-256/canonical JSON | REUSE/ADAPT | Consider the generic utility with MIT attribution |
| Reversible normalization | ADAPT | Add JPEG/WebP/EXIF and transform chains |
| Sense Pack structure | ADAPT | Redesign around voxel-route diagnostics |
| Sufficiency verdict/action | ADAPT | Use 3Craft issue codes and route-specific policies |
| Provider protocol/budget | ADAPT | Add asynchronous API, quota, and cost |
| Compute-stage profile | ADAPT | Add queue/worker metrics and GPU memory |
| Discriminated schema/fail unknown | REUSE AS PATTERN | Apply to mesh/voxel/export contracts |
| Blueprint character hierarchy | DO NOT REUSE | Irrelevant to the voxel domain |
| Geometry builders | REFERENCE | No direct dependency beyond relief prototypes |
| TypeScript factory emitter | DO NOT REUSE | A 3Craft result is not a source factory |
| Deterministic render/metrics | ADAPT | Canonical voxel render and quality metrics |
| Delivery gates/manifest | ADAPT | Center on schematic semantic validation |
| Vite scene/renderer/resources | ADAPT | Rewrite as a React wrapper and instanced viewer |
| Golden/browser/portability tests | REUSE AS PATTERN | Fixtures, builds, browser smoke, bundle consumer |

Classification meanings:

- `REUSE`: code may be reused after license and test review;
- `ADAPT`: change the idea or selected code under a new contract;
- `REFERENCE`: consult only the implementation approach;
- `DO NOT REUSE`: do not import it because the domain differs.

## 6. Gaps that 3Craft must solve

`gpthreejs` does not provide the following, so 3Craft needs new designs:

- production image upload and MIME/security validation;
- a real image-to-mesh AI model adapter;
- a GPU queue and long-running jobs;
- mesh repair, watertightness, and coordinate normalization;
- surface/solid/hollow voxelization;
- version-specific Minecraft block-state palettes;
- color quantization and representative orientation-specific block-texture colors;
- Sponge schematic serialization and semantic round-trip validation;
- multi-user authentication, quotas, and private object storage;
- large voxel browser payloads and instanced rendering;
- BOM, layer views, and Minecraft import UX.

## 7. License and provenance

`gpthreejs` uses the MIT License. If code is copied or modified:

1. Preserve the original LICENSE and copyright notice.
2. Record the source in copied files or change history.
3. Confirm compatibility with 3Craft's own license.
4. Review sample images, Minecraft textures, and model weights under their separate licenses.
5. Record fixture origin, purpose, and distribution permission in a manifest.

Do not confuse rights to MIT engine code with rights to Minecraft assets or AI model weights.

## 8. Final adoption principles

- Never label unseen geometry as `observed`.
- Do not hide quality warnings when input is insufficient.
- Separate reconstruction success from delivery success.
- Every stage has a schema, content hash, input lineage, and version.
- Quality metrics are necessary conditions and cannot offset an invalid export.
- Do not create fake results when a provider or GPU is unavailable.
- Build candidate artifacts first, inspect them, and publish only afterward.
- Prove a vertical slice through pipeline contracts before centering the UI.
