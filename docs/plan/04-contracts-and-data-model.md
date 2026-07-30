# Contracts and Data Model

## 1. Contract design principles

1. Every long-lived artifact has a `schemaVersion`.
2. IDs are opaque strings safe for external exposure.
3. File paths and signed URLs are not domain identities.
4. Distinguish source, generated, edited, and inferred data.
5. Compute semantic hashes from canonical JSON serialization.
6. Binary data has a raw SHA-256 and a separate manifest.
7. Store dates as UTC ISO-8601, sizes in bytes, and durations with explicit units.
8. Do not permit NaN or Infinity in JSON.
9. Never silently convert an unknown enum to a default.
10. Schema changes require a migration or a new version.

Examples in this document define implementation contracts; they are not final JSON Schemas. Milestone 0 creates machine-readable schemas under `packages/contracts`.

## 2. IDs and naming

Recommended prefixes:

- `ast_`: asset
- `ref_`: reference entry
- `job_`: job
- `att_`: attempt
- `art_`: artifact
- `pal_`: palette
- `usr_`: user
- `ses_`: anonymous session

Do not put user-supplied filenames, email addresses, or prompts in storage keys.

```text
tenants/{ownerId}/jobs/{jobId}/artifacts/{artifactId}/{safeName}
```

Databases and logs use IDs; the actual storage key is access-restricted.

## 3. EvidenceAsset

```json
{
  "schemaVersion": 1,
  "assetId": "ast_...",
  "kind": "image",
  "origin": "upload",
  "evidenceClass": "observed",
  "contentType": "image/png",
  "byteSize": 123456,
  "sha256": "...",
  "width": 1024,
  "height": 1024,
  "frames": 1,
  "colorSpace": "srgb",
  "createdAt": "2026-07-30T00:00:00Z",
  "provenance": {
    "originalFileName": "display-only.png",
    "provider": null,
    "model": null,
    "seed": null,
    "parentAssetIds": []
  }
}
```

### 3.1 origin

- `upload`
- `generated`
- `edited`
- `derived`
- `fixture`

### 3.2 evidenceClass

- `observed`: an actual observed source supplied by the user
- `design-intent`: a generated or composited target image
- `design-hypothesis`: a candidate view or shape not approved by the user
- `inferred`: depth, masks, or hidden geometry estimated by a model/algorithm

`origin=generated|edited` assets cannot be `observed`. User approval does not change the actual source of evidence.

Source-resolution invariants:

- Non-`None` image bytes select upload processing even when a prompt also exists.
- `None` means no image; empty bytes mean an invalid supplied image.
- Generation is permitted only for the `None` case.
- Upload provenance is `origin=upload`, `evidenceClass=observed`.
- Generated fallback provenance is `origin=generated`, `evidenceClass=design-intent`.

## 4. ReferenceSet

```json
{
  "schemaVersion": 1,
  "id": "refset_...",
  "subjectType": "single-object",
  "references": [
    {
      "id": "ref_front",
      "assetId": "ast_...",
      "assetHash": "...",
      "declaredView": "source",
      "detectedView": "source-34",
      "evidenceClass": "observed",
      "origin": "upload",
      "visibleFeatures": ["handle", "front-emblem"],
      "primary": true
    }
  ],
  "contentHash": "..."
}
```

Invariants:

- A set has at least one reference.
- IDs are unique within the set.
- `assetHash` matches the asset manifest.
- Exactly one reference is primary.
- Never promote a generated view to observed.
- Exclude the hash itself and volatile storage locations from `contentHash`.

## 5. TransformChain

```json
{
  "schemaVersion": 1,
  "sourceAssetId": "ast_source",
  "outputAssetId": "ast_canonical",
  "operations": [
    {
      "type": "exif-orient",
      "inputSize": [3024, 4032],
      "outputSize": [4032, 3024],
      "parameters": {"orientation": 6},
      "reversible": true
    },
    {
      "type": "pad",
      "inputSize": [1000, 800],
      "outputSize": [1024, 1024],
      "offset": [12, 112],
      "parameters": {"background": [255, 255, 255, 0]},
      "reversible": true
    },
    {
      "type": "resize",
      "inputSize": [1024, 1024],
      "outputSize": [512, 512],
      "parameters": {"filter": "configured"},
      "reversible": false
    }
  ]
}
```

An operation that cannot return to source coordinates records the reason. Masks and overlays reference the same chain.

## 6. SensePack

