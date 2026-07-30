# 테스트 전략과 품질 게이트

## 1. 품질 원칙

- 테스트는 구현 뒤 부록이 아니라 task 완료 조건이다.
- ML 품질, deterministic geometry, export validity와 서비스 신뢰성을 구분한다.
- 아름다운 preview가 invalid schematic을 통과시키지 못한다.
- metric은 필요조건이며 사람이 보기 좋다는 판단만으로 hard gate를 우회하지 않는다.
- 입력·artifact·review의 hash freshness를 확인한다.
- fail-open 대신 fail-closed를 기본으로 한다.

## 2. 테스트 피라미드

```text
                 Human/Model Quality Eval
             Browser + Minecraft Compatibility E2E
          API/Queue/Worker/Storage Integration
       Contract/Geometry/Voxel/Exporter Unit & Golden
```

### 2.1 Unit

- canonical JSON/hash
- evidence classification
- transform chain/reverse mapping
- sufficiency policy
- state transition
- idempotency hash
- coordinate/scale
- primitive voxelization
- component/morphology
- color distance/palette filter
- RLE/binary codec
- BOM
- schematic primitives/VarInt helper
- error redaction
- retention calculation

### 2.2 Contract

- JSON Schema valid/invalid fixture
- TypeScript/Python fixture parity
- previous schema read compatibility
- unknown enum fail-fast
- API OpenAPI example validation
- binary Python writer↔TypeScript reader

### 2.3 Integration

- API + Postgres
- API + private object storage
- outbox + queue
- queue + worker lease
- stage manifest recovery
- provider fake/timeout
- schematic writer + independent parser
- signed URL owner/expiry
- cleanup/retention

### 2.4 E2E

- upload→conversion→viewer→download
- generated image→conversion
- refresh/SSE reconnect
- cancellation/retry
- invalid upload
- reconstruction failure/fallback
- export validation failure
- cross-owner access
- browser resource lifecycle

### 2.5 Eval

- reconstruction model 비교
- voxel recognizability
- block palette 인상
- hidden surface plausibility
- input challenge별 failure taxonomy

## 3. Fixture 구조

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

모든 외부 fixture manifest:

- source
- license
- checksum
- intended use
- challenge tags
- expected route/gate
- redistribution 여부

큰 binary는 Git LFS 또는 versioned fixture archive를 사용하되 checksum과 fetch 절차를 저장소에 둔다.

## 4. 입력 테스트 matrix

| Fixture | 기대 |
|---|---|
| transparent PNG | alpha 우선, pass |
| EXIF rotated JPEG | canonical orientation |
| WebP | decode/canonicalize |
| extension spoof | reject |
| corrupt/truncated | reject |
| huge dimensions | decode 전/초기 reject |
| animated image | policy reject |
| empty alpha | foreground blocker |
| tiny subject | ask/abort |
| clipped object | route-aware issue |
| multi-subject | warning/ask |
| thin structure | risk warning |
| generated source | design-intent provenance |
| generated as observed | schema failure |

## 5. Reconstruction benchmark

### 5.1 corpus

[06-reconstruction-and-mesh-pipeline.md](06-reconstruction-and-mesh-pipeline.md)의 최소 24개를 사용한다. train/marketing example만 고르지 않고 실패가 예상되는 투명·반사·얇은 구조를 포함한다.

### 5.2 정량 지표

- source view silhouette IoU
- canonical render edge overlap
- component count
- non-manifold/open boundary
- watertight rate
- repair 변화량
- 32/64 voxel silhouette loss
- inference p50/p95
- peak VRAM/RAM
- failure/OOM
- job당 비용

### 5.3 정성 rubric 1~5

- 물체 식별 가능성
- 전체 비율
- source silhouette
- side/back 자연스러움
- 주요 feature
- thin/concave structure
- texture/color
- Minecraft 결과 적합성

model 이름을 숨긴 blind comparison을 우선한다. evaluator 간 불일치를 기록한다.

## 6. Golden test

### 6.1 Mesh→Voxel

AI inference output byte를 golden으로 고정하지 않는다. curated mesh fixture로 다음을 고정한다.

- dimensions
- occupancy/block coordinate
- component count
- palette index
- BOM
- semantic hash
- canonical render metric

algorithm 변경으로 golden이 바뀌면 diff summary, 이유, 기대 개선과 regression 검토가 필요하다.

### 6.2 Voxel codec

- Python encode/decode
- TypeScript decode
- truncated/length overflow
- invalid palette index
- compression bomb limit
- random round-trip/property test

### 6.3 Schematic

- writer output independent parse
- parser output internal model과 semantic compare
- BOM compare
- target version/block validity
- corruption fixture
- deterministic semantic hash

## 7. Property와 fuzz 테스트

대상:

- dimensions/linear index round-trip
- axis rotation 4회 identity
- RLE encode/decode
- palette reindex 의미 보존
- sparse/random occupancy
- NBT/VarInt boundary
- malformed preview header
- arbitrary file name/download header
- state machine illegal transition

fuzz input은 size/time 제한 아래 실행하고 crash artifact를 최소화해 regression fixture로 저장한다.

