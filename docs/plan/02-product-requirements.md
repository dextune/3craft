# 제품 요구사항

## 1. 제품 문제

Minecraft에서 사진이나 콘셉트를 블록 조형물로 재현하려면 사용자가 3D 형상을 추정하고, 적절한 해상도로 voxel화하고, 수백 가지 블록 중 색과 배치 제약에 맞는 블록을 고른 뒤, WorldEdit 호환 구조로 변환해야 한다. 3Craft는 이 과정을 자동화하되 AI의 추정과 실제 관찰 정보를 분리하고 사용자가 결과 크기·재료·형태를 제어할 수 있게 한다.

## 2. 목표와 비목표

### 2.1 목표

- `G-01`: 3D/NBT 지식이 없는 사용자도 이미지 한 장으로 블록 조형물을 생성한다.
- `G-02`: 미리보기 이미지가 아니라 실제 Minecraft 도구에서 읽을 수 있는 구조 파일을 제공한다.
- `G-03`: 크기, 채움 방식, palette, 회전과 품질/비용 trade-off를 사용자가 제어한다.
- `G-04`: 보이지 않는 면의 추정, 손실된 특징과 export target version을 투명하게 설명한다.
- `G-05`: 외부 image/reconstruction provider를 교체할 수 있고 동일한 후처리·export 계약을 사용한다.
- `G-06`: 동일 intermediate mesh와 설정은 동일 voxel 결과를 만든다.
- `G-07`: invalid output을 성공으로 공개하지 않는 fail-closed 제품 경험을 제공한다.

### 2.2 MVP 비목표

- Minecraft 서버나 사용자의 월드에 직접 구조물을 배치
- 리소스팩용 item/entity JSON 또는 Blockbench project 생성
- animation, rig, skin 또는 mob behavior 생성
- redstone 의미론, 내부 동선 또는 구조 공학 자동 설계
- 도시, 건물 내부, 복수 인물 장면의 정확한 복원
- 실제 치수나 공학적 정확성을 보장하는 digital twin
- 모든 Minecraft/mod/edition/version 동시 지원
- 사용자 콘텐츠 marketplace와 공개 gallery
- 생성된 뒷면을 실제 관찰 데이터처럼 표시

## 3. 대상 사용자

### Persona A: 일반 플레이어

- 한 장의 캐릭터, 동물, 장식품 이미지를 구조물로 만들고 싶다.
- 3D 도구 경험이 적다.
- 빠른 기본값, 명확한 오류와 다운로드 안내가 중요하다.

### Persona B: Minecraft 건축가/콘텐츠 제작자

- 서버 로비, 영상, 맵에 넣을 조형물이 필요하다.
- 크기, block palette, hollow/solid와 레이어를 제어하고 싶다.
- BOM과 WorldEdit 호환성이 중요하다.

### Persona C: 개발자/운영자

- repeatable job, provenance, API와 batch 처리가 필요하다.
- model version, seed, cache, 비용과 결과 결정성을 중요하게 본다.
- 공개 API는 후속이지만 내부 API는 이 요구를 막지 않게 설계한다.

MVP UI는 A와 B에 우선 최적화한다.

## 4. 핵심 사용자 여정

### 4.1 업로드에서 schematic까지

1. 사용자가 PNG/JPEG/WebP를 선택한다.
2. client 사전 검증 후 private storage에 업로드한다.
3. 서버가 파일 signature, decode, 크기와 안전성을 재검증한다.
4. 자동 배경 제거와 quality diagnostics를 표시한다.
5. 사용자는 16/32/64 크기, 복원 경로, fill mode와 palette를 고른다.
6. 충분성 gate가 경고·필수 보완·중단 중 하나를 제시한다.
7. 사용자가 허용된 조건으로 job을 생성한다.
8. 화면은 단계와 진행률을 표시하고 새로고침 후 복구한다.
9. 결과 viewer에서 회전, 레이어, 블록 수량과 경고를 확인한다.
10. 검증된 `.schem`, BOM과 manifest를 다운로드한다.

### 4.2 프롬프트에서 schematic까지

