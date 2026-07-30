# Architecture Decisions와 위험 등록부

## 1. ADR 상태

- Proposed: 문서 기본값, 구현 전 승인 필요
- Accepted: spike/evidence와 함께 채택
- Deprecated: 새 사용 금지
- Superseded: 다른 ADR로 대체

Accepted로 변경할 때 날짜, owner, evidence link와 dependency version을 추가한다.

## 2. ADR-001: Block sculpture를 제품 결과로 사용

- 상태: Proposed
- 결정: 월드에 배치 가능한 voxel/block structure를 만든다.
- 대안: resource-pack item/entity, 일반 GLB, procedural Three.js source
- 이유: 이미지→voxel→schematic 가치가 명확하고 Minecraft 사용 흐름과 직접 연결된다.
- 결과: palette, BOM, placement/export가 핵심 도메인이다.
- 재검토: 사용자 조사에서 Blockbench/resource-pack 수요가 우세할 때.

## 3. ADR-002: Java Edition Sponge `.schem` 우선

- 상태: Proposed
- 결정: 첫 delivery는 Java Edition, Sponge v3 계열 `.schem`이다.
- 대안: `.litematic`, Bedrock `.mcstructure`, command function
- 이유: WorldEdit 기반 검증과 배치 흐름이 성숙하다.
- 비용: DataVersion/block state/WorldEdit compatibility 관리.
- 재검토: target 사용자의 Bedrock 비율이 우세하거나 parser 호환성 문제가 치명적일 때.

## 4. ADR-003: Image→Mesh→Voxel pipeline

- 상태: Proposed
- 결정: mesh를 AI와 Minecraft domain 사이 canonical intermediate로 사용한다.
- 대안: direct image→voxel, procedural primitive blueprint, pure depth relief
- 이유: provider 교체, geometry 검사, color transfer와 여러 export에 유리하다.
- 결과: mesh repair와 coordinate 계약이 필요하다.
- 예외: relief는 별도 deterministic route로 유지.
- 재검토: direct voxel 모델이 license/품질/비용에서 명백히 우수할 때.

## 5. ADR-004: Relief를 baseline/fallback으로 유지

- 상태: Proposed
- 결정: 2.5D relief를 MVP의 first vertical slice와 사용자 선택 route로 제공한다.
- 이유: GPU 없이 전체 시스템 검증, 정면 이미지에 적합, provider 장애 fallback.
- 결과: 완전 3D로 오인하지 않도록 UI/manifest 표시.
- 재검토: 제거하지 않고 지원 범위를 축소할 수 있음.

## 6. ADR-005: React/Vite + imperative Three.js

- 상태: Proposed
- 결정: 제품 UI는 React, viewer runtime은 명시적 Three.js lifecycle로 구현한다.
- 대안: vanilla Vite 전체, React Three Fiber, Babylon.js
- 이유: gpthreejs renderer/resource 패턴을 활용하고 대량 instance ownership을 직접 제어한다.
- 결과: React state와 scene state를 분리해야 한다.
- 재검토: R3F spike가 성능·dispose·개발성 모두 우월함을 보일 때.

## 7. ADR-006: Python API와 Python Worker

- 상태: Proposed
- 결정: AI/geometry pipeline과 API를 Python ecosystem에 둔다.
- 대안: TypeScript API + Python worker, 전부 TypeScript
- 이유: gpthreejs Python 패턴, ML/mesh library와 contract 공유.
- 비용: frontend와 타입 생성 필요, API와 GPU worker dependency 분리 필요.
- 재검토: 기존 조직 platform 또는 gpthreejs 통합보다 TypeScript API 이점이 클 때.

## 8. ADR-007: 비동기 durable job

- 상태: Proposed
- 결정: conversion/image generation은 queue job이다.
- 이유: 수십 초~분 단위, timeout/retry/cancel/progress/비용 관리.
- 결과: Postgres state, Redis queue, outbox, worker lease 필요.
- 재검토: 없음. local fixture adapter만 동기 실행 허용.

## 9. ADR-008: S3-compatible private artifact storage