## 8. Job/복구 테스트

필수:

1. 동일 idempotency key/body → 같은 job
2. 같은 key/다른 body → conflict
3. queue duplicate delivery → lease 하나
4. worker crash after artifact upload before DB commit
5. worker crash after DB candidate before ack
6. stale worker fencing
7. provider timeout/rate limit
8. storage transient error
9. cancel during reconstruction
10. cancel vs complete race
11. retry budget exhaustion
12. completed job 재처리 금지
13. published artifact만 download

각 시나리오는 최종 DB state, object orphan, event와 비용 count를 검증한다.

## 9. Browser 테스트

gpthreejs의 Vite/Playwright preflight, runtime smoke, capture smoke와 dispose 원칙을 확장한다.

필수:

- clean install/typecheck/build
- page console/pageerror 0
- WebGL canvas ready
- 32/64 fixture load
- deterministic canonical capture
- malformed preview error
- WebGL unavailable fallback
- resize/DPR
- 10회 viewer create/load/dispose
- renderer.info geometry/texture 안정
- source/result switch
- keyboard flow
- SSE disconnect/poll fallback

beauty PNG exact hash는 OS/GPU 차이가 있으므로 같은 환경 exact hash, 교차 환경 alpha/semantic/perceptual tolerance를 조합한다.

## 10. 성능 benchmark

### 10.1 Intake

- decode/normalize/matte/depth 시간
- peak memory
- image size별 결과

### 10.2 Reconstruction

- cold/warm load
- inference/repair
- VRAM/RAM
- provider network

### 10.3 Voxel/export

조합:

- 16/32/64/128 experimental
- surface/hollow/solid
- small/large palette
- manifold/non-manifold
- texture/no texture

측정:

- voxelization
- mapping
- preview encode
- schematic export/parse
- output size

### 10.4 Viewer

- fetch/decode/build
- first render
- frame p50/p95
- draw calls/triangles/instances
- GPU memory proxy
- dispose 후 안정성

## 11. 잠정 성능 예산

| 지표 | 초기 목표 |
|---|---|
| 일반 API p95 | 500ms 이하 |
| progress/event 지연 | 2초 이하 |
| 32축 preview decode+build | 다운로드 후 2초 목표 |
| 64축 viewer | 권장 desktop 30FPS 이상 |
| export round-trip | 32축 수 초 이내 |
| 지원 설정 worker OOM | 0 |
| client long task | 반복 100ms 이상 작업 방지 |
| stage manifest overhead | 전체 job 대비 미미한 수준 |

baseline 측정 전 threshold를 release claim으로 사용하지 않는다. CI machine과 production hardware metadata를 함께 기록한다.

## 12. 품질·Delivery gate

### Input

- `GATE-IN-001`: asset validated
- `GATE-IN-002`: provenance/hash valid
- `GATE-IN-003`: route sufficiency not reject

### Reconstruction

- `GATE-REC-001`: output parse/finite/non-empty
- `GATE-REC-002`: canonical coordinate/bounds
- `GATE-REC-003`: route topology capability
- `GATE-REC-004`: license/model provenance

### Voxel

- `GATE-VOX-001`: schema/semantic hash
- `GATE-VOX-002`: dimensions/count
- `GATE-VOX-003`: palette valid
- `GATE-VOX-004`: structural diagnostics policy

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

- `GATE-RUN-001`: web build/browser smoke
- `GATE-RUN-002`: resource dispose
- `GATE-RUN-003`: worker recovery
- `GATE-RUN-004`: authorization

필수 gate가 없거나 stale하면 accept 금지다.

## 13. CI pipeline

PR:

1. formatting/lint
2. Python/TypeScript type check
3. unit/contract
4. schema generation drift
5. frontend/backend build
6. service integration
7. voxel/schematic golden
8. browser E2E fixture provider
9. container build
10. dependency/license/secret scan

Scheduled:

- actual GPU model smoke
- reconstruction benchmark subset/full
- performance regression
- cross-browser
- retention/backup restore
- vulnerability/model checksum

Release candidate:

- staging real provider
- 20+ corpus
- actual WorldEdit compatibility
- load/soak
- rollback rehearsal

## 14. Requirement traceability

테스트 이름/metadata에 요구사항 ID를 포함한다.

```text
FR-EXP-003_schematic_semantic_roundtrip
FR-JOB-005_duplicate_delivery_single_publish
NFR-PERF-003_viewer_64_axis
SEC-AUTH_cross_owner_artifact_denied
```

중요 요구사항에 test가 없으면 release checklist에서 명시적 예외와 owner가 필요하다.

## 15. MVP release 품질 조건

- blocker/critical defect 0
- 지원 input E2E 성공
- schematic semantic round-trip 100%
- 실제 WorldEdit smoke 성공
- cross-owner auth test 성공
- 지원 resolution OOM 없음
- browser runtime/pageerror 0
- resource leak gate 통과
- model/palette/exporter version과 license 기록
- known limitation UI/문서 표시
- rollback 가능 image/artifact 존재
