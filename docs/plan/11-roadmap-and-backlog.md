# 구현 로드맵과 백로그

> 현재 milestone별 구현 상태와 concrete evidence는 [`../implementation-status.md`](../implementation-status.md)를 따른다. 이 문서는 남은 production roadmap까지 포함한다.

## 1. 계획 원칙

- 먼저 end-to-end 얇은 vertical slice를 만든다.
- UI 완성보다 schematic round-trip을 먼저 증명한다.
- 실제 reconstruction model을 기다리지 않고 fixture/fake adapter로 병렬 개발한다.
- 불확실성이 큰 model, Minecraft format, viewer 성능을 초기에 spike한다.
- 각 milestone은 test evidence와 gate가 있어야 완료된다.
- 추정은 person-day 범위이며 일정 약속이 아니다.

가정:

- full-stack/graphics 1명
- ML/geometry 1명
- infra/QA part-time 지원
- 2명이 병렬 작업할 때 MVP 7~11주 예상
- 실제 provider/license/VRAM 결과에 따라 변동

## 2. M0: Bootstrap과 결정 관문

예상: 3~5 person-days

### 작업

- `BOOT-001`: monorepo/디렉터리 skeleton
- `BOOT-002`: Node/Python runtime pin
- `BOOT-003`: exact dependencies와 lockfile
- `BOOT-004`: lint/type/test/build scripts
- `BOOT-005`: local Postgres/Redis/S3-compatible 환경
- `BOOT-006`: contract package와 schema CI
- `BOOT-007`: MIT attribution과 third-party inventory
- `DEC-001`: target Minecraft/WorldEdit/DataVersion
- `DEC-002`: API framework/queue implementation
- `DEC-003`: anonymous/auth alpha 정책
- `DEC-004`: source/artifact retention 기본값

### 완료 조건

- clean checkout에서 install/test/build
- local services health
- web→API hello contract
- Python/TS schema fixture parity
- [12-adrs-and-risks.md](12-adrs-and-risks.md)의 핵심 ADR Accepted

## 3. M1: Deterministic vertical slice

예상: 6~9 person-days

목표:

```text
fixture PNG → provenance/sense → relief mesh → 32 voxel → stone/safe palette → `.schem` → parser → viewer
```

### Pipeline

- `REF-001`: EvidenceAsset/ReferenceSet
- `REF-002`: canonical JSON/hash
- `REF-003`: PNG/JPEG/WebP decode/normalize
- `REF-004`: alpha/heuristic matte
- `REF-005`: minimal SensePack
- `REL-001`: depth/height relief mesh
- `MESH-001`: canonical coordinates/primitive validation
- `VOX-001`: surface occupancy
- `PAL-001`: minimal curated palette
- `EXP-001`: one-block and primitive schematic writer
- `EXP-002`: independent parser round-trip

### Web/backend

- `API-001`: local direct asset adapter
- `API-002`: fixture conversion command/job skeleton
- `VIEW-001`: viewer runtime/instanced block
- `VIEW-002`: binary/JSON debug preview

### 완료 조건

- one command/test로 deterministic slice 실행
- one block/asymmetric axis fixture round-trip
- browser에서 fixture 표시
- 동일 input semantic hash
- 외부 AI/GPU 불필요

## 4. M2: Production intake와 sufficiency

예상: 6~9 person-days

- `ASSET-001`: upload session/signed upload
- `ASSET-002`: server signature/decode/pixel limit
- `ASSET-003`: canonical re-encode/EXIF/color
- `ASSET-004`: private storage/owner
- `SENSE-001`: segmentation adapter
- `SENSE-002`: matte confidence/edges/depth/palette
- `SENSE-003`: transform chain/reverse mapping
- `SUF-001`: route-aware issue policy
- `SUF-002`: pass/conditional/reject action
- `SUF-003`: user message/remedy
- `GEN-001`: image provider port/null adapter
- `GEN-002`: generated provenance
- `SEC-001`: malformed/adversarial upload fixture

완료 조건:

