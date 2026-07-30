# Frontend, Viewer와 UX 계획

## 1. 목표

프론트엔드는 복잡한 AI/geometry pipeline을 단순한 단계로 보여주되 불확실성과 비용을 숨기지 않는다. Three.js viewer는 수만~수십만 block을 안정적으로 표시하고 결과 교체 시 GPU resource를 확실히 해제해야 한다.

## 2. 정보 구조와 route

```text
/                         제품 소개, 예시, 시작
/create                   source 선택과 conversion 설정
/jobs/:jobId              진행/실패/완료 결과
/help/input-guide         좋은 입력과 한계
/help/minecraft-import    WorldEdit import 안내
```

후속:

- `/library`: 저장된 asset/job
- `/settings`: provider/custom palette
- `/share/:id`: 사용자가 명시적으로 공개한 결과

job URL은 새로고침과 다른 tab에서도 복구 가능해야 한다.

## 3. Create workspace

```text
CreatePage
├── SourceMethodTabs
│   ├── UploadPanel
│   └── GeneratePanel
├── SourcePreview
├── MatteReview
├── SufficiencySummary
├── ConversionSettings
├── CostQualityEstimate
└── StartConversionAction
```

### 3.1 Upload UX

- drag/drop와 file button 모두 제공
- 허용 format/크기 표시
- local preview는 임시이며 server validation 전 ready로 표시하지 않음
- upload와 validation progress 분리
- client object URL은 교체/unmount 시 revoke
- extension/MIME 오류, size, decode 실패를 구분
- retry가 새 duplicate asset을 만들지 않도록 upload session 처리

### 3.2 Generate UX

- prompt 입력
- single-object profile 설명
- 선택적 seed/variation은 advanced
- generation job 진행 상태
- 후보 grid와 provenance 요약
- provider policy/rate limit 오류
- 선택한 후보를 source asset으로 채택
- 생성 이미지는 “실제 사진”이 아닌 “생성된 설계 이미지”로 표시

### 3.3 Matte review

- original/masked toggle 또는 side-by-side
- checkerboard alpha background
- clipping/multiple subject warning overlay
- `다시 분리`, `원본 alpha 사용`, `다른 이미지 선택`
- 후속 brush editor를 위한 mask artifact/version 경계

## 4. Conversion settings

### 4.1 기본 영역

- 변환 방식: AI 3D / relief
- 크기: 16/32/64
- 채움: surface/hollow/solid
- palette profile
- 방향/회전

### 4.2 고급 영역

- shell thickness
- filler block
- dithering
- transparent block 허용
- gravity block 허용
- thin feature 보존
- small component cleanup
- target Minecraft version

### 4.3 Progressive disclosure

일반 사용자에게 provider/model ID나 geometry threshold를 노출하지 않는다. 선택 결과에 영향을 주는 개념만 설명한다.

- 64는 처리 시간과 block 수 증가 경고
- solid는 block 수 증가
- relief는 빠르지만 360도 형상이 아님
- AI 3D는 뒷면을 추정함
- color-rich palette는 block 종류가 늘 수 있음

## 5. Sufficiency UX

- pass: 바로 진행
- conditional/continue: warning과 결과 한계 확인 후 진행
- conditional/ask: 권장 입력 개선과 허용된 대체 route
- reject/abort: start button disabled, blocker remedy

issue를 단순 점수로 숨기지 않는다. 사용자가 override할 수 있는 warning은 checkbox가 아니라 구체적인 결과를 설명하고 명시 확인을 받는다.

예:

> 이 이미지는 정면만 보여 뒷면은 AI가 추정합니다. 계속하거나, side view를 추가하거나, relief를 선택할 수 있습니다.

## 6. Job 화면

### 6.1 진행 중

- source thumbnail
- 현재 stage와 설명
- 전체 progress
- 시작/경과 시간
- cancel
- page를 닫아도 실행됨 안내
- 연결 상태(SSE/polling fallback)

stage label:

- 입력 분석
- 3D 형상 생성
- 형상 정리
- 블록 변환
- 색상/재료 선택
- 결과 검토
- schematic 생성
- 최종 검증

정확하지 않은 남은 시간을 임의 표시하지 않는다. 충분한 historical metric이 생기면 범위 형태로 제공한다.

### 6.2 실패

- 실패 stage
- 사용자 메시지
- retry 가능 여부
- remedy action
- relief/낮은 해상도/입력 교체
- support용 job/request ID

stack trace, provider raw error와 storage path는 표시하지 않는다.

### 6.3 완료

```text
ResultPage
├── SourceAndWarnings
├── VoxelViewer
├── ViewerToolbar
├── DimensionsAndQuality
├── BlockBOM
├── ExportCompatibility
├── ArtifactDownloads
└── ConvertAgain
```

## 7. Client 상태

server state와 local editing state를 분리한다.

```text
SourceState:
  empty → local-selected → uploading → validating → ready|rejected

GenerationState:
  idle → submitting → queued → generating → completed|failed|cancelled

ConversionDraft:
  editing → checking → submit-ready

JobState:
  queued → running stages → completed|failed|cancelled

ViewerState:
  idle → fetching → decoding → building → ready|error → disposed
```

server state는 query/cache layer가 관리하고 Three.js object는 React serializable state에 넣지 않는다.

## 8. Viewer architecture

### 8.1 React wrapper

```text
VoxelViewer React component
  useEffect mount
    → create ViewerRuntime(canvas/container)
    → load PreviewArtifact
    → render/update
  cleanup
    → abort fetch/decode
    → terminate worker
    → dispose scene/resources/renderer/controls
```