- 상태: Proposed
- 결정: DB에는 metadata, binary는 private object storage.
- 이유: 크기, lifecycle, signed URL, worker/API 분리.
- 결과: owner authorization, orphan cleanup, checksum 필요.
- 재검토: offline desktop-only 제품으로 방향 전환할 때.

## 10. ADR-009: Evidence class와 immutable lineage

- 상태: Proposed
- 결정: gpthreejs의 observed/design-intent/design-hypothesis/inferred 구분과 SHA-256 provenance를 적응한다.
- 이유: 생성 이미지와 hidden geometry의 신뢰 수준을 투명하게 관리.
- 결과: manifest/schema/UI가 evidence class를 전달한다.
- 재검토: 없음. 이름은 schema migration으로 바뀔 수 있다.

## 11. ADR-010: Fail-closed delivery

- 상태: Proposed
- 결정: input/reconstruction/voxel/export hard gate가 모두 통과해야 artifact를 publish한다.
- 대안: warning을 붙여 모든 결과 download
- 이유: invalid schematic, 잘못된 block state, private leak 방지.
- 결과: candidate와 published artifact state 분리.
- 재검토: hard/soft gate 구분은 조정 가능하나 parse/authorization gate는 완화하지 않는다.

## 12. ADR-011: Safe full-cube palette 우선

- 상태: Proposed
- 결정: 불투명 full cube, block entity/중력/액체 제외 palette를 default로 한다.
- 이유: placement와 schematic 의미 안정성.
- 결과: 색 표현 범위가 줄 수 있음.
- 재검토: placement validator와 복합 block 지원 후 profile 확대.

## 13. ADR-012: Canonical semantic hash

- 상태: Proposed
- 결정: canonical JSON과 raw/semantic hash를 분리한다.
- 이유: cache, stale report 방지, deterministic postprocess 검증.
- 결과: hash field/volatile field 제외 규칙을 엄격히 유지.
- 재검토: 새로운 serialization에서도 semantic contract는 유지.

## 14. 미결정 질문

| 질문 | 기본값 | 결정 시점 | 필요한 evidence |
|---|---|---|---|
| API framework | Python ASGI 후보 | M0 | type/schema, 운영성, ecosystem |
| queue library | Redis-backed 후보 | M0 | retry/lease/outbox/모니터링 |
| target MC/DataVersion | 지원 버전 1개 | M0/M1 | parser/WorldEdit smoke |
| primary reconstruction | 미정 | M3 | license+24 corpus benchmark |
| segmentation provider | local/hosted adapter | M2 | mask quality/latency/cost |
| auth | alpha anonymous session | M0 | 제품 배포 방식 |
| source retention | 24h 제안 | M0/M7 | privacy/cost |
| default fill | hollow 또는 surface | M4 | recognizability/block count |
| color metric | perceptual 후보 | M4 | palette benchmark |
| texture-derived palette | 보류 | M4 | license review |
| R3F 사용 | imperative default | viewer spike | 64축/perf/dispose |
| self-hosted GPU | 환경 의존 | M3/M7 | cost/latency/ops |

## 15. 위험 평가

- 확률: Low/Medium/High
- 영향: Low/Medium/High/Critical
- signal: 현실화 조기 지표
- mitigation: 사전 완화
- response: 발생 후 대응

## 16. 위험 등록부

### RISK-001: Single-image hidden surface 부정확

- 확률: High
- 영향: High
- signal: side/back blind score, 재변환/불만
- mitigation: evidence 표시, input guide, relief, multi-view backlog
- response: warning, route 변경, side view 요청
- owner: Product/ML

### RISK-002: 얇은/투명/반사 물체 손실

- 확률: High
- 영향: High
- signal: matte confidence, component 삭제, silhouette loss
- mitigation: diagnostics, minimum thickness, challenge corpus
- response: 64축/다른 image/수동 mask/unsupported 안내
- owner: Vision/Geometry

### RISK-003: Reconstruction model 라이선스 불가