- upload/generated asset가 같은 contract
- generated를 observed로 표시할 수 없음
- blocker가 production queue 생성 차단
- original/canonical/derived lineage
- UI matte/sufficiency review

## 5. M3: Reconstruction model 선정

예상: 8~13 person-days

### 조사/spike

- `ML-001`: 후보 license/data policy
- `ML-002`: common adapter/capability
- `ML-003`: candidate A
- `ML-004`: candidate B
- `ML-005`: 필요 시 hosted candidate
- `ML-006`: 24개 corpus benchmark
- `ML-007`: VRAM/latency/cost/failure
- `ML-008`: blind quality evaluation
- `ML-009`: primary/fallback ADR

### Mesh

- `MESH-002`: raw ingest sandbox
- `MESH-003`: finite/degenerate/component report
- `MESH-004`: normal/hole/repair
- `MESH-005`: coordinate/ground normalize
- `MESH-006`: texture/color handoff
- `MESH-007`: simplification benchmark

완료 조건:

- hard license gate 통과
- selected model/profile version 고정
- invalid output이 downstream 차단
- raw/repaired artifact와 report
- primary/fallback/relief 정책

## 6. M4: Voxel, palette와 export core

예상: 10~15 person-days

- `VOX-002`: solid occupancy
- `VOX-003`: hollow/shell
- `VOX-004`: component/morphology/thin feature
- `VOX-005`: deterministic semantic hash
- `COL-001`: UV/vertex/material color sample
- `PAL-002`: safe-basic versioned data
- `PAL-003`: target block validator
- `PAL-004`: perceptual mapper
- `PAL-005`: regularization/dithering
- `BOM-001`: JSON/CSV
- `CODEC-001`: production voxel binary/RLE
- `CODEC-002`: TS decoder golden
- `EXP-003`: full Sponge v3 adapter
- `EXP-004`: BOM/coordinate semantic validation
- `EXP-005`: delivery bundle/leak gate
- `EXP-006`: actual WorldEdit smoke matrix

완료 조건:

- 16/32/64 surface/hollow/solid fixture
- safe palette target validation
- Python/TS codec parity
- all export gates
- 실제 WorldEdit import

## 7. M5: Durable jobs와 backend

예상: 8~12 person-days

- `DB-001`: owner/assets/reference/jobs/attempts/artifacts/events
- `DB-002`: migration/test fixtures
- `JOB-001`: state machine
- `JOB-002`: idempotency/request hash
- `JOB-003`: outbox/queue publish
- `JOB-004`: lease/heartbeat/fencing
- `JOB-005`: stage manifest/reuse
- `JOB-006`: retry/backoff/dead letter
- `JOB-007`: cancellation/race
- `API-003`: job/SSE/polling
- `API-004`: artifact download authorization
- `STORE-001`: candidate/validated/published
- `STORE-002`: retention/delete
- `OBS-001`: logs/metrics/traces

완료 조건:

- duplicate queue에서 single execution/publish
- worker kill recovery
- cancel/complete race
- owner scope
- candidate download 불가
- retention test

## 8. M6: Product UI와 viewer

예상: 8~12 person-days

- `WEB-001`: app shell/routes/design token
- `WEB-002`: upload/generate source
- `WEB-003`: mask/sufficiency
- `WEB-004`: settings/validation
- `WEB-005`: job progress/SSE/poll
- `WEB-006`: error/retry/cancel
- `WEB-007`: result/BOM/download
- `VIEW-003`: production binary/Web Worker
- `VIEW-004`: palette instancing
- `VIEW-005`: camera/grid/orientation
- `VIEW-006`: layer clipping/selection
- `VIEW-007`: canonical capture
- `VIEW-008`: dispose/leak probe
- `A11Y-001`: keyboard/text alternative

완료 조건:

- upload와 generate E2E
- refresh/reconnect
- 64축 performance
- repeated dispose
- keyboard core flow
- WebGL fallback

## 9. M7: Security, operations와 staging

예상: 6~10 person-days

