# 3D Reconstruction and Mesh Pipeline

> [!IMPORTANT]
> The current local MVP implements only deterministic 2.5D relief. Single-image and multi-view mesh routes in this document are production roadmap targets, not current capabilities.

## 1. Goals and realistic limits

The reconstruction stage aims to produce **3D shape and color evidence stable enough for Minecraft voxelization**, not a visually perfect copy. Surfaces hidden in a single image are inferred rather than recovered; provenance and result warnings must say so.

Priorities:

1. subject recognizability and major silhouette;
2. overall proportions and major protrusions/holes;
3. topology suitable for voxelization;
4. stable coordinates, scale, and grounding;
5. surface-color transfer;
6. small details.

## 2. Reconstruction routes

### 2.1 Relief baseline

Uses:

- validate the complete pipeline without external AI;
- inputs whose front view matters most, such as logos, coins, faces, and murals;
- fallback after GPU/provider failure when policy and user intent permit;
- regression baseline.

Process:

1. Determine the foreground domain from the matte.
2. Normalize a depth proxy.
3. Apply edge-aware smoothing.
4. Create a front height field.
5. Create a back plane with minimum base thickness.
6. Connect boundary side walls.
7. Check watertightness.
8. Project the source image onto the front.

Settings:

- depth scale;
- base thickness;
- invert depth;
- smoothing;
- edge emphasis;
- back shape (`flat`/`mirrored`).

Mark the result manifest with `2.5D`, hidden-side policy, and front-view orientation. The current MVP directly builds an equivalent deterministic voxel relief rather than claiming a general reconstructed mesh.

### 2.2 Single-image mesh

This is the intended primary route for a future production MVP. A model/provider returns a raw mesh and, where possible, texture or vertex colors. Normalize vendor output through a common adapter result instead of passing it directly to the voxelizer.

### 2.3 Multi-view mesh

This is a later route. Use only views that pass ReferenceSet consistency gates. Generated multi-view images are all design hypotheses, and model-integrated hidden surfaces remain inferred.

### 2.4 Imported mesh

User GLB/OBJ upload is useful but outside the MVP scope. Design the internal `MeshArtifact` contract so imported meshes can eventually use the same post-processing, voxel, and export path.

## 3. Provider adapter

```python
class ReconstructionProvider(Protocol):
    name: str
    capabilities: ReconstructionCapabilities

    async def reconstruct(
        self,
        request: ReconstructionRequest,
        budget: ComputeBudget,
    ) -> ReconstructionResult: ...
```

Capabilities:

- single image/multi-view;
- alpha support;
- texture/vertex-color/material output;
- seed support;
- cancellation;
- maximum input size;
- output formats;
- required GPU/VRAM;
- hosted/local execution;
- data-retention policy.

Requests use asset IDs/manifests and server-approved model profiles. Clients cannot submit arbitrary local model paths or provider parameters. A hosted adapter would require explicit privacy and egress review; the current repository does not transmit user images externally.

## 4. Model-selection spike

Do not select a model from documentation alone. Candidates may include TRELLIS, Hunyuan3D, TripoSR families, or then-available hosted providers, but verify current licenses and deployment terms before adoption.

### 4.1 Hard gates

- License permits the intended commercial/service use.
- Model-weight use and redistribution terms are acceptable.
- Input-data processing and retention terms are acceptable.
- Runs on Linux/in containers.
- Output can be validated locally.
- Runs on supported hardware or has predictable API cost.

Reject a candidate regardless of quality when any hard gate fails.

### 4.2 Evaluation corpus

At least 24 inputs:

- symmetric hard-surface: 3;
- asymmetric hard-surface: 3;
- organic/animal: 4;
- thin legs/handles/horns: 4;
- deep holes/concavities: 3;
- texture-identifying objects: 3;
- expected transparent/reflective failures: 2;
- service-generated images: 2.

Record origin, license, expected challenge, and observed view for every input.

### 4.3 Measurements

- canonical front silhouette IoU;
- blind score of side/back visual plausibility;
- major-feature retention;
- connected-component count;
- non-manifold edges;
- watertightness;
- volume/bounds change after repair;
- recognizability at 32/64 voxels;
- texture/color transfer;
- p50/p95 latency;
- peak RAM/VRAM;
- cold/warm startup;
- failure/OOM rate;
- cost per job.

### 4.4 Selection method

Weighted scores assist decisions; license, invalid output, and operational feasibility remain hard gates. Select one primary and one fallback, then record the decision in an ADR.

## 5. Model-input preparation

- canonical color space;
- model-required square/padding;
- matte/alpha composition;
- background-color profile;
- input resolution;
- camera/view token;
- seed;
- all transforms.

Provider-specific normalization creates separate model-input artifacts; it never modifies the common canonical asset.

## 6. Raw-output intake

Allowlist containers and formats. Inspect raw output for:

- file size;
- parser success;
- existence of scene/mesh;
- vertex/face-count limits;
- NaN/Infinity;
- texture count, size, and format;
- external URI/path references;
- risky embedded scripts/extensions;
- coordinate metadata.

Prevent OBJ/MTL/GLB external references from escaping the sandbox. Hosted-provider URLs must also use a bounded, allowlisted download path.

## 7. Internal coordinate system

Canonical MVP coordinates:

