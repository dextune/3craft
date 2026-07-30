# 계약과 데이터 모델

## 1. 계약 설계 원칙

1. 모든 장기 보존 artifact는 `schemaVersion`을 가진다.
2. ID는 외부에 노출 가능한 opaque string을 사용한다.
3. 파일 path나 signed URL을 domain identity로 사용하지 않는다.
4. source, generated, edited, inferred를 구분한다.
5. JSON은 canonical serialization 후 semantic hash를 만든다.
6. binary는 raw SHA-256와 별도 manifest를 가진다.
7. 날짜는 UTC ISO-8601, 크기는 byte, 시간은 명시 단위로 저장한다.
8. NaN/Infinity를 JSON에 허용하지 않는다.
9. unknown enum을 조용히 기본값으로 바꾸지 않는다.
10. schema 변경은 migration 또는 새 version을 요구한다.

이 문서의 예시는 최종 JSON Schema가 아니라 구현 계약의 기준이다. Milestone 0에서 `packages/contracts`에 machine-readable schema를 작성한다.

## 2. ID와 naming

권장 prefix:

- `ast_`: asset
- `ref_`: reference entry
- `job_`: job
- `att_`: attempt
- `art_`: artifact
- `pal_`: palette
- `usr_`: user
- `ses_`: anonymous session

storage key에는 사용자 입력 파일명, 이메일, prompt를 사용하지 않는다.

```text
tenants/{ownerId}/jobs/{jobId}/artifacts/{artifactId}/{safeName}
```

DB와 log는 ID를 사용하고 실제 storage key는 접근 제한 필드로 취급한다.

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

- `observed`: 사용자가 제공한 실제 관찰 source
- `design-intent`: 생성 또는 합성된 목표 이미지
- `design-hypothesis`: 사용자가 승인하지 않은 후보 view/shape
- `inferred`: 모델/알고리즘이 추정한 depth, mask, hidden geometry

`origin=generated|edited`인 asset은 `observed`가 될 수 없다. 사용자 승인 여부와 증거의 실제 출처를 혼동하지 않는다.

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

불변조건:

- reference는 최소 1개다.
- ID는 set 안에서 unique다.
- `assetHash`는 asset manifest와 일치한다.
- primary는 정확히 하나다.
- generated view를 observed로 승격하지 않는다.
- `contentHash` 계산 시 자신과 volatile storage location을 제외한다.

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

원본 좌표로 돌아갈 수 없는 operation은 이유를 명시한다. mask와 overlay는 같은 chain을 참조한다.

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

metric 정의와 threshold는 policy version에 묶는다.

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

`reject/abort`는 override할 수 없다. `conditional/ask` override 여부는 policy가 route별로 결정한다.

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

- max-axis는 allowlist 값만 허용한다.
- shell thickness는 grid에 유효한 범위다.
- strategy와 required capability가 맞아야 한다.
- target version과 palette compatibility를 검증한다.
- server policy가 허용하지 않는 model/provider name을 client가 지정할 수 없다.

## 9. Job과 Attempt

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

Attempt는 다음을 별도 기록한다.

- attempt number
- lease owner/expiry
- heartbeat
- started/ended time
- stage cursor
- retry cause
- provider usage
- CPU/RSS/GPU memory/wall time
- public error와 operator diagnostic reference

## 10. PipelineManifest와 StageRecord

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

재시도 시 input hash, stage version, settings hash와 output checksum이 모두 일치해야 재사용한다.

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

## 12. ReconstructionResult와 MeshMetadata

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

repair report는 제거/변경한 face, component, hole, normal과 volume 변화를 기록한다. raw와 repaired mesh hash를 둘 다 보존한다.

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

semantic hash에는 압축 방식과 상관없이 dimensions, canonical palette와 좌표별 block state 의미를 사용한다.

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

block state 문자열은 target version에서 유효해야 한다. palette data 출처와 라이선스를 기록한다.

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

manifest에는 내부 path, signed URL, secret, 사용자 email과 원본 prompt 전체를 포함하지 않는다.

## 16. Job Event와 오류

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

오류:

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

public payload에 stack trace, provider raw body, file path와 key를 넣지 않는다.

## 17. Canonical hash 규칙

JSON canonicalization 제안:

- UTF-8
- key lexical sort
- compact separator
- Unicode를 의미 그대로 유지
- NaN/Infinity 금지
- 끝 newline
- hash field 자체와 승인된 volatile field 제외

binary:

- byte-level SHA-256
- semantic hash는 decoder가 해석한 canonical 의미에 대해 별도 계산

cache key 예시:

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

- additive optional field: 같은 major에서 허용 가능
- required field/meaning 변경: 새 schema version
- enum rename: migration 또는 dual-read 기간
- binary encoding 변경: `encoding` version 변경
- old artifact는 immutable, 읽기 adapter로 지원
- migration은 원본을 덮어쓰지 않고 새 artifact와 lineage를 만든다.

CI는 current writer→current reader, previous fixture→current reader, round-trip semantic equality를 검사한다.