1. 사용자가 원하는 물체를 설명한다.
2. 시스템이 single-object 생성 profile과 제약을 보여준다.
3. 이미지 provider가 후보를 생성한다.
4. 후보마다 provider/model/seed/prompt provenance를 기록한다.
5. 사용자가 하나를 선택한다.
6. 해당 asset은 `design-intent`로 분류되고 업로드 asset과 같은 conversion pipeline을 사용한다.

### 4.3 실패와 재시도

1. job이 특정 stage에서 실패한다.
2. 사용자에게 오류 코드가 아닌 이해 가능한 원인과 remedy를 보여준다.
3. retryable 오류면 동일 job attempt 또는 clone job을 제공한다.
4. 입력 부족이면 더 나은 이미지, side view, relief 또는 낮은 해상도를 제안한다.
5. 원본을 재업로드하지 않고 설정만 바꿔 새 conversion을 만들 수 있다.

## 5. 기능 요구사항

### 5.1 Asset와 입력

- `FR-ASSET-001 MUST`: PNG, JPEG, WebP를 지원한다.
- `FR-ASSET-002 MUST`: extension과 client MIME이 아니라 magic byte와 실제 decode 결과를 신뢰한다.
- `FR-ASSET-003 MUST`: byte size, decoded pixel count, width/height와 frame 수를 제한한다.
- `FR-ASSET-004 MUST`: EXIF orientation을 반영하고 불필요한 metadata를 제거한 canonical image를 만든다.
- `FR-ASSET-005 MUST`: 원본은 immutable artifact로 보존하고 전처리본은 별도 artifact로 만든다.
- `FR-ASSET-006 MUST`: source SHA-256와 사용자/생성 origin을 기록한다.
- `FR-ASSET-007 SHOULD`: alpha가 있으면 segmentation의 우선 evidence로 사용한다.
- `FR-ASSET-008 SHOULD`: 자동 mask를 변환 전에 비교할 수 있게 한다.
- `FR-ASSET-009 MUST`: 임의 URL을 서버가 가져오는 입력은 MVP에서 금지한다.

### 5.2 이미지 생성

- `FR-GEN-001 MUST`: 텍스트 prompt로 변환용 이미지를 생성할 수 있다.
- `FR-GEN-002 MUST`: provider 호출은 server-side adapter를 통한다.
- `FR-GEN-003 MUST`: provider/model/final prompt/seed/request ID와 비용 metadata를 기록한다.
- `FR-GEN-004 MUST`: 생성 이미지를 observed로 분류하지 않는다.
- `FR-GEN-005 SHOULD`: single object, full body/object in frame, neutral background, moderate perspective를 보조 prompt에 적용한다.
- `FR-GEN-006 SHOULD`: provider 거부, quota와 timeout을 사용자 메시지로 변환한다.
- `FR-GEN-007 MAY`: 정면·측면·후면의 일관된 multi-view 생성을 지원한다.

### 5.3 충분성·전처리

- `FR-SUF-001 MUST`: conversion 전 image diagnostics와 route-aware sufficiency를 실행한다.
- `FR-SUF-002 MUST`: 결과는 `pass|conditional|reject`, `continue|ask|abort`, issue와 remedy를 포함한다.
- `FR-SUF-003 MUST`: 빈 foreground, decode 실패, 지나치게 작은 피사체는 production conversion을 막는다.
- `FR-SUF-004 MUST`: single image의 hidden side가 inferred임을 결과에 표시한다.
- `FR-SUF-005 SHOULD`: 고품질 mesh 경로에서 side/back evidence 부족을 더 엄격하게 처리한다.
- `FR-SUF-006 SHOULD`: relief 경로는 단일 정면 이미지에 맞는 별도 gate를 사용한다.
- `FR-SUF-007 MAY`: 사용자가 warning을 override할 수 있으나 이유와 policy version을 기록한다.

### 5.4 Reconstruction