- right-handed;
- `+X`: right from the user's view;
- `+Y`: up;
- `+Z`: front direction fixed by documentation and fixtures;
- ground plane: `Y=0`;
- object center: horizontal bounding-box center;
- unit: normalized model unit, with maximum extent or height recorded separately.

The model adapter converts source coordinates to canonical coordinates and records the transform matrix. Voxel and export stages must not make independent axis changes.

## 8. Mesh validation

Generate reports for both raw and repaired meshes.

Required checks:

- vertex/face counts and bounds;
- finite coordinates;
- degenerate/zero-area triangles;
- duplicate vertices/faces;
- existence and consistency of normals;
- connected components;
- non-manifold edges/vertices;
- open boundaries/holes;
- possible self-intersection;
- UV ranges and texture presence;
- material count;
- extreme aspect/scale;
- ground penetration.

An empty mesh, non-finite bounds, or excessively large data is a blocker.

## 9. Mesh repair

Version the sequence and parameters:

1. Remove non-finite primitives.
2. Remove degenerate faces.
3. Merge duplicate vertices within tolerance.
4. Normalize face winding and normals.
5. Classify small components.
6. Fill holes conservatively.
7. Diagnose self-intersections/duplicate shells.
8. Optionally remesh or simplify.
9. Align to ground.
10. Normalize scale.

Principles:

- Do not always keep only the largest component; detached ears, handles, or decorations may matter.
- Consider component volume/surface area, distance from the main body, and source-silhouette contribution together.
- Warn or fail when repair substantially changes the source form.
- Never overwrite the raw artifact.
- Record vertex, face, component, bounds, and volume changes before and after repair.

## 10. Watertightness and voxel routes

- Watertight meshes provide the most stable inside/outside test for solids.
- If repair cannot close a mesh, generalized winding or surface voxelization may be used.
- Hollow mode requires a solid occupancy field first.
- When topology cannot satisfy a route, explicitly downgrade to surface mode or ask the user.
- Record downgrade warnings and settings/result differences. Silent mode changes are forbidden.

## 11. Texture and color handoff

Priority:

1. UV + texture;
2. vertex color;
3. material base color;
4. source-view projection;
5. neutral fallback.

Checks:

- UV NaN/out-of-range policy;
- texture orientation/color space;
- missing images;
- alpha and transparency;
- multiple-material assignment;
- percentage of untextured faces.

When projecting from a source, distinguish visible front colors from inferred hidden colors. Select nearest-observed, symmetry, or neutral policy for hidden surfaces and record it in the manifest.

## 12. Simplification and detail budget

A 32-axis target does not need millions of triangles, but pre-voxel simplification can damage the silhouette.

Policy:

- maximum triangle budget based on target resolution;
- silhouette-aware or error-bounded simplification;
- preservation of the raw mesh;
- before/after silhouette comparison in canonical views;
- protection of thin features relative to resolution thresholds;
- retention of detail maps only when needed for block color.

## 13. Compute budget

Stage profile:

- wall/CPU time;
- peak RSS;
- peak VRAM;
- model load time;
- inference time;
- repair time;
- input/output bytes;
- attempts/cache hits.

Budget:

- maximum wall time;
- maximum GPU-memory class;
- maximum output face/texture size;
- maximum retries;
- cancellation checkpoints.

A budget breach returns a clear error and an allowed alternative route instead of destabilizing the process.

## 14. Error classification

- `RECON_PROVIDER_UNAVAILABLE`
- `RECON_PROVIDER_REJECTED`
- `RECON_RATE_LIMITED`
- `RECON_TIMEOUT`
- `RECON_OOM`
- `RECON_INVALID_OUTPUT`
- `MESH_PARSE_FAILED`
- `MESH_EMPTY`
- `MESH_NONFINITE`
- `MESH_TOO_COMPLEX`
- `MESH_REPAIR_FAILED`
- `MESH_NOT_SOLID_CAPABLE`
- `TEXTURE_MISSING`
- `MODEL_LICENSE_BLOCKED`
- `BUDGET_EXHAUSTED`

For each error, separate retryability, public message, remedies, and operator detail.

## 15. Determinism

- AI inference: only limited reproducibility by seed/provider/runtime;
- raw-output intake: deterministic;
- repair/normalization: deterministic for the same version/parameters;
- voxelization onward: deterministic.

If GPU floating-point results differ, use tolerance metrics and canonical renders rather than requiring identical raw-byte hashes. Do not reuse a cache when model/provider version is ambiguous.

## 16. Stage artifacts

```text
model-input image(s)
provider-request manifest
provider-response summary
raw mesh
raw texture(s)
raw validation report
repaired mesh
repair report
canonical transform
canonical renders
reconstruction result manifest
```

Never store secrets, signed URLs, or provider authorization headers in artifacts.

## 17. Completion criteria

- The relief route produces a watertight mesh for fixtures in the target architecture.
- A primary adapter follows the common contract before any AI route is advertised.
- A 24-input corpus benchmark and license report exist.
- Invalid raw meshes never reach the voxelizer.
- Raw/repaired provenance and checksums exist.
- Canonical coordinate/ground fixtures pass.
- Repair output is deterministic for identical input.
- Provider timeout/OOM/unavailable behavior follows retry/fallback policy.
- Surface/solid capability is explicit in the report.
- Current product copy continues to describe only the implemented deterministic 2.5D route until these gates pass.
