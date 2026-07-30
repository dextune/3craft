# Voxelization, Block Palette와 Schematic Export

## 1. 목표

정규화된 mesh를 목표 block 해상도로 변환하고, 관찰 가능한 색과 사용자 제약을 Minecraft block state에 대응시킨 뒤, 게임 도구가 읽을 수 있는 구조 파일을 생성한다. 이 단계는 AI 결과와 달리 동일 입력·설정·version에서 결정적이어야 한다.

## 2. 내부 좌표계 불변조건

- right-handed canonical mesh를 입력으로 받는다.
- voxel index `x`, `y`, `z`는 0 이상 정수다.
- `+Y`는 위다.
- `Y=0`은 ground layer다.
- voxel cell과 voxel center 좌표를 구분한다.
- dimensions는 occupied bounding box가 아니라 전체 grid shape다.
- export adapter만 Minecraft format의 선형화/offset/축 변환을 담당한다.

필수 primitive fixture:

- 1×1×1 cube
- 2×3×4 rectangular prism
- 음수 좌표에 있는 mesh
- 경계에 정확히 닿는 triangle
- 회전된 비대칭 mesh
- 한 voxel보다 얇은 plane/rod

## 3. Resolution과 scale

MVP mode는 `max-axis`다.

```text
mesh extents = (ex, ey, ez)
target max axis = N
usable cells = N - configured margin
scale = usable cells / max(ex, ey, ez)
```

구현 시 center/cell boundary와 rasterization 규칙 때문에 `N` 또는 `N-1`을 임의로 선택하지 않는다. primitive fixture에서 정확한 dimensions를 먼저 고정한다.

정책:

- 16: 빠른 preview와 큰 실루엣
- 32: 기본값
- 64: 높은 비용/메모리 경고
- 128: benchmark와 admission gate 전 비공개

원본 비율을 유지한다. 사용자가 width/height를 각각 강제로 지정하는 비균일 scale은 MVP에서 지원하지 않는다.

## 4. Occupancy 생성

### 4.1 Surface mode

mesh와 교차하거나 표면 거리 threshold 안에 있는 cell을 채운다.

구현 후보:

- triangle-box overlap rasterization
- signed/unsigned distance field threshold
- conservative voxelization

요구사항:

- watertight가 아니어도 동작
- 한 voxel보다 얇은 feature를 가능한 한 보존
- triangle 순서에 독립적
- 중복 hit가 결과에 영향을 주지 않음
- surface crack 진단

### 4.2 Solid mode

inside/outside를 판정해 내부를 모두 채운다.

우선순위:

1. watertight mesh의 robust winding/inside test
2. repair된 mesh
3. 정책이 허용하면 flood-fill 기반 exterior 구분
4. 실패 시 surface로 downgrade 요청 또는 abort

ray parity만 사용할 경우 vertex/edge 교차와 방향 편향 fixture를 반드시 둔다. 여러 축의 판정을 결합하거나 검증된 geometry library를 사용한다.

### 4.3 Hollow mode

solid occupancy에서 내부를 제거하여 일정 shell thickness를 만든다.

```text
solid mask
→ interior distance/erosion
→ distance >= shellThickness인 내부 제거
→ shell 연결성과 hole 검사
```

`hollow`는 단순 surface와 다르다. 닫힌 외피를 목표로 하며, shell thickness와 내부 접근용 opening은 별도 옵션이다.

### 4.4 Fill policy

- surface voxel: 색상 기반 block
- solid 내부: configurable filler 또는 surface block propagation
- hollow 내부: air
- filler는 BOM에서 별도 구분
- 중력/투명 filler 금지

## 5. Topology와 morphology 정리

처리 순서를 pipeline version으로 고정한다.

1. occupancy 생성
2. connected component labeling
3. tiny component 평가
4. 제한적 closing/fill hole
5. 최소 두께 적용
6. diagonal-only connection 정책
7. floating component 진단
8. ground alignment
9. final bounds crop/pad

### 5.1 Component 유지

가장 큰 component만 남기는 단순 정책은 손잡이·귀·장식을 삭제할 수 있다. 다음 점수를 사용한다.

