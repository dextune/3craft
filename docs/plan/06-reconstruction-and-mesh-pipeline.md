# 3D Reconstruction과 Mesh Pipeline

## 1. 목표와 현실적 한계

reconstruction 단계의 목표는 시각적으로 완벽한 원본 복제품이 아니라 **Minecraft voxelization에 안정적인 3D 형상과 색상 근거**를 만드는 것이다. 단일 이미지에서 보이지 않는 면은 복구가 아니라 추론이며, 이를 provenance와 결과 warning에 남긴다.

우선순위:

1. 물체 인식 가능성과 큰 실루엣
2. 전체 비율과 주요 돌출/구멍
3. voxel화 가능한 topology
4. 안정적 좌표·scale·grounding
5. 표면 색상 전달
6. 작은 detail

## 2. Reconstruction route

### 2.1 Relief baseline

용도:

- 전체 pipeline을 외부 AI 없이 검증
- 로고, 동전, 얼굴, 벽화처럼 정면 표현이 중요한 입력
- GPU/provider 장애 fallback
- regression baseline

과정:

1. matte로 foreground domain 결정
2. depth proxy를 normalize
3. edge-aware smoothing
4. front height field 생성
5. 최소 base thickness를 가진 back plane 생성
6. boundary side wall 연결
7. watertight 검사
8. source image를 front에 project

설정:

- depth scale
- base thickness
- invert depth
- smoothing
- edge emphasis
- back shape(flat/mirrored)

결과 manifest에 `2.5D`, hidden side policy와 front view orientation을 표시한다.

### 2.2 Single-image mesh

MVP primary route다. model/provider가 raw mesh와 가능하면 texture/vertex color를 반환한다. vendor response를 바로 voxelizer에 넘기지 않고 공통 adapter 결과로 정규화한다.

### 2.3 Multi-view mesh

후속 route다. ReferenceSet consistency gate를 통과한 view만 사용한다. generated multi-view는 모두 design hypothesis이며 model이 통합한 hidden surface도 inferred다.

### 2.4 Imported mesh

사용자 GLB/OBJ upload는 유용하지만 MVP 비범위다. 내부 `MeshArtifact` 계약은 향후 imported mesh가 같은 후처리·voxel·export를 사용하도록 설계한다.

## 3. Provider adapter

```python
class ReconstructionProvider(Protocol):
    name: str
    capabilities: ReconstructionCapabilities

    async def reconstruct(
        self,
        request: ReconstructionRequest,
        budget: ComputeBudget,
    ) -> ReconstructionResult: ...
```

capability:

- single image/multi-view
- alpha support
- texture/vertex color/material output
- seed
- cancellation
- maximum input size
- output formats
- required GPU/VRAM
- hosted/local
- data retention policy

request는 asset ID/manifest와 server-approved model profile을 사용한다. client가 arbitrary local model path나 provider parameter를 전달하지 못하게 한다.

## 4. Model 선정 spike

특정 model을 문서만 보고 고정하지 않는다. 후보군은 TRELLIS, Hunyuan3D, TripoSR 계열 또는 당시 사용 가능한 hosted provider를 포함할 수 있지만 채택 전에 실제 license와 최신 배포 조건을 다시 확인한다.

### 4.1 Hard gate

- 상업/서비스 사용 가능 라이선스
- model weight 사용·배포 조건
- 입력 데이터 처리/보존 조건
- Linux/container 실행 가능
- output을 로컬에서 검증 가능
- 지원 hardware에서 실행 또는 예측 가능한 API 비용

하나라도 통과하지 못하면 품질과 무관하게 제외한다.

### 4.2 평가 corpus

최소 24개:

- 대칭 hard-surface 3
- 비대칭 hard-surface 3
- 유기체/동물 4
- 얇은 다리/손잡이/뿔 4
- 깊은 hole/concavity 3
- texture가 identity인 물체 3
- 투명/반사 실패 예상 2
- 서비스 생성 이미지 2

각 입력은 출처, 라이선스, expected challenge, observed view를 manifest에 기록한다.

### 4.3 측정

- canonical front silhouette IoU
- side/back visual plausibility blind score
- 주요 feature retention
- connected component 수
- non-manifold edge
- watertightness
- repair 후 volume/bounds 변화
- 32/64 voxel recognizability
- texture/color 전달
- p50/p95 latency
- peak RAM/VRAM
- cold/warm startup
- failure/OOM rate
- job당 비용

### 4.4 선택 방식

가중 점수는 의사결정 보조다. license, invalid output과 운영 가능성은 hard gate다. primary 한 개, fallback 한 개를 정하고 결정은 ADR로 남긴다.

## 5. Model input preparation

- canonical color space
- model-required square/padding
- matte/alpha compose
- background color profile
- input resolution
- camera/view token
- seed
- all transforms

provider별 normalization은 공통 canonical asset을 수정하지 않고 별도 model-input artifact로 만든다.

## 6. Raw output ingest

허용 container/format을 allowlist한다. raw output 검사:

- 파일 크기
- parser 성공
- scene/mesh 존재
- vertex/face count 상한
- NaN/Infinity
- texture count/size/format
- external URI/path 참조
- embedded script/extension 위험
- coordinate metadata

OBJ/MTL/GLB 등이 외부 file reference로 sandbox를 벗어나지 못하게 한다. hosted provider URL도 제한된 download 경로를 거친다.

## 7. 내부 좌표계

MVP 내부 canonical 좌표:

- right-handed
- `+X`: 사용자가 보는 오른쪽
- `+Y`: 위
- `+Z`: front 방향을 문서와 test fixture에서 고정
- ground plane: `Y=0`
- object center: horizontal bounds center
- unit: normalized model unit; 최대 extent 또는 height metadata 별도

