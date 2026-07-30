# 이미지 Intake, 생성, 전처리와 충분성

## 1. 목적

입력 단계는 단순 upload가 아니라 이후 결과의 신뢰 수준을 결정하는 evidence pipeline이다. 원본을 보존하고 모든 파생물을 추적하며, 현재 입력으로 선택한 reconstruction route를 안정적으로 수행할 수 있는지 먼저 판단한다.

## 2. 지원 입력과 초기 제한

MVP:

- PNG
- JPEG
- WebP
- 단일 frame
- 단일 중심 물체
- 최소 한 변 256px 권장
- 최대 byte와 decoded pixel 제한은 configuration

초기 제안:

- 10MB 이하
- 24 megapixel 이하
- animated PNG/WebP/GIF 거부
- 지나치게 긴 aspect ratio 거부 또는 warning

제한 값은 security test와 운영 지표 후 조정한다. client 제한은 UX용이고 server가 다시 검사한다.

## 3. Upload 단계

```text
client preflight
→ upload session/owner/quota
→ private temporary object
→ server signature + decode
→ canonical image
→ asset manifest + SHA-256
→ ready 또는 rejected
```

검사 순서:

1. declared byte size와 quota
2. magic byte
3. 안전한 decoder로 header 검사
4. width/height/frame/pixel count
5. 전체 decode
6. EXIF orientation
7. ICC profile 처리와 sRGB normalization
8. alpha 유효성
9. canonical re-encode
10. original/canonical checksum과 manifest

확장자와 사용자 파일명은 신뢰하지 않는다. 원본 object는 immutable하고 canonical object는 별도 ID를 가진다.

## 4. Provenance와 evidence 분류

| source | origin | evidenceClass | 설명 |
|---|---|---|---|
| 사용자가 올린 실제 사진/그림 | upload | observed | 입력에서 실제로 보이는 것만 observed |
| 서비스가 prompt로 생성 | generated | design-intent | 사용자가 원하는 설계 목표 |
| 생성 이미지의 보정본 | edited | design-intent | 원본 lineage 유지 |
| depth/mask/normal | derived | inferred | 알고리즘 추정 |
| 생성된 side/back view | generated | design-hypothesis | 일관성 검증 전 hypothesis |
| reconstruction mesh 뒷면 | derived | inferred | observed로 승격 금지 |

사용자가 생성 결과를 승인해도 `design-intent`가 `observed`로 바뀌지 않는다. 승인은 “목표로 채택”했다는 별도 metadata다.

## 5. 이미지 생성

### 5.1 Provider port

```python
class ImageGenerationProvider(Protocol):
    async def generate(self, request: GenerateImageRequest, budget: ProviderBudget) -> GenerateImageResult: ...
    async def cancel(self, provider_request_id: str) -> None: ...
```

내부 request:

- user prompt
- system profile ID
- aspect ratio
- count
- seed 또는 seed policy
- safety context
- output constraints
- idempotency/provider correlation

provider-specific parameter는 adapter configuration에 둔다.

### 5.2 Single-object prompt profile

사용자 prompt의 의미를 변경하지 않는 범위에서 다음 지침을 추가한다.

- exactly one primary object
- entire object inside frame
- neutral/transparent/simple background
- no text, watermark or frame
- moderate orthographic-like or three-quarter camera
- even lighting, limited cast shadow
- no motion blur or extreme depth of field
- distinguishable silhouette

원문 prompt, profile version과 최종 provider prompt를 구분해 보관한다. 사용자에게 profile 적용 여부를 알린다.

### 5.3 Provider budget

job/user 기준:

- 최대 후보 수
- 최대 edit/generate 횟수
- 최대 wall time
- 최대 비용 추정
- provider retry 횟수
- 동시 요청 수

budget 소진은 무한 retry가 아니라 `ask`/`failed`로 끝난다. provider가 설정되지 않으면 null adapter가 실제 이미지처럼 보이는 placeholder를 만들지 않고 capability unavailable을 반환한다.

### 5.4 Provider output ingest

provider URL을 영구 source로 사용하지 않는다.

1. 허용 domain/provider response인지 확인
2. server-side로 제한된 크기만 다운로드
3. signature/decode/security 검사
4. private storage에 canonical asset 생성
5. provider provenance와 checksum 저장
6. temporary provider URL 폐기

임의 사용자 URL fetch와 이 경로를 공유하지 않는다.

## 6. Segmentation과 matte

우선순위:

1. 신뢰 가능한 alpha
2. 사용자가 제공/수정한 mask
3. segmentation provider
4. local heuristic fallback
5. 사용자에게 입력 개선 요청

matte diagnostics:

- foreground ratio
- bounding box와 frame touch
- connected component 수와 크기
- internal hole 비율
- edge noise
- confidence
- shadow 포함 가능성
- hair/fur/thin structure 가능성

자동 mask가 불확실하면 조용히 사용하지 않고 original/masked toggle과 warning을 표시한다.

MVP에서 full brush editor를 제공하지 않아도 `use alpha`, `use original`, `retry segmentation`과 입력 교체를 제공한다.

## 7. Reversible normalization

operation chain:

- orient
- color convert
- crop-to-mask with margin
- pad to model aspect
- resize
- background compose
- alpha premultiply/unpremultiply 필요 시 기록

규칙:

- 원본을 덮어쓰지 않는다.
- 각 operation은 input/output size, offset, parameters와 reversibility를 기록한다.
- destructive crop보다 padding을 우선한다.
- model별 input을 별도 artifact로 만든다.
- source-space overlay를 위해 역변환 가능한 구간을 제공한다.