```json
{
  "schemaVersion": 1,
  "sourceAssetId": "ast_canonical",
  "mode": "standard",
  "artifacts": {
    "matte": "art_...",
    "edges": "art_...",
    "depthProxy": "art_...",
    "palette": "art_..."
  },
  "diagnostics": {
    "foregroundRatio": 0.62,
    "foregroundBounds": [0.12, 0.08, 0.76, 0.88],
    "touchesFrame": false,
    "componentCount": 1,
    "matteConfidence": 0.91,
    "blurScore": 0.14,
    "exposure": "ok",
    "thinStructureRisk": "medium",
    "transparentMaterialRisk": "low"
  },
  "contentHash": "..."
}
```

Metric definitions and thresholds are bound to a policy version.

## 7. SufficiencyReport

```json
{
  "schemaVersion": 1,
  "policyVersion": "sufficiency-v1",
  "route": "single-image-mesh",
  "verdict": "conditional",
  "sufficient": true,
  "agentAction": "continue",
  "score": 0.74,
  "issues": [
    {
      "code": "HIDDEN_SURFACE_INFERRED",
      "severity": "warning",
      "messageKey": "sufficiency.hiddenSurfaceInferred",
      "evidence": {"viewCount": 1},
      "remedies": ["add-side-view", "use-relief"]
    }
  ],
  "override": null,
  "inputHashes": ["..."],
  "contentHash": "..."
}
```

severity:

- `info`
- `warning`
- `error`
- `blocker`

`reject/abort` cannot be overridden. Policy determines by route whether `conditional/ask` may be overridden.

## 8. ConversionRequest

```json
{
  "schemaVersion": 1,
  "sourceReferenceSetId": "refset_...",
  "strategy": "single-image-mesh",
  "resolution": {"mode": "max-axis", "value": 32},
  "fill": {"mode": "hollow", "shellThickness": 1, "fillerBlock": null},
  "palette": {
    "profileId": "safe-basic",
    "version": "java-safe-v1",
    "allowTransparent": false,
    "allowGravity": false,
    "allowBlockEntities": false,
    "deny": []
  },
  "color": {"metric": "configured-perceptual", "dithering": "off"},
  "orientation": {"rotateYQuarterTurns": 0, "ground": true},
  "target": {"edition": "java", "minecraftVersion": "configured-supported-version"}
}
```

request validation:

- `max-axis` accepts only allowlisted values.
- Shell thickness is valid for the grid.
- Strategy and required capability must agree.
- Validate target-version and palette compatibility.
- Clients cannot select model/provider names disallowed by server policy.

## 9. Job and Attempt

```json
{
  "schemaVersion": 1,
  "jobId": "job_...",
  "kind": "conversion",
  "status": "voxelizing",
  "stage": "voxelizing",
  "progress": 68,
  "requestHash": "...",
  "pipelineVersion": "pipeline-v1",
  "activeAttemptId": "att_...",
  "createdAt": "...",
  "updatedAt": "...",
  "terminal": false
}
```

An Attempt separately records:

- attempt number
- lease owner/expiry
- heartbeat
- started/ended time
- stage cursor
- retry cause
- provider usage
- CPU/RSS/GPU memory/wall time
- public error and operator diagnostic reference

## 10. PipelineManifest and StageRecord

```json
{
  "schemaVersion": 1,
  "jobId": "job_...",
  "attemptId": "att_...",
  "pipelineVersion": "pipeline-v1",
  "stages": [
    {
      "name": "voxelize",
      "version": "voxelizer-v1",
      "status": "completed",
      "inputArtifactIds": ["art_mesh"],
      "inputHashes": ["..."],
      "outputArtifactIds": ["art_voxel"],
      "settingsHash": "...",
      "startedAt": "...",
      "endedAt": "...",
      "profile": {
        "wallSeconds": 1.82,
        "cpuSeconds": 4.31,
        "peakRssBytes": 123456789,
        "peakGpuBytes": null
      },
      "warnings": []
    }
  ],
  "contentHash": "..."
}
```

A retry reuses output only when input hashes, stage version, settings hash, and output checksum all match.

## 11. ArtifactManifest

```json
{
  "schemaVersion": 1,
  "artifactId": "art_...",
  "jobId": "job_...",
  "kind": "voxel-model",
  "state": "candidate",
  "contentType": "application/x-3craft-voxel",
  "byteSize": 45678,
  "sha256": "...",
  "semanticHash": "...",
  "producer": {"stage": "voxelize", "version": "voxelizer-v1"},
  "parents": ["art_mesh"],
  "metadata": {},
  "createdAt": "...",
  "expiresAt": "..."
}
```

state:

- `writing`
- `candidate`
- `validated`
- `published`
- `expired`
- `deleted`

## 12. ReconstructionResult and MeshMetadata