model adapter가 source coordinate를 canonical로 변환하고 transform matrix를 기록한다. voxel/export가 각자 임의로 축을 바꾸지 않는다.

## 8. Mesh validation

raw와 repaired 모두 report를 만든다.

필수 검사:

- vertex/face 수와 bounds
- finite coordinates
- degenerate/zero-area triangle
- duplicate vertex/face
- normal 유무와 consistency
- connected components
- non-manifold edge/vertex
- open boundary/hole
- self-intersection 가능성
- UV 범위/texture 존재
- material count
- 극단적 aspect/scale
- ground penetration

빈 mesh, non-finite bounds, 지나치게 큰 데이터는 blocker다.

## 9. Mesh repair

순서와 parameter를 versioning한다.

1. finite하지 않은 primitive 제거
2. degenerate face 제거
3. tolerance 내 duplicate vertex merge
4. face winding과 normal 정리
5. small component 분류
6. 제한적 hole fill
7. self-intersection/duplicate shell 진단
8. optional remesh/simplify
9. ground alignment
10. scale normalize

원칙:

- 가장 큰 component만 무조건 남기지 않는다. 분리된 귀, 손잡이, 장식이 있을 수 있다.
- component volume/surface area, main body 거리와 source silhouette contribution을 함께 본다.
- repair가 원형을 크게 바꾸면 warning 또는 failure다.
- raw artifact를 덮어쓰지 않는다.
- repair 전후 vertex/face/component/bounds/volume 변화량을 기록한다.

## 10. Watertightness와 voxel route

- solid inside/outside 판정은 watertight mesh가 가장 안정적이다.
- repair로 닫을 수 없으면 generalized winding 또는 surface voxelization을 사용할 수 있다.
- hollow는 먼저 solid occupancy를 만들 수 있어야 한다.
- route가 요구하는 topology를 충족하지 못하면 surface mode로 명시적으로 downgrade하거나 사용자에게 ask한다.
- downgrade는 warning과 settings/result 차이에 기록한다. 조용한 모드 변경은 금지한다.

## 11. Texture와 color handoff

우선순위:

1. UV + texture
2. vertex color
3. material base color
4. source-view projection
5. neutral fallback

검사:

- UV NaN/out-of-range policy
- texture orientation/color space
- missing image
- alpha와 transparency
- multiple material assignment
- untextured face 비율

source projection을 사용할 때 visible front color와 inferred hidden color를 구분한다. hidden surface는 nearest observed color, symmetry 또는 neutral policy 중 선택하고 manifest에 기록한다.

## 12. Simplification과 detail budget

voxel target이 32축인데 수백만 triangle을 유지할 이유가 없다. 다만 voxelization 전 simplification이 silhouette를 망칠 수 있다.

정책:

- target resolution 기반 최대 triangle budget
- silhouette-aware 또는 error-bound simplification
- raw mesh 보존
- canonical views에서 simplification 전후 silhouette 차이 측정
- 얇은 feature는 resolution threshold와 함께 보호
- detail map은 block color에 필요할 때 유지

## 13. Compute budget

stage profile:

- wall/cpu time
- peak RSS
- peak VRAM
- model load time
- inference time
- repair time
- input/output bytes
- attempts/cache hit

budget:

- max wall time
- max GPU memory class
- max output face/texture size
- max retry
- cancellation checkpoint

budget 초과는 process 전체를 불안정하게 두지 않고 명확한 error와 대체 route를 반환한다.

## 14. 오류 분류

- `RECON_PROVIDER_UNAVAILABLE`
- `RECON_PROVIDER_REJECTED`
- `RECON_RATE_LIMITED`
- `RECON_TIMEOUT`
- `RECON_OOM`
- `RECON_INVALID_OUTPUT`
- `MESH_PARSE_FAILED`
- `MESH_EMPTY`
- `MESH_NONFINITE`
- `MESH_TOO_COMPLEX`
- `MESH_REPAIR_FAILED`
- `MESH_NOT_SOLID_CAPABLE`
- `TEXTURE_MISSING`
- `MODEL_LICENSE_BLOCKED`
- `BUDGET_EXHAUSTED`

각 error는 retryable, public message, remedies와 operator detail을 분리한다.

## 15. Determinism

- AI inference: seed/provider/runtime에 따른 제한적 재현성만 보장
- raw output ingest: 결정적
- repair/normalize: 동일 version/parameter에서 결정적
- voxelization 이후: 결정적

GPU별 floating point 차이가 있으면 raw byte hash 동일성을 요구하지 않고 tolerance metric과 canonical render를 사용한다. model/provider version이 불명확하면 cache를 재사용하지 않는다.

## 16. Stage artifact

```text
model-input image(s)
provider-request manifest
provider-response summary
raw mesh
raw texture(s)
raw validation report
repaired mesh
repair report
canonical transform
canonical renders
reconstruction result manifest
```

secret, signed URL과 provider raw auth header는 artifact에 넣지 않는다.

## 17. 완료 조건

- relief route가 fixture에서 watertight mesh를 생성함
- primary adapter가 공통 contract를 따름
- 24개 corpus benchmark와 license report가 있음
- raw invalid mesh가 voxelizer에 전달되지 않음
- raw/repaired provenance와 checksum이 있음
- canonical coordinate/ground fixture 통과
- repair output이 같은 입력에서 결정적임
- provider timeout/OOM/unavailable이 재시도·fallback policy대로 종료됨
- surface/solid capability가 report로 명시됨