- 확률: Medium
- 영향: Critical
- signal: 비상업/weight/API data 제한
- mitigation: hard license gate, 후보 복수
- response: 후보 교체, relief만 제한 제공
- owner: Tech/Product

### RISK-004: GPU 비용·queue 지연

- 확률: Medium
- 영향: Critical
- signal: GPU seconds, oldest age, cancellation, cost/job
- mitigation: 32 default, quota, benchmark, admission, cache
- response: 64 제한, provider/모델 변경, capacity scale
- owner: Platform

### RISK-005: Invalid/non-manifold mesh

- 확률: High
- 영향: High
- signal: repair failure, solid route failure
- mitigation: raw validation, surface fallback, mesh corpus
- response: downgrade with consent, relief, model 변경
- owner: Geometry

### RISK-006: Schematic 좌표/format 호환 오류

- 확률: Medium
- 영향: Critical
- signal: parser/WorldEdit 실패, BOM mismatch
- mitigation: M1 primitive export, independent parser, actual smoke
- response: exporter rollback/disable, artifact unpublish
- owner: Export

### RISK-007: Minecraft palette 자산 라이선스

- 확률: Medium
- 영향: High
- signal: texture 재배포/derived data 불명확
- mitigation: curated values, source/license record, legal review
- response: texture 없는 manual palette로 전환
- owner: Product

### RISK-008: Viewer memory/FPS

- 확률: Medium
- 영향: High
- signal: 64축 frame p95, context loss, resource growth
- mitigation: instancing, interior skip, worker decode, dispose gate
- response: exposed-face/greedy mesh, resolution/device fallback
- owner: Frontend

### RISK-009: Queue 중복 실행/중복 비용

- 확률: Medium
- 영향: High
- signal: 같은 job 동시 attempt/provider call
- mitigation: lease/fencing/idempotent stage/provider correlation
- response: stale attempt 차단, 비용 audit, retry 조정
- owner: Backend

### RISK-010: 사용자 asset 노출

- 확률: Low
- 영향: Critical
- signal: IDOR/public bucket/signed URL leak
- mitigation: private storage, owner scope, security test
- response: access revoke, key rotation, incident/삭제/통지 정책
- owner: Security

### RISK-011: Provider outage/data retention 변경

- 확률: Medium
- 영향: High
- signal: error/rate spike, policy notice
- mitigation: adapter/null/fallback, circuit breaker, policy inventory
- response: provider disable/교체, 기능별 상태 공지
- owner: Platform

### RISK-012: Artifact/schema drift

- 확률: Medium
- 영향: High
- signal: old job read failure, TS/Python mismatch
- mitigation: schema source, generated types, previous fixture CI
- response: compatibility reader/migration, rollout 중단
- owner: Architecture

### RISK-013: gpthreejs code의 잘못된 직접 복사

- 확률: Medium
- 영향: Medium
- signal: character/THREE.Group 계약이 voxel core에 침투
- mitigation: [01-gpthreejs-analysis.md](01-gpthreejs-analysis.md) 분류와 review
- response: adapter boundary로 refactor, 불필요 코드 제거
- owner: Tech Lead

### RISK-014: 자동 repair가 identity를 훼손

- 확률: Medium
- 영향: High
- signal: repair 전후 silhouette/volume 급변
- mitigation: change threshold/raw 보존/canonical comparison
- response: 덜 공격적 repair, surface route, ask
- owner: Geometry

### RISK-015: Scope creep

- 확률: High
- 영향: High
- signal: Bedrock/mod/gallery/editor가 MVP critical path에 포함
- mitigation: [02-product-requirements.md](02-product-requirements.md) 비범위와 P1/P2
- response: backlog로 이동, vertical slice 우선
- owner: Product

## 17. Decision review cadence

- M0: ADR-001/002/005/006/007/008
- M1: axis, schema, exporter target, hash
- M3: primary model/provider
- M4: default fill/palette/color
- M7: auth/retention/deployment/cost
- Beta: 성능 예산과 support matrix

결정은 benchmark·test·운영 증거 없이 “익숙하다”는 이유만으로 Accepted로 바꾸지 않는다.
