# gpthreejs 분석과 3Craft 적용 전략

## 1. 분석 범위와 결론

분석 대상은 [dextune/gpthreejs](https://github.com/dextune/gpthreejs) 0.2.0이다. 저장소의 README, Python engine, Vite/Three.js demo, 핵심 playbook, CI와 테스트를 확인했다.

핵심 결론은 다음과 같다.

1. `gpthreejs`는 이미지에서 mesh를 추론하는 photogrammetry 제품이 아니다.
2. 결과물은 검증 가능한 TypeScript `THREE.Group` factory이며, 증거 기반의 절차적 모델링을 강조한다.
3. 3Craft는 voxel model과 schematic을 만들기 때문에 blueprint/cast 구현을 직접 재사용하면 도메인 불일치가 생긴다.
4. 반면 reference provenance, 충분성, canonical artifact, budget, review, delivery gate와 runtime dispose 패턴은 3Craft에 매우 적합하다.
5. 따라서 **코드 복제보다 계약과 fail-closed 운영 모델을 이식**하고, reconstruction·voxel·Minecraft 계층은 새로 구현한다.

## 2. 실제 저장소 구조

```text
gpthreejs/
├── engine/
│   ├── reference/       # ReferenceSet, view, normalization, provider
│   ├── sense/           # matte, edges, depth proxy, palette, sufficiency
│   ├── blueprint/       # 계층형 procedural form specification
│   ├── geometry/        # discriminated geometry kinds와 builders
│   ├── cast/            # TypeScript factory emitter와 surface maps
│   ├── critique/        # render, metrics, review, iteration
│   ├── orchestration/   # production stage orchestration
│   ├── delivery/        # hard gates와 portable bundle
│   ├── runtime/         # compute budget, portability, dispose
│   └── shared/          # PNG, canonical JSON, artifact hash
├── demo/                # Vite + TypeScript + vanilla Three.js
├── tests/               # unit/integration/golden/production gate tests
├── playbook/            # sufficiency, fidelity, surface/detail 원칙
└── docs/planning/       # 품질 향상과 delivery 계획
```

Python core는 `pyproject.toml` 기준 Python 3.10+이며 필수 runtime dependency가 없다. demo는 Vite, TypeScript, Three.js와 Playwright를 사용한다. CI는 Python 3.11/3.12 테스트, demo typecheck/build/runtime smoke, wheel portability를 분리한다.

## 3. 파이프라인 분석

README에 선언된 흐름은 다음과 같다.

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

이 흐름의 중요한 특성은 “무조건 결과를 생성”하지 않는다는 점이다. 입력이 불충분하면 `ask` 또는 `abort`하고, 필수 증거가 없으면 production delivery를 차단한다. 3Craft도 reconstruction이 실행됐다는 이유만으로 `.schem`을 공개해서는 안 된다.

## 4. 영역별 상세 분석

### 4.1 ReferenceSet과 provenance

`engine/reference/reference_set.py`는 각 reference에 다음 필드를 요구한다.

- `id`
- `path`
- `assetHash`
- `declaredView`
- `evidenceClass`

증거 분류는 `observed`, `design-intent`, `design-hypothesis`, `inferred`다. 생성되거나 편집된 asset을 `observed`로 승격시키는 것을 validation 오류로 막는다. 파일 SHA-256과 전체 manifest content hash도 기록한다.

3Craft 적용:

- 사용자 업로드 사진은 `observed`다.
- 프롬프트 생성 이미지는 `design-intent` 또는 별도 `generated` origin을 가진다.
- 모델이 만든 뒷면·depth·mesh는 `inferred`다.
- 사용자가 생성 이미지를 선택했더라도 실제 관찰 사진으로 표시하지 않는다.
- 모든 source, mask, mesh, voxel, schematic에 lineage를 연결한다.

### 4.2 Reversible normalization

`engine/reference/normalize.py`는 원본을 덮어쓰지 않고 padding한 새 PNG와 transform을 만든다. source hash, canvas, offset, source size와 `reversible=true`를 기록하고 역변환 함수도 제공한다.

3Craft 적용:

- EXIF 회전, crop, pad, resize, alpha 생성과 model-specific normalization을 transform chain으로 기록한다.
- 사용자가 본 원본 좌표와 model input 좌표를 구분한다.
- segmentation 수정, silhouette metric과 preview overlay가 같은 transform을 사용한다.
- 원본 byte는 immutable source artifact로 유지한다.

### 4.3 Sense Pack

`engine/sense/pack.py`는 matte, edge, depth proxy, palette와 3×3 part grid를 생성한다. quality mode에 따라 계산량을 조절한다.

3Craft 적용:

- matte: 배경 제거, foreground 비율과 clipping 판정
- edges: 얇은 구조 및 detail budget 진단
- depth proxy: relief baseline, 복원 경로 선택과 품질 비교
- palette: Minecraft palette 후보와 입력 색상 분포 비교
- diagnostics: blur, exposure, 투명/반사 위험, 다중 component

3Craft Sense Pack은 기존 형식을 그대로 복사하지 않고 schema version을 새로 정의한다.

### 4.4 Sufficiency gate

`engine/sense/sufficiency.py`는 image, sense, brief, ledger, blueprint를 검사하고 다음을 반환한다.

- `verdict`: `pass | conditional | reject`
- `sufficient`
- `score`
- `agentAction`: `continue | ask | abort`
- issue 목록과 severity
- 사용자 메시지와 next steps

3Craft 적용:

- 파일 decode 실패나 foreground 없음은 `abort`
- 단일 이미지의 hidden side 불확실성은 목적과 품질 설정에 따라 `ask` 또는 `conditional`
- relief를 선택한 사용자는 side view가 없어도 계속할 수 있음
- high-fidelity mesh 또는 64축 요청은 더 엄격한 입력 조건 적용
- gate 결과와 override 이유를 job manifest에 저장

### 4.5 Provider와 budget

`engine/reference/provider.py`는 provider protocol과 `ProviderBudget`을 분리한다. 구현이 없을 때 `NullImageProvider`가 픽셀을 지어내지 않고 명확히 `ask`한다. 생성 횟수, 편집 횟수와 wall time 예산도 기록한다.

3Craft 적용:

- image generation, segmentation, reconstruction을 각각 provider port로 정의
- 미설정 provider는 요청을 실패시키되 명확한 remedy 제공
- 사용자별 quota와 job별 provider/compute budget 분리
- retry가 provider 비용을 무제한 소비하지 않게 함
- provider raw response를 외부 API 계약으로 사용하지 않음

### 4.6 Canonical artifact hash

`engine/shared/artifacts.py`는 정렬된 key, compact separator, UTF-8, no-NaN, trailing newline의 canonical JSON을 SHA-256으로 hash한다. self-referential `contentHash`를 제외하는 규칙도 있다.

3Craft 적용:

- schema JSON, settings, manifest, BOM에 canonical hash 사용
- binary artifact는 raw byte SHA-256 사용
- cache key는 source hash + contract version + settings + model/palette version으로 구성
- filesystem path, signed URL, timestamp처럼 output 의미와 무관한 field는 semantic hash에서 제외
- 동일 mesh→voxel 변환의 결정성을 golden test로 검증

### 4.7 Blueprint, geometry와 cast

`engine/blueprint`는 character hierarchy, material profile, attachment와 revision을 관리하고, `engine/geometry`는 geometry kind별 필수 field를 discriminated schema로 검증한다. `engine/cast`는 TypeScript factory를 emit한다.

3Craft 적용 판단:

- character/anatomy 구조: 사용하지 않음
- geometry kind 구현: 직접 사용하지 않음
- discriminated union과 unknown kind fail-fast 원칙: 재사용
- strict schema, 명시적 migration, revision hash: 재사용
- silent fallback to box 금지 원칙: voxel/export adapter에 적용

3Craft에서는 `ReconstructionResult`, `MeshArtifact`, `VoxelModel`, `BlockPalette`, `SchematicExport`를 discriminated contract로 정의한다.

### 4.8 Render, metric과 critique

`engine/critique`는 deterministic software render, silhouette IoU, edge/part metric, render set freshness, reviewer policy와 iteration budget을 제공한다. metric이 accept의 필요조건이고 reviewer 판단만으로 hard fail을 우회할 수 없다.

3Craft 적용:

- canonical front/side/isometric voxel render 생성
- source matte와 front silhouette IoU 측정
- mesh와 voxel의 occupancy/silhouette 손실 비교
- disconnected component, floating block, palette error를 정량화
- 높은 미적 점수만으로 invalid schematic을 승인하지 않음
- 설정 재시도 시 best result와 regression 기록

### 4.9 Delivery gate와 portable bundle

`engine/delivery/export.py`는 production run을 거치고 hard gate가 모두 통과해야 bundle을 만든다. 실패 시 checklist와 failure report를 남기고 성공 bundle을 만들지 않는다. manifest에는 toolchain, file list와 content hash가 포함된다.

3Craft 적용:

- `.schem` parse/round-trip 실패 시 download artifact를 공개하지 않음
- BOM count와 schematic count 불일치 시 실패
- invalid block state, dimensions mismatch, target version 누락 시 실패
- 성공 bundle은 schematic, BOM, preview, manifest, warnings를 포함
- 내부 source image나 signed URL이 bundle에 섞이지 않도록 leak gate 수행

### 4.10 Three.js demo와 resource lifecycle

`demo/src/app`은 renderer, scene, animation, references, resources를 분리한다. renderer는 DPR 상한, sRGB와 ACES tone mapping을 설정하고, `RuntimeResources`가 geometry/material/renderer/controls를 dispose한다. Playwright smoke는 browser runtime과 capture를 검증한다.

3Craft 적용:

- renderer/scene/viewer lifecycle 분리
- canvas가 unmount되거나 job 결과가 바뀔 때 모든 GPU resource 해제
- fixed capture profile로 preview regression 생성
- WebGL context, console error와 page error를 release gate로 사용
- block별 object가 아니라 shared geometry와 `InstancedMesh` 사용

## 5. 재사용 분류표

| gpthreejs 영역 | 분류 | 3Craft 처리 |
|---|---|---|
| ReferenceSet evidence/provenance | ADAPT | 3Craft AssetSet 계약으로 확장 |
| SHA-256/canonical JSON | REUSE/ADAPT | MIT attribution 후 generic utility 검토 |
| reversible normalization | ADAPT | JPEG/WebP/EXIF와 transform chain 추가 |
| Sense Pack 구조 | ADAPT | voxel route 진단 중심으로 재설계 |
| sufficiency verdict/action | ADAPT | 3Craft issue code와 route별 policy |
| provider protocol/budget | ADAPT | async API, quota, cost 포함 |
| compute stage profile | ADAPT | queue/worker metric과 GPU memory 추가 |
| discriminated schema/fail unknown | REUSE AS PATTERN | mesh/voxel/export contract에 적용 |
| blueprint character hierarchy | DO NOT REUSE | voxel domain과 무관 |
| geometry builders | REFERENCE | relief prototype 외 직접 종속 금지 |
| TypeScript factory emitter | DO NOT REUSE | 3Craft 결과가 source factory가 아님 |
| deterministic render/metric | ADAPT | voxel canonical render와 quality metric |
| delivery gates/manifest | ADAPT | schematic semantic validation 중심 |
| Vite scene/renderer/resources | ADAPT | React wrapper와 instanced viewer로 재작성 |
| golden/browser/portability tests | REUSE AS PATTERN | fixture, build, browser smoke, bundle consumer |

분류 의미:

- `REUSE`: 라이선스와 테스트 확인 후 코드 재사용 가능
- `ADAPT`: 아이디어/일부 코드를 새 계약 아래 변경
- `REFERENCE`: 구현 방식만 참고
- `DO NOT REUSE`: 도메인이 달라 가져오지 않음

## 6. 3Craft가 새로 해결해야 하는 gap

`gpthreejs`에는 다음이 없으므로 신규 설계가 필요하다.

- production 이미지 upload와 MIME/security validation
- 실제 image-to-mesh AI model adapter
- GPU queue와 long-running job
- mesh repair, watertightness와 coordinate normalization
- surface/solid/hollow voxelization
- Minecraft version별 block state palette
- 색상 양자화와 방향별 block texture 대표값
- Sponge schematic serialization과 semantic round-trip
- multi-user auth, quota, private object storage
- voxel 대용량 browser payload와 instanced rendering
- BOM, 레이어 보기와 Minecraft import UX

## 7. 라이선스와 provenance

`gpthreejs`는 MIT 라이선스다. 코드를 직접 복사하거나 변형할 경우 다음을 수행한다.

1. 원본 LICENSE와 저작권 고지를 보존한다.
2. 복사한 파일 또는 변경 기록에 출처를 남긴다.
3. 3Craft 자체 라이선스와 결합 가능성을 확인한다.
4. sample image, Minecraft texture, model weight는 각각 별도 라이선스로 검토한다.
5. 테스트 fixture는 출처, 사용 목적과 배포 가능 여부를 manifest에 기록한다.

MIT인 엔진 코드와 Minecraft 자산 또는 AI model weight의 사용 권한을 혼동하지 않는다.

## 8. 최종 적용 원칙

- 보이지 않는 형상을 `observed`로 표시하지 않는다.
- 입력이 부족하면 품질 경고를 숨기지 않는다.
- reconstruction 성공과 delivery 성공을 분리한다.
- 모든 단계는 schema, content hash, input lineage와 version을 갖는다.
- 품질 metric은 필요조건이며 invalid export를 상쇄할 수 없다.
- provider나 GPU가 없으면 fake result를 만들지 않는다.
- artifact를 먼저 만들고 검사 후 공개한다.
- UI가 아니라 pipeline contract부터 vertical slice로 검증한다.