## 8. 3Craft Sense Pack

MVP artifact:

- `canonical.png`
- `matte.png`
- `masked.png`
- `edges.png`
- `depth-proxy` 이미지/데이터
- `input-palette.json`
- `diagnostics.json`
- `transform-chain.json`
- `sense-pack.json`

모드:

| 모드 | 용도 | 계산 |
|---|---|---|
| draft | 빠른 UI 진단 | metadata, alpha/matte, 기본 palette |
| standard | 기본 conversion | edges, depth, diagnostics 포함 |
| high | 64축/고품질 route | 추가 model-specific 진단과 multi-view consistency |

Sense Pack은 reconstruction input이 아니라도 relief, route selection, metric과 user guidance에 사용한다.

## 9. Sufficiency policy

### 9.1 출력

- `verdict`: pass/conditional/reject
- `agentAction`: continue/ask/abort
- `sufficient`
- score
- issue code/severity/evidence/remedy
- user message
- policy version
- route

### 9.2 공통 blocker

- `FILE_MISSING`
- `FILE_UNSUPPORTED`
- `DECODE_FAILED`
- `IMAGE_TOO_LARGE`
- `RESOLUTION_TOO_LOW`
- `FOREGROUND_EMPTY`
- `SUBJECT_TOO_SMALL`
- `SUBJECT_SEVERELY_CLIPPED`
- `MASK_INVALID`
- `POLICY_OR_LICENSE_BLOCKED`

blocker가 있으면 production job을 만들지 않는다.

### 9.3 Warning/conditional issue

- `MULTIPLE_SUBJECTS`
- `BACKGROUND_COMPLEX`
- `EXPOSURE_DARK`
- `EXPOSURE_BRIGHT`
- `IMAGE_BLURRY`
- `THIN_STRUCTURE_RISK`
- `TRANSPARENT_MATERIAL_RISK`
- `REFLECTIVE_MATERIAL_RISK`
- `HIDDEN_SURFACE_INFERRED`
- `SIDE_VIEW_MISSING`
- `BACK_VIEW_MISSING`
- `VIEW_INCONSISTENT`
- `PALETTE_COLOR_OUT_OF_GAMUT`

### 9.4 Route별 정책

#### Relief

필수:

- usable foreground
- front/source view
- depth proxy 또는 대체 height rule

side/back view 부족은 blocker가 아니다. 결과가 2.5D임을 명확히 표시한다.

#### Single-image mesh

필수:

- 단일 주 component
- 충분한 silhouette
- frame 내 전체 물체
- 선택 model이 지원하는 입력 형식

side/back 부족은 일반적으로 warning이지만 high fidelity 목표에서 `ask`가 될 수 있다.

#### Multi-view mesh

필수:

- 최소 view 수
- view label
- 같은 subject identity
- scale/camera 일관성
- cross-view feature consistency

생성 view가 서로 다르면 reject 또는 해당 view 제외를 요구한다.

### 9.5 설정과 gate 강도

- 16축은 작은 detail 부족을 완화할 수 있다.
- 64축은 high-resolution source와 더 높은 matte confidence를 요구한다.
- transparent/reflection risk는 reconstruction route에 따라 severity가 다르다.
- user override는 warning/일부 conditional만 가능하다.
- override에는 user, time, issue, 이유와 결과 warning을 기록한다.

## 10. Multi-view ReferenceSet

후속 또는 고품질 입력:

- source/front
- left/right side
- back
- optional top/detail

각 view에는 declared/detected view, asset hash, evidence class와 visible feature가 있다. consistency 검사 예:

- dominant palette 차이
- silhouette size ratio
- 주요 component 수
- 사용자 표식/손잡이/뿔 등 feature 존재
- 좌우가 뒤바뀐 가능성
- 생성된 view의 subject drift

불일치 view를 평균내지 않고 issue로 드러낸다.

## 11. 사용자 메시지 원칙

나쁜 메시지:

- “AI 변환에 실패했습니다.”
- “Error code 422.”

좋은 메시지:

- “물체가 이미지 오른쪽에서 잘려 있어 완전한 형상을 만들기 어렵습니다. 물체 전체가 보이는 이미지를 사용하거나 relief 모드를 선택하세요.”
- “이 이미지는 정면만 보여 뒷면은 AI가 추정합니다. side view를 추가하면 더 안정적인 결과를 얻을 수 있습니다.”

public 메시지와 operator diagnostic을 분리한다.

## 12. 출력과 handoff

Sufficiency를 통과한 handoff에는 다음이 있다.

- immutable source asset
- canonical asset
- ReferenceSet
- TransformChain
- Sense Pack
- SufficiencyReport
- 선택 route와 settings
- input semantic hash

reconstruction stage는 직접 upload path를 받지 않고 이 handoff manifest를 받는다.

## 13. 테스트와 완료 조건

필수 fixture:

- transparent PNG
- EXIF-rotated JPEG
- valid WebP
- corrupt image
- MIME spoof
- huge dimensions
- empty alpha
- frame-filling/clipped subject
- multiple components
- thin handle/antenna
- generated image provenance
- inconsistent generated side view

완료 조건:

- original과 canonical checksum/lineage가 기록됨
- generated asset이 observed로 분류되지 않음
- normalization metadata로 overlay 좌표를 재현함
- route별 동일 fixture가 기대 verdict/action을 냄
- provider unavailable/budget exhausted가 fake result 없이 종료됨
- blocker input이 queue에 production conversion을 만들지 않음