- `FR-REC-001 MUST`: deterministic relief baseline을 제공한다.
- `FR-REC-002 MUST`: 하나 이상의 single-image reconstruction adapter를 선택 가능하게 한다.
- `FR-REC-003 MUST`: provider/model version, seed, runtime과 output checksum을 저장한다.
- `FR-REC-004 MUST`: 빈/NaN/invalid mesh를 다음 단계로 넘기지 않는다.
- `FR-REC-005 MUST`: raw mesh와 normalized/repaired mesh를 구분한다.
- `FR-REC-006 SHOULD`: model/provider 실패 시 허용된 fallback을 제안한다.
- `FR-REC-007 MAY`: 사용자 제공 또는 생성 multi-view를 사용한다.

### 5.5 Voxel과 palette

- `FR-VOX-001 MUST`: 최대 축 16, 32, 64 preset을 제공한다.
- `FR-VOX-002 MUST`: `surface`, `hollow`, `solid`의 의미를 고정하고 결과 metadata에 기록한다.
- `FR-VOX-003 MUST`: 동일 mesh/settings/palette version에 결정적인 결과를 낸다.
- `FR-VOX-004 MUST`: 사용 가능한 Minecraft block state를 versioned palette로 제한한다.
- `FR-VOX-005 MUST`: 중력, 투명, block entity와 위험한 block category를 filter할 수 있다.
- `FR-VOX-006 MUST`: total count, block별 count, dimensions와 component 수를 계산한다.
- `FR-VOX-007 SHOULD`: perceptual color mapping을 사용한다.
- `FR-VOX-008 SHOULD`: 선택적 dithering과 최소 feature/두께 정책을 제공한다.
- `FR-VOX-009 SHOULD`: disconnected/floating component를 경고하거나 정책에 따라 제거한다.
- `FR-VOX-010 MAY`: custom allow/deny palette를 제공한다.

### 5.6 Job과 상태

- `FR-JOB-001 MUST`: image generation과 conversion을 비동기 job으로 처리한다.
- `FR-JOB-002 MUST`: 현재 stage, 단조 증가 progress와 public event를 제공한다.
- `FR-JOB-003 MUST`: `completed`, `failed`, `cancelled` terminal state를 구분한다.
- `FR-JOB-004 MUST`: idempotency key와 request hash로 중복 job을 통제한다.
- `FR-JOB-005 MUST`: queue의 at-least-once delivery에서 중복 공개 artifact가 생기지 않아야 한다.
- `FR-JOB-006 SHOULD`: queued job 취소와 실행 중 cancel request를 지원한다.
- `FR-JOB-007 SHOULD`: retryable/terminal 오류를 구분한다.

### 5.7 Viewer와 결과

- `FR-VIEW-001 MUST`: orbit, zoom, pan과 reset을 제공한다.
- `FR-VIEW-002 MUST`: dimensions, total blocks, block별 BOM과 warnings를 표시한다.
- `FR-VIEW-003 MUST`: 원본 이미지와 voxel 결과를 비교한다.
- `FR-VIEW-004 SHOULD`: X/Y/Z layer 또는 clipping view를 제공한다.
- `FR-VIEW-005 SHOULD`: block 선택 시 block state를 표시한다.
- `FR-VIEW-006 SHOULD`: 배경/grid/lighting을 바꿀 수 있다.
- `FR-VIEW-007 MUST`: 결과 교체·route 이동 시 GPU resource를 해제한다.

### 5.8 Export

- `FR-EXP-001 MUST`: Java Edition용 `.schem`을 생성한다.
- `FR-EXP-002 MUST`: target Minecraft version과 DataVersion을 manifest에 기록한다.
- `FR-EXP-003 MUST`: 독립 parser round-trip을 통과한 결과만 공개한다.
- `FR-EXP-004 MUST`: schematic count와 BOM이 일치해야 한다.
- `FR-EXP-005 MUST`: manifest에 source lineage, pipeline/model/palette version과 checksums를 기록한다.
- `FR-EXP-006 MUST`: source image, secret, internal path와 signed URL을 bundle에 포함하지 않는다.
- `FR-EXP-007 SHOULD`: BOM을 JSON과 CSV로 제공한다.
- `FR-EXP-008 MAY`: `.litematic`, `.mcstructure`, GLB를 adapter로 추가한다.

## 6. 비기능 요구사항

### 6.1 성능