viewer runtime은 imperative class/module로 두고 React는 props와 lifecycle만 연결한다.

### 8.2 Scene

- one renderer/canvas
- PerspectiveCamera
- OrbitControls
- model bounds 기반 camera fit
- neutral ambient/hemisphere/directional light
- grid/ground toggle
- sRGB output
- DPR 상한
- resize observer 기반 크기 조절

canonical capture mode는 고정 viewport, camera, light, tone mapping과 background를 사용한다.

### 8.3 Block rendering

금지:

- block마다 React component
- block마다 geometry/material
- 매 frame instance matrix 재생성
- render loop에서 React state update
- texture/material 중복 생성

기본:

- shared box geometry
- block state/material별 `InstancedMesh`
- typed array로 matrix/color 준비
- 정적 결과는 `instanceMatrix.needsUpdate` 한 번
- 내부 voxel을 preview에서 생략 가능
- selection을 위한 instance ID→voxel coordinate map

64축에서 draw call/palette 수가 과도하면 색상 material grouping 또는 texture atlas를 사용한다.

### 8.4 고해상도 전략

단순 instancing도 128³ solid에서 비효율적이다.

단계적 최적화:

1. occupied voxel만 instance
2. 완전히 둘러싸인 interior block skip
3. frustum/bounds
4. chunk 단위 build/visibility
5. exposed-face mesh
6. greedy meshing

레이어 보기와 block selection을 유지해야 하므로 preview representation과 download VoxelModel을 분리할 수 있다.

## 9. Preview decode

- binary fetch
- content length/limit 확인
- Web Worker에서 header/checksum/decode
- palette와 coordinate typed array 생성
- transferable buffer로 main thread 전달
- 진행률 또는 skeleton 표시
- abort signal 지원
- malformed data는 viewer error이고 job artifact corruption metric 발생

Python writer와 TypeScript decoder는 같은 golden binary를 읽어야 한다.

## 10. Viewer 기능

MVP MUST:

- orbit/zoom/pan
- reset camera
- grid/background
- dimensions와 orientation indicator
- source/result 비교
- palette/BOM 연동
- fullscreen 또는 충분한 확대

MVP SHOULD:

- X/Y/Z layer clipping
- 선택 block state/coordinate
- palette block 숨기기/highlight
- screenshot
- canonical front/side/isometric view

후속:

- exploded layers
- build order
- silhouette overlay
- block replacement
- live palette remap

## 11. Resource ownership

`ViewerRuntime`가 소유:

- renderer
- controls
- geometries
- materials
- textures
- render targets
- workers
- event listeners
- animation frame
- object URLs

`dispose()`는 idempotent해야 한다.

검증:

- 결과 A→B→A 반복
- route 이동/복귀
- 10회 create/render/dispose
- WebGL context 수
- renderer.info geometries/textures
- worker/listener 누적
- heap/GPU memory 경향

gpthreejs의 `RuntimeResources`와 browser smoke 패턴을 확장한다.

## 12. 접근성

- dropzone 외 button
- form label/description/error 연결
- status를 색상만으로 표현하지 않음
- progress text와 live region
- canvas 외 dimensions/BOM/warnings 표
- keyboard action과 focus order
- modal focus trap
- reduced motion 존중
- viewer shortcut 설명
- table sort/filter에 accessible name

3D canvas를 완전히 음성화하려 하지 말고 동일 정보를 text와 layer table로 제공한다.

## 13. 반응형 UI

Desktop:

- source/settings와 viewer 2-column
- viewer가 주 영역

Mobile/tablet:

- 단계형 vertical flow
- viewer 높이 제한과 fullscreen action
- 고급 옵션 collapse
- BOM virtualized list 필요 여부 측정
- WebGL capability/메모리 부족 시 static canonical images와 download 제공

## 14. 오류 경계

별도 error boundary:

- create form
- job stream
- viewer decode/runtime
- downloads

viewer crash가 job 상태와 다운로드를 숨기지 않게 한다. WebGL unavailable이면 canonical server preview와 BOM을 표시한다.

## 15. 보안과 개인정보 UI

- signed URL을 log/analytics에 보내지 않음
- 원본 파일명과 prompt를 page title/URL에 넣지 않음
- 보존 기간과 외부 provider 전송 표시
- public share는 opt-in 전까지 없음
- download 파일명은 정제된 display name 사용
- raw HTML/error/provider message 렌더 금지

## 16. Frontend 테스트 기준

component:

- upload states
- generation states
- sufficiency issue/action
- settings validation
- job terminal states
- BOM count/format

browser:

- upload→fixture conversion→preview→download
- refresh/reconnect
- SSE failure→polling
- cancel race
- viewer malformed payload
- WebGL unavailable
- console/page error 0
- repeated viewer dispose
- keyboard-only flow

성능:

- route bundle split
- Three.js lazy load
- 32/64 decode/build/frame benchmark
- DPR와 mobile fallback

## 17. 완료 조건

- upload와 generation 모두 동일 source contract로 연결됨
- blocker sufficiency가 conversion을 막음
- job 새로고침/연결 복구가 됨
- 64축 fixture가 목표 FPS를 통과함
- layer/BOM이 VoxelModel과 일치함
- viewer 반복 교체에서 resource가 누적되지 않음
- WebGL 실패에도 artifact 다운로드가 가능함
- 핵심 흐름의 keyboard/browser E2E가 통과함