- component voxel 수와 비율
- main component까지 거리
- source silhouette 기여
- mesh component provenance
- 입력 edge/feature와 겹침
- target resolution

삭제된 component 목록과 count를 report에 기록한다.

### 5.2 최소 두께

얇은 feature를 무조건 두껍게 만들면 형태가 바뀐다. 정책:

- user-controlled `preserveThinFeatures`
- source edge evidence가 있는 component 우선
- 최대 expansion distance 제한
- 적용 전후 silhouette metric
- 적용 voxel 수와 feature ID 기록

## 6. Mesh 색상에서 surface sample

surface voxel마다 대표 surface point, normal과 color evidence를 만든다.

우선순위:

1. 가장 가까운 triangle의 UV texture sample
2. barycentric vertex color
3. material base color
4. visible source projection
5. inferred hidden-surface policy
6. neutral fallback

여러 triangle이 한 voxel에 걸리면 면적, normal alignment와 sample confidence를 이용해 aggregate한다. sRGB 값을 바로 평균하지 않고 linear RGB에서 집계 후 perceptual 비교 색공간으로 변환한다.

hidden side policy:

- symmetry projection
- nearest observed surface color
- dominant palette color
- neutral block

정책과 confidence를 기록하며 observed color처럼 표시하지 않는다.

## 7. Minecraft Block Palette

### 7.1 기본 profile

- `safe-basic`: 불투명 full cube, block entity 없음
- `color-rich`: concrete/wool/terracotta 계열, 색상 표현 우선
- `natural`: stone/wood/soil 계열
- `survival-friendly`: 획득성 metadata 기반
- `custom`: allow/deny list 기반 후속 기능

MVP default는 `safe-basic`이다.

### 7.2 Entry 정보

- canonical block state
- display name/localization key
- target edition/version 범위
- top/side/bottom representative color
- opacity/alpha
- full cube 여부
- gravity
- block entity 요구
- emissive
- placement support 요구
- survival/cost/rarity tag
- enabled-by-default
- source와 license note

### 7.3 기본 제외

- water/lava/fire
- 작물과 성장 상태
- chest/sign/banner 등 block entity
- command/structure/technical block
- sand/gravel 등 gravity block
- door/bed/tall plant처럼 multi-block state
- rail/redstone처럼 neighbor semantics가 큰 block
- shape가 full cube가 아닌 stair/slab/fence

후속에 추가할 때 placement validator가 필요하다.

## 8. Color mapping

### 8.1 Candidate filter

먼저 user/profile/target version 제약으로 candidate를 줄인다. 금지 block은 큰 penalty가 아니라 후보에서 제거한다.

### 8.2 비용 함수

```text
cost =
  perceptual_color_distance
  + face_orientation_penalty
  + transparency_penalty
  + rarity_or_cost_penalty
  + neighborhood_speckle_penalty
  + inferred_color_penalty
```

기본 mapping은 각 voxel의 source normal에 따라 top/side/bottom 대표색을 선택한다. color metric과 weight는 palette mapper version에 포함한다.

### 8.3 Neighborhood regularization

nearest color만 쓰면 한두 block speckle이 발생한다. 선택적 후처리:

- 작은 고립 색 component 통합
- palette 종류 상한
- edge evidence가 강한 위치는 색 경계 보존
- source color error 증가량 제한

### 8.4 Dithering

- default off
- surface에만 적용
- deterministic scan order
- component와 실루엣 경계를 넘지 않음
- error diffusion 또는 ordered pattern version 기록
- 적용 전후 color error, block 다양성과 speckle count 비교

## 9. 구조 진단

필수 통계:

- dimensions
- occupied/surface/interior count
- block state별 count
- component count
- floating component/block count
- ground contact area
- unsupported gravity placement
- invalid/missing block state
- empty layers
- palette diversity
- inferred color 비율
- mesh→voxel silhouette loss

fatal:

- dimensions/data length 불일치
- palette index out of range
- target version invalid block
- block count 0
- configured maximum 초과
- semantic hash 생성 실패

warning:

- multiple components
- low ground contact
- 많은 floating block
- 높은 inferred color 비율
- 큰 silhouette loss

