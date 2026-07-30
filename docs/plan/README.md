# 3Craft 개발 계획

> 상태: Living plan — local MVP 구현 완료, production roadmap 진행 중
> 기준일: 2026-07-30
> 공개 저장소: [dextune/3craft](https://github.com/dextune/3craft)
> 설계 참고: [dextune/gpthreejs](https://github.com/dextune/gpthreejs) 0.2.0 (MIT)
> 현재 구현·검증 상태: [`../implementation-status.md`](../implementation-status.md)

## 1. 목적

이 디렉터리는 사용자가 업로드한 이미지 또는 서비스가 생성한 이미지를 Minecraft 블록 조형물로 변환하는 **3Craft**의 제품·기술·실행 계획을 정의한다. 구현자는 별도 구두 설명 없이 이 문서 세트에서 범위, 계약, 작업 순서, 품질 관문과 운영 기준을 찾아야 한다.

3Craft의 MVP는 다음 한 문장으로 정의한다.

> 단일 물체 이미지를 받아 입력 증거와 한계를 기록하고, 3D 형상 복원 또는 relief 경로를 거쳐 결정적으로 voxel화하고, Minecraft Java Edition에서 불러올 수 있는 검증된 `.schem`과 브라우저 미리보기 및 블록 수량표를 제공한다.

## 2. 확정한 기본 방향

| 항목 | MVP 기본값 | 비고 |
|---|---|---|
| 결과물 | 월드 배치용 블록 조형물 | 리소스팩/Blockbench 모델은 비범위 |
| Edition | Minecraft Java Edition | Bedrock은 후속 adapter |
| 주 export | Sponge `.schem` v3 계열 | 구현 시 공식 규격과 독립 parser로 검증 |
| 입력 | PNG/JPEG/WebP 업로드, 생성 이미지 | 내부 처리는 canonical PNG/manifest 사용 |
| 피사체 | 배경과 구분되는 단일 물체 | 장면·건축물·복수 물체는 후속 |
| 크기 | 최대 축 16/32/64 | 32 기본, 128은 실험적 backlog |
| 복원 | relief baseline + single-image mesh adapter | multi-view는 확장 경로 |
| voxel 모드 | surface/hollow/solid | 모드별 의미를 계약으로 고정 |
| palette | 안전한 full-cube Java block palette | 중력·block entity·액체 기본 제외 |
| 웹 | React + TypeScript + Vite | gpthreejs Vite 기반을 참고하되 UI는 새로 구성 |
| viewer | React 내부 imperative Three.js | block별 React component 금지, instancing 사용 |
| 서버 | Python API + Python worker | AI/geometry 생태계 및 참고 엔진 패턴 활용 |
| 비동기 처리 | Postgres + Redis queue + S3-compatible storage | 구현체는 ADR로 확정하고 버전 pin |
| 품질 정책 | fail-closed | 필수 artifact/gate 실패 시 다운로드 공개 금지 |

## 3. gpthreejs에서 가져오는 것과 가져오지 않는 것

`gpthreejs`는 photogrammetry 도구가 아니라 참조 증거에서 편집 가능한 procedural `THREE.Group` 코드를 만드는 code-first 파이프라인이다. 3Craft의 결과는 voxel과 schematic이므로 생성 코드를 그대로 재사용하지 않는다. 대신 다음 검증된 설계 패턴을 적응한다.

- `ReferenceSet`과 `observed`/`design-intent`/`design-hypothesis`/`inferred` 증거 구분
- 원본 SHA-256, canonical JSON과 self-field를 제외한 content hash
- 원본을 변경하지 않는 reversible normalization
- matte, edges, depth proxy, palette로 이루어진 Sense Pack
- `pass | conditional | reject` 및 `continue | ask | abort` 충분성 계약
- provider와 compute budget
- 단계별 artifact와 provenance
- 입력 부족, cast 실패, review 실패 시 산출물을 공개하지 않는 fail-closed 정책
- deterministic render/metric과 golden fixture
- 브라우저 runtime/capture smoke 및 resource dispose
- portable delivery bundle과 manifest

다음 요소는 직접 재사용하지 않는다.

- character 전용 Blueprint v2와 anatomy/attachment 규칙
- procedural geometry builder와 `createXxxForm.ts` emitter
- knight demo의 고정 카메라·조명·표면 장식
- Three.js form handle, pivot, socket 계약
- 이미지 증거를 바탕으로 코드를 생성하는 cast 단계

상세 근거는 [01-gpthreejs-analysis.md](01-gpthreejs-analysis.md)를 따른다.

## 4. 문서 지도

| 문서 | 구현 질문 |
|---|---|
| [구현 상태 및 검증 증거](../implementation-status.md) | 현재 코드가 어느 milestone까지 구현·검증되었고 무엇이 남았는가? |
| [01-gpthreejs-analysis.md](01-gpthreejs-analysis.md) | 참고 저장소에서 무엇을 재사용·적응·폐기하는가? |
| [02-product-requirements.md](02-product-requirements.md) | 누구를 위해 무엇을 어디까지 만드는가? |
| [03-system-architecture.md](03-system-architecture.md) | 서비스와 pipeline을 어떤 경계로 나누는가? |
| [04-contracts-and-data-model.md](04-contracts-and-data-model.md) | 단계 간 JSON/binary/DB 계약은 무엇인가? |
| [05-image-intake-generation-sufficiency.md](05-image-intake-generation-sufficiency.md) | 입력·생성 이미지와 충분성을 어떻게 다루는가? |
| [06-reconstruction-and-mesh-pipeline.md](06-reconstruction-and-mesh-pipeline.md) | 이미지에서 voxel화 가능한 mesh를 어떻게 얻는가? |
| [07-voxel-palette-schematic.md](07-voxel-palette-schematic.md) | mesh를 블록과 `.schem`으로 어떻게 바꾸는가? |
| [08-frontend-viewer-ux.md](08-frontend-viewer-ux.md) | 사용 흐름과 Three.js viewer는 어떻게 구현하는가? |
| [09-backend-jobs-storage-security.md](09-backend-jobs-storage-security.md) | API, queue, 저장소, 권한과 실패 복구는 무엇인가? |
| [10-testing-and-quality-gates.md](10-testing-and-quality-gates.md) | 어떤 테스트와 지표가 release를 막는가? |
| [11-roadmap-and-backlog.md](11-roadmap-and-backlog.md) | 어떤 순서와 완료 조건으로 구현하는가? |
| [12-adrs-and-risks.md](12-adrs-and-risks.md) | 핵심 결정, 대안, 위험과 미결정 사항은 무엇인가? |
| [13-operations-and-release.md](13-operations-and-release.md) | 배포, 관측, 장애 대응과 rollback은 어떻게 하는가? |

## 5. 목표 저장소 구조

계획 작성 당시 3Craft는 빈 greenfield 상태였다. 현재는 local vertical slice가 구현되어 있으며 실제 구조와 검증 결과는 [구현 상태 문서](../implementation-status.md)를 따른다. 아래는 production 확장을 포함한 목표 구조다.

```text
3craft/
├── apps/
│   └── web/                       # React + TypeScript + Vite
├── services/
│   ├── api/                       # Python HTTP API
│   └── worker/                    # 비동기 conversion worker
├── packages/
│   ├── contracts/                 # JSON Schema/OpenAPI/generated TS/Python types
│   ├── viewer/                    # imperative Three.js voxel viewer
│   └── minecraft-data/            # versioned palette와 block metadata
├── threecraft/
│   ├── reference/                 # provenance, normalization, sufficiency
│   ├── reconstruction/            # relief/model adapters/mesh repair
│   ├── voxel/                     # occupancy, cleanup, material mapping
│   ├── export/                    # schematic/BOM/preview adapters
│   └── runtime/                   # budget, artifacts, stage manifests
├── tests/
│   ├── fixtures/
│   ├── golden/
│   ├── integration/
│   └── e2e/
├── docs/plan/
└── infra/                         # local compose와 배포 정의
```

초기 vertical slice에서 모노레포 tooling이 개발을 지연시키면 `apps/web`과 단일 Python package만 먼저 만들 수 있다. 다만 계약·artifact·viewer 경계는 위 구조와 호환되게 유지한다.

## 6. 전체 pipeline

```text
intent / uploaded image / generated image
  → SourceAsset + ReferenceSet + provenance
  → decode / canonicalize / reversible normalization
  → Sense Pack (matte, edges, depth proxy, palette, diagnostics)
  → sufficiency gate
      reject/ask → 입력 개선, view 생성 또는 종료
      continue   → reconstruction route 선택
  → relief | single-image mesh | multi-view mesh
  → mesh validation / repair / normalize
  → surface | hollow | solid voxelization
  → Minecraft palette mapping / structural diagnostics
  → deterministic preview render / silhouette and integrity review
  → `.schem` + BOM + preview artifact export
  → semantic round-trip and delivery gates
  → signed download 공개
```

## 7. 문서 규칙

키워드는 RFC 스타일로 사용한다.

- **MUST**: MVP release에 필수다.
- **SHOULD**: 강한 기본값이며 변경 시 근거를 남긴다.
- **MAY**: 선택 또는 후속 범위다.
- **Proposed**: 구현 전 검증이 필요한 결정이다.
- **Accepted**: 팀이 검증·승인한 결정이다.

식별자 접두어:

- `FR`: 기능 요구사항
- `NFR`: 비기능 요구사항
- `CON`: 계약 불변조건
- `GATE`: 품질·delivery 관문
- `SEC`: 보안 요구사항
- `OPS`: 운영 요구사항
- `ADR`: 아키텍처 결정
- `RISK`: 위험

## 8. 구현 시작 관문

본 구현에 들어가기 전에 다음을 완료한다.

1. 3Craft가 block sculpture를 만든다는 제품 정의 승인
2. Java `.schem` target version 하나와 독립 검증 도구 결정
3. reconstruction 후보의 라이선스·VRAM·추론 시간 spike
4. gpthreejs에서 가져올 코드에 MIT attribution과 변경 이력 계획 수립
5. 최소 20개 benchmark fixture의 출처·사용 권한 기록
6. relief 기반 end-to-end 기술 spike
7. target dependency의 정확한 버전 pin과 lockfile 생성
8. 업로드·보존·외부 provider 전송 정책 승인

## 9. 문서와 코드의 우선순위

충돌 시 다음 순서를 따른다.

1. Accepted ADR과 보안 정책
2. 제품 요구사항과 공개 API 계약
3. artifact/schema 불변조건
4. pipeline 및 viewer 세부 계획
5. backlog 추정

의도된 코드 변경이 문서와 다르면 같은 변경 묶음에서 문서를 갱신한다. 알고리즘 output을 바꾸는 변경은 golden fixture 차이와 pipeline version 변경을 요구한다.