- `NFR-PERF-001`: inference를 제외한 API p95 목표는 500ms다.
- `NFR-PERF-002`: 활성 job progress는 최대 2초 간격으로 갱신한다.
- `NFR-PERF-003`: 권장 데스크톱에서 64축 preview 조작 30FPS 이상을 목표로 한다.
- `NFR-PERF-004`: 대규모 voxel decode와 instance 배열 생성은 Web Worker를 사용한다.
- `NFR-PERF-005`: 128축은 성능·비용 gate를 통과하기 전 공개하지 않는다.

### 6.2 신뢰성과 결정성

- `NFR-REL-001`: stage manifest와 checksum으로 crash 후 안전한 재시도를 지원한다.
- `NFR-REL-002`: completed는 검증된 필수 artifact가 모두 있을 때만 설정한다.
- `NFR-REL-003`: ML stage의 비결정성과 deterministic post-process를 구분한다.
- `NFR-REL-004`: pipeline/palette/schema version 변경 시 cache key가 분리된다.

### 6.3 호환성과 접근성

- `NFR-COMP-001`: 최신 Chrome, Edge, Firefox의 최근 두 major를 우선한다.
- `NFR-COMP-002`: target Minecraft/WorldEdit 조합을 명시하고 smoke matrix를 유지한다.
- `NFR-A11Y-001`: canvas 외에 모든 결과 정보를 구조화된 text로 제공한다.
- `NFR-A11Y-002`: 업로드→변환→다운로드 핵심 흐름을 키보드로 수행할 수 있다.

### 6.4 보안·개인정보·비용

- `NFR-SEC-001`: asset은 기본 private이고 owner scope로 접근한다.
- `NFR-SEC-002`: provider secret은 client bundle과 사용자 오류에 노출하지 않는다.
- `NFR-SEC-003`: worker는 resource/time/network 제한 아래 실행한다.
- `NFR-PRIV-001`: 보존 기간과 외부 provider 전송을 사용자에게 알린다.
- `NFR-COST-001`: user/job별 GPU seconds, generation count와 storage quota를 적용할 수 있다.

## 7. 성공 지표

초기 beta에서 측정한다.

- valid input의 end-to-end completion rate
- schematic semantic validation success rate
- WorldEdit manual import success rate
- reconstruction/voxel/export stage별 실패율
- 32축 median job duration과 GPU seconds
- 재변환률과 route 변경률
- 다운로드 성공률
- 사용자 평가 기준 ‘물체를 알아볼 수 있음’ 비율
- invalid upload 차단률과 authorization incident 0건
- 64축 viewer p95 frame time

지표 목표치는 benchmark baseline 확보 후 Accepted ADR로 확정한다. 숫자를 맞추기 위해 hard validation을 완화하지 않는다.

## 8. MVP 인수 시나리오

1. 투명 PNG와 일반 JPEG 각각을 업로드한다.
2. canonical asset과 provenance가 생성된다.
3. mask와 sufficiency 결과를 확인한다.
4. 32축 hollow, safe palette로 conversion을 생성한다.
5. job이 새로고침 후에도 추적된다.
6. viewer와 BOM이 로드된다.
7. `.schem`과 manifest를 다운로드한다.
8. 독립 parser와 실제 WorldEdit에서 불러온다.
9. BOM과 schematic block count가 일치한다.
10. 동일 repaired mesh/settings로 다시 voxel화했을 때 같은 semantic hash가 나온다.
11. 손상 이미지, 빈 foreground, 권한 없는 artifact와 invalid schematic은 공개되지 않는다.
12. 생성 이미지 경로도 동일 conversion 계약을 사용하며 provenance는 `design-intent`로 남는다.

## 9. 알려진 한계의 제품 표기

UI와 결과 manifest는 다음을 숨기지 않는다.

- 한 장의 이미지에서 보이지 않는 뒷면은 추정이다.
- 투명·반사·얇은 구조와 깊은 구멍은 손실될 수 있다.
- 낮은 block resolution은 작은 특징을 제거한다.
- 생성 이미지의 시점 간 일관성은 보장되지 않을 수 있다.
- `.schem` 호환성은 명시된 Minecraft/WorldEdit 조합에 한정된다.
- 선택한 palette에 따라 색상과 재질 인상이 크게 달라진다.