## 10. Voxel preview encoding

초기 debug JSON과 production binary를 구분한다.

production 제안:

```text
header:
  magic
  encodingVersion
  width/height/length
  paletteCount
  palette table length
body:
  canonical palette strings
  occupancy/block index RLE 또는 chunk stream
footer:
  checksum
```

요구사항:

- browser와 Python decoder golden fixture 공유
- bounds/length를 decode 전에 검증
- decompression bomb 방지
- transferable typed array 사용
- semantic hash는 압축 방식과 무관
- layer access를 위해 chunk 또는 y-slice index 고려

## 11. Schematic export

### 11.1 Target

MVP target은 Sponge Schematic v3 계열 `.schem`이다. 세부 NBT field와 block data 선형화는 구현 시 공식 format 문서와 독립 parser를 기준으로 한다. 기억이나 예제 한 개만 보고 writer를 만들지 않는다.

### 11.2 Export adapter 책임

- internal axis→Minecraft axis 변환
- width/height/length와 offset
- target DataVersion
- canonical block state palette
- palette index stream/VarInt encoding
- air 처리
- metadata
- compression
- optional block entities 없음 확인

### 11.3 Deterministic ordering

- palette entry 정렬 규칙 고정
- voxel traversal order 고정
- metadata key와 serializer 고정
- timestamp가 byte hash를 흔들면 semantic hash에서 분리
- 동일 VoxelModel/target/exporter version은 동일 semantic output

### 11.4 Offset와 grounding

기본 구조 origin은 occupied bounds의 최소점이며 ground layer `y=0`을 유지한다. paste position과 구조 offset의 의미를 실제 WorldEdit fixture로 검증한다. 회전은 export 직전 임의로 수행하지 않고 VoxelModel transform 단계에서 결정한다.

## 12. BOM과 delivery bundle

BOM JSON:

- target version
- dimensions
- total occupied
- block state별 count
- filler count
- palette profile/version
- warnings
- semantic hash

CSV는 사용자 편의를 위한 derived artifact다.

bundle:

```text
model.schem
blocks.json
blocks.csv
preview.vox
thumbnail.png
manifest.json
README-import.txt
```

source image와 internal diagnostic은 기본 delivery bundle에 포함하지 않는다.

## 13. Export validation gates

- `GATE-VOX-001`: VoxelModel schema valid
- `GATE-VOX-002`: non-empty and within dimensions/count limit
- `GATE-VOX-003`: palette indices valid
- `GATE-VOX-004`: block states target-compatible
- `GATE-EXP-001`: NBT decompress/parse 성공
- `GATE-EXP-002`: format version/DataVersion/dimensions 일치
- `GATE-EXP-003`: independent parser semantic round-trip
- `GATE-EXP-004`: coordinate별 block state가 VoxelModel과 일치
- `GATE-EXP-005`: BOM count 일치
- `GATE-EXP-006`: 금지 block/block entity 없음
- `GATE-EXP-007`: bundle leak/UTF-8/path 검사
- `GATE-EXP-008`: target WorldEdit smoke fixture 성공

hard gate 하나라도 실패하면 schematic을 `published`로 만들지 않는다.

## 14. 테스트 fixture

- one stone block
- 2×2×2 single block cube
- asymmetric two-color shape
- internal air cavity
- hollow shell
- disconnected accessory
- negative mesh coordinates
- palette index가 여러 byte를 요구하는 구조
- 16/32/64 boundary
- rotation/axis marker shape
- invalid target block
- gravity block unsupported placement
- unicode display name
- BOM count mismatch corruption
- truncated/invalid NBT

## 15. 완료 조건

- surface/hollow/solid가 문서 정의대로 fixture를 생성함
- 동일 repaired mesh/settings에서 semantic hash가 고정됨
- Lab 계열 또는 승인된 perceptual mapping benchmark가 있음
- safe palette가 target version validator를 통과함
- preview Python/TS decoder가 같은 semantic data를 읽음
- `.schem` round-trip이 좌표별로 일치함
- 실제 WorldEdit smoke가 지원 matrix에서 통과함
- invalid export가 사용자에게 공개되지 않음