- `SEC-002`: auth/session/CSRF/CORS
- `SEC-003`: IDOR/owner integration
- `SEC-004`: rate/quota/admission
- `SEC-005`: worker sandbox/egress/resource
- `SEC-006`: secret/dependency/model scan
- `OPS-001`: production containers
- `OPS-002`: staging topology
- `OPS-003`: dashboard/alerts
- `OPS-004`: backup/restore
- `OPS-005`: provider circuit breaker
- `OPS-006`: cost telemetry
- `OPS-007`: release/rollback rehearsal

완료 조건:

- [13-operations-and-release.md](13-operations-and-release.md) smoke
- security critical 0
- alerts 실제 test
- restore와 rollback evidence
- quota/cost protection

## 10. M8: Beta hardening

예상: 7~12 person-days

- `QA-001`: full fixture/golden regression
- `QA-002`: reconstruction benchmark rerun
- `QA-003`: browser compatibility
- `QA-004`: Minecraft/WorldEdit matrix
- `QA-005`: load/soak
- `QA-006`: provider outage/OOM/storage incident drill
- `QA-007`: UX copy/known limitation
- `QA-008`: privacy/retention UI
- `QA-009`: release candidate
- `QA-010`: canary/rollback

완료 조건은 [10-testing-and-quality-gates.md](10-testing-and-quality-gates.md)의 MVP release 조건 전체다.

## 11. 병렬화

### Track A: Contract/Backend

M0 → M1 contract → asset/job/storage → operations

### Track B: Geometry/ML

fixture → relief → model benchmark → mesh → voxel/palette/export

### Track C: Web/Viewer

gpthreejs viewer pattern 분석 → fixture viewer → create/job UI → production viewer

동기화 지점:

- M1 VoxelModel/preview contract
- M2 ReferenceSet/SufficiencyReport
- M3 ReconstructionResult/MeshMetadata
- M4 DeliveryManifest
- M5 JobEvent/API

contract fixture가 merge되기 전 양쪽에서 임시 shape를 만들지 않는다.

## 12. Critical path

```text
Target schematic 결정
→ primitive export round-trip
→ VoxelModel/axis 고정
→ reconstruction adapter/mesh normalize
→ color/palette
→ durable job
→ product E2E
→ staging/compatibility
```

Minecraft export를 마지막에 미루면 coordinate/palette 설계를 다시 해야 한다. M1에 최소 exporter를 넣는 이유다.

## 13. MVP P0/P1/P2 backlog

### P0

- source/upload/generated provenance
- sufficiency fail-closed
- relief + primary reconstruction
- 16/32/64
- surface/hollow/solid
- safe palette
- viewer/BOM
- Java `.schem` round-trip
- private storage/job recovery
- security/release gate

### P1

- generated multi-view
- custom mask editor
- color-rich/natural/survival profiles
- advanced layer viewer
- GLB/imported mesh
- result library/auth
- `.litematic`

### P2

- Bedrock `.mcstructure`
- custom/mod palette
- build order/instructions
- block replacement editor
- public gallery/share
- batch/public API
- direct server/world integration

## 14. Definition of Ready

- 요구사항/위험/owner
- 입력·출력 계약
- dependency와 선행 task
- test와 acceptance
- security/privacy/cost 영향
- feature flag/rollback 필요 여부
- fixture 준비

## 15. Definition of Done

- code review
- unit/contract/integration test
- lint/type/build
- failure/cancel/loading 처리
- telemetry
- secret/user content 검토
- docs/schema 갱신
- migration/compatibility
- acceptance evidence
- rollback 또는 safe disable

## 16. 첫 2주 실행안

### 1~2일

- M0 skeleton/runtime/dependency pin
- target `.schem`/DataVersion 결정
- contract schema와 CI

### 3~5일

- canonical hash/ReferenceSet
- primitive mesh/VoxelModel
- one-block/asymmetric schematic round-trip

### 6~7일

- relief mesh
- 32축 surface voxel
- safe palette subset/BOM

### 8~10일

- fixture job/API
- React page + instanced viewer
- browser smoke
- first end-to-end demo

2주 목표는 화려한 UI가 아니라 검증된 schematic과 재현 가능한 vertical slice다.