```json
{
  "schemaVersion": 1,
  "strategy": "single-image-mesh",
  "provider": "configured-provider",
  "model": "configured-model-version",
  "seed": 42,
  "rawMeshArtifactId": "art_raw_mesh",
  "textureArtifactIds": ["art_texture"],
  "coordinateSystem": {
    "handedness": "right",
    "upAxis": "+Y",
    "frontAxis": "+Z",
    "unit": "model-unit"
  },
  "stats": {
    "vertices": 12000,
    "faces": 23000,
    "components": 2,
    "watertight": false,
    "bounds": [[-1, 0, -0.4], [1, 2.3, 0.5]]
  },
  "warnings": []
}
```

The repair report records removed or changed faces, components, holes, normals, and volume changes. Preserve both raw and repaired mesh hashes.

## 13. VoxelModel

```json
{
  "schemaVersion": 1,
  "dimensions": {"width": 32, "height": 28, "length": 20},
  "axis": {"x": "right", "y": "up", "z": "front"},
  "origin": [0, 0, 0],
  "occupancyEncoding": "rle-v1",
  "paletteVersion": "java-safe-v1",
  "palette": ["minecraft:air", "minecraft:stone"],
  "dataArtifactId": "art_voxel_bin",
  "mode": "hollow",
  "statistics": {
    "occupied": 4500,
    "surface": 4200,
    "components": 1,
    "floating": 0,
    "groundContact": 34
  },
  "semanticHash": "..."
}
```

The semantic hash uses dimensions, a canonical palette, and coordinate-to-block-state meaning independently of compression.

## 14. BlockPalette

```json
{
  "schemaVersion": 1,
  "id": "safe-basic",
  "version": "java-safe-v1",
  "edition": "java",
  "minecraftVersions": ["configured-range"],
  "entries": [
    {
      "blockState": "minecraft:stone",
      "colors": {"top": [125,125,125], "side": [125,125,125], "bottom": [125,125,125]},
      "tags": ["opaque", "full-cube", "safe"],
      "gravity": false,
      "transparent": false,
      "blockEntity": false,
      "enabledByDefault": true
    }
  ],
  "source": {"method": "curated", "licenseNote": "documented-separately"},
  "contentHash": "..."
}
```

Every block-state string must be valid in the target version. Record palette-data origin and license.

## 15. DeliveryManifest

```json
{
  "schemaVersion": 1,
  "jobId": "job_...",
  "status": "passed",
  "target": {"edition": "java", "minecraftVersion": "...", "dataVersion": 0},
  "pipeline": {
    "version": "pipeline-v1",
    "reconstructionModel": "...",
    "voxelizer": "voxelizer-v1",
    "palette": "java-safe-v1",
    "exporter": "sponge-v3-v1"
  },
  "artifacts": {
    "schematic": {"id": "art_...", "sha256": "..."},
    "bomJson": {"id": "art_...", "sha256": "..."},
    "preview": {"id": "art_...", "sha256": "..."}
  },
  "gates": [{"id": "GATE-EXP-ROUNDTRIP", "passed": true}],
  "warnings": ["hidden surfaces inferred"],
  "contentHash": "..."
}
```

The manifest excludes internal paths, signed URLs, secrets, user email addresses, and complete original prompts.

## 16. Job Event and errors

```json
{
  "eventId": "evt_...",
  "jobId": "job_...",
  "type": "stage_changed",
  "stage": "voxelizing",
  "progress": 65,
  "occurredAt": "...",
  "publicPayload": {"messageKey": "job.voxelizing"}
}
```

Error:

```json
{
  "code": "RECONSTRUCTION_OOM",
  "messageKey": "errors.reconstructionOom",
  "retryable": true,
  "remedies": ["retry-later", "use-relief", "lower-resolution"],
  "requestId": "req_...",
  "operatorReference": "err_..."
}
```

Public payloads exclude stack traces, provider raw bodies, file paths, and keys.

## 17. Canonical hash rules

Proposed JSON canonicalization:

- UTF-8
- key lexical sort
- compact separator
- preserve Unicode semantically
- forbid NaN/Infinity
- trailing newline
- exclude the hash field itself and approved volatile fields

binary:

- byte-level SHA-256
- calculate a separate semantic hash over the canonical meaning interpreted by the decoder

Example cache key:

```text
sha256(
  sourceSemanticHash
  + strategyVersion
  + canonicalSettingsHash
  + modelIdentifier
  + paletteContentHash
  + targetVersion
)
```

## 18. Schema migration

- additive optional field: may be allowed within the same major version
- required field or meaning change: new schema version
- enum rename: migration or dual-read period
- binary encoding change: change the `encoding` version
- old artifacts remain immutable and are supported through read adapters
- a migration creates a new artifact and lineage instead of overwriting the source

CI checks current writer → current reader, previous fixture → current reader, and round-trip semantic equality.
