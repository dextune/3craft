# 3Craft 구현 상태 및 검증 증거

> 기준일: 2026-07-30
> 구현 판정: **실행 가능한 end-to-end local MVP vertical slice 완료**
> release 판정: **production/beta release 아님**

이 문서는 [`plan/README.md`](plan/README.md)의 목표와 현재 코드를 연결한다. 계획의 모든 production milestone을 완료했다고 주장하지 않으며, 이번 구현에서 실제로 실행·검증한 범위와 아직 검증하지 않은 범위를 분리한다.

## 1. 완료한 local vertical slice

```text
PNG/JPEG/WebP upload 또는 deterministic-dev 이미지 생성
  → SHA-256 provenance와 evidence class
  → canonical RGBA PNG, matte/depth SensePack
  → route-aware fail-closed sufficiency
  → deterministic 2.5D relief
  → 16/32/64 surface/hollow/solid voxel
  → versioned safe full-cube palette와 BOM
  → Sponge Schematic v3 / DataVersion 3700
  → semantic round-trip delivery gates
  → local async job API
  → React/Three.js preview와 `.schem` download
```

구현 경계는 다음과 같다.

| 영역 | 현재 구현 |
|---|---|
| 입력 | PNG/JPEG/WebP magic, decode, MIME, byte/pixel/frame 제한, EXIF orientation, canonical PNG |
| 증거 | upload=`observed`, generated=`design-intent`; generated/edited를 observed로 승격하지 못하는 invariant |
| Sense/sufficiency | alpha 또는 corner-background matte, depth proxy, diagnostics, `continue/ask/abort` |
| 생성 | 외부 호출 없는 `deterministic-dev`와 fail-closed `null` provider |
| 형상 | 결정적 2.5D relief; 실제 single-image AI mesh는 없음 |
| voxel | 최대 축 16/32/64, surface/hollow/solid, semantic hash |
| palette/export | `java-safe-v1` concrete palette, Lab/CIE76 mapping, BOM, gzip NBT Sponge v3 |
| 검증 | 자체 NBT reader와 독립 `nbtlib==2.0.4`, DataVersion/semantic/BOM gate |
| backend | FastAPI, process-local `ThreadPoolExecutor`, idempotency, polling/cancel, private local artifacts |
| frontend | React 19, strict TypeScript, Vite, lazy Three.js viewer, palette별 `InstancedMesh`, layer control |
| 실행 | CLI와 loopback-only API/Web launcher; runtime directory `0700`, files `0600` |

## 2. 계획 milestone 매핑

상태는 계획 milestone 전체가 아니라 현재 local adapter에 대한 이행 정도다.

| Milestone | 상태 | 완료한 부분 | 남은 핵심 항목 |
|---|---|---|---|
| M0 Bootstrap | 부분 완료 | Python/Node skeleton, exact direct dependencies, npm lockfile, test/build scripts, Java 1.20.4/DataVersion 3700 결정 | Postgres/Redis/S3 local stack, generated contract package, Accepted ADR/inventory |
| M1 Deterministic slice | local 완료 | provenance→SensePack→relief→voxel→Sponge v3→parser→viewer, deterministic hash, 외부 AI/GPU 불필요 | 실제 browser visual golden/capture |
| M2 Intake/sufficiency | local 부분 완료 | upload/generated 공통 contract, canonicalization, private filesystem, heuristic matte/depth, fail-closed sufficiency | signed upload, owner scope, production segmentation/provider, retention |
| M3 Reconstruction model | 미구현 | relief fallback과 provider boundary만 존재 | model/license/VRAM corpus spike, mesh ingest/repair, primary/fallback ADR |
| M4 Voxel/export | local 부분 완료 | 16/32/64×3 modes, safe palette, BOM JSON, Sponge v3, semantic delivery gates | binary/RLE TS codec, CSV, morphology/dithering, 실제 WorldEdit matrix |
| M5 Durable jobs | local adapter만 완료 | state/progress, request hash/idempotency, terminal persistence, safe download gate, polling/cancel | DB/outbox/Redis, lease/fencing/recovery, SSE, auth, retention, observability |
| M6 Product UI/viewer | local 부분 완료 | upload/generate, sufficiency, settings, polling, viewer/BOM/download, instancing, layer/camera, dispose/fallback | Web Worker/binary codec, persisted reconnect, canonical capture, browser/FPS matrix |
| M7 Security/operations | 미구현 | loopback binding, CORS allowlist, input/path limits, private permissions만 적용 | auth/CSRF/IDOR/quota/sandbox, containers/staging, alerts/backup/rollback |
| M8 Beta hardening | 미구현 | local automated regression과 한 fixture benchmark만 존재 | full corpus/golden/browser/Minecraft/load/incident/release matrix |

## 3. 검증 증거

### 3.1 Python과 API

최종 전체 실행:

```text
.............................                                            [100%]
29 passed
```

검증 범위:

- canonical JSON/hash, evidence invariant와 settings validation
- corrupt/MIME mismatch/tiny/empty image의 fail-closed 처리
- 16/32/64 및 surface/hollow/solid 의미와 결정성
- VarInt 경계, Sponge v3 deterministic writer와 손상 입력
- 자체 reader와 독립 `nbtlib` semantic parse
- delivery gate와 BOM/semantic hash 일치
- job completion/failure persistence, idempotency conflict, missing asset 즉시 거절
- API upload/generation/conversion/poll/artifact와 private response header
- null provider 503, malformed ID, path escape, filesystem permission
- CLI generate→convert→independent schematic parse

일반 isolated venv를 임시로 새로 만든 뒤 `pip install -e '.[dev]'`, console entrypoint, 동일 29 tests도 재현했다. 현재 유일한 warning은 Starlette 1.3.1이 기존 `httpx` TestClient backend 대신 `httpx2` 설치를 권고하는 third-party deprecation이다. 제품 코드 warning이나 test failure는 아니다.

### 3.2 Frontend

lockfile 기반 clean install과 strict build:

```text
npm ci: added 39 packages
TypeScript: tsc --noEmit 성공
Vite 8.2.0: 23 modules transformed
initial app JS: 203.12 kB (gzip 64.57 kB)
lazy VoxelViewer JS: 551.71 kB (gzip 138.02 kB)
npm audit --omit=dev: found 0 vulnerabilities
```

Three.js chunk는 결과가 생길 때 `React.lazy`로 로드된다. 실제 GPU별 렌더 품질/FPS는 이 검증에 포함되지 않았으며 typecheck, production build, lifecycle 정적 감사까지만 완료했다.

### 3.3 실제 process/HTTP E2E

`./scripts/dev.sh`로 Uvicorn과 Vite를 실제 실행해 다음을 확인했다.

```text
deterministic generation → canonical source image
→ 16-axis hollow conversion → async polling completed
→ preview/BOM/schematic download → independent nbtlib parse
```

관찰값:

| 항목 | 결과 |
|---|---:|
| dimensions | 11×16×4 |
| occupied blocks | 265 |
| block types | 9 |
| `.schem` bytes | 547 |
| Schematic version | 3 |
| DataVersion | 3700 |
| preview/schematic privacy | `Cache-Control: private, no-store`, `nosniff` |
| Vite binding | `127.0.0.1:5173`, strict port |
| Web root | HTTP 200, React root 확인 |
| launcher 종료 | 5173/8000 listener와 child process 모두 해제 |

설치된 `threecraft` executable로 `--help`, nested output generation, conversion, `serve`, custom `--data-dir` 적용과 `0700` mode도 별도로 통과했다.

### 3.4 Baseline benchmark

환경: Python 3.12.3, Linux 6.8 x86_64, logical CPU 16. `tracemalloc`을 켠 단일 deterministic fixture의 local diagnostic baseline이며 SLA가 아니다.

| Axis | Fill | Time | Python peak | Blocks | Schematic |
|---:|---|---:|---:|---:|---:|
| 16 | surface | 50.47 ms | 0.37 MiB | 118 | 505 B |
| 16 | hollow | 71.71 ms | 0.35 MiB | 265 | 547 B |
| 16 | solid | 81.55 ms | 0.36 MiB | 350 | 524 B |
| 32 | surface | 131.50 ms | 0.81 MiB | 468 | 696 B |
| 32 | hollow | 255.81 ms | 0.82 MiB | 1,158 | 861 B |
| 32 | solid | 478.35 ms | 1.38 MiB | 2,587 | 775 B |
| 64 | surface | 573.66 ms | 5.51 MiB | 1,908 | 1,459 B |
| 64 | hollow | 1,244.03 ms | 6.14 MiB | 4,961 | 1,944 B |
| 64 | solid | 3,727.19 ms | 10.24 MiB | 20,383 | 1,726 B |

9개 조합 모두 다섯 delivery gate가 `true`였고 worker OOM은 없었다. 이 수치는 fixture·hardware별 benchmark corpus를 대체하지 않는다.

## 4. 자체 감사에서 발견하고 수정한 항목

이번 검증은 single-agent 직접 감사로 진행했으며 multi-agent 또는 독립 reviewer 검토는 포함하지 않았다. 대신 source-scoped 위험 패턴 검색, 직접 lifecycle/API audit, clean install과 실제 process smoke를 수행했다.

- Vite `0.0.0.0` LAN 노출 → loopback-only
- port 점유 시 5174로 silent fallback → `--strictPort`
- npm parent 종료 뒤 orphan Vite process → Vite process 직접 관리와 종료 검증
- direct Vite 실행 root 404 → `apps/web` root 명시
- `GridHelper`와 per-rebuild `InstancedMesh` dispose 누락 → 명시적 dispose
- API module import 시 app/job manager 중복 생성 → entrypoint에서 한 번만 factory 호출
- 존재하지 않는 source asset이 job 생성 뒤 실패 → enqueue 전 동기 404
- 기존 artifact root가 permissive mode일 수 있음 → startup 시 `0700` 강제
- 예상 밖 worker exception traceback 유실 → server-side exception logging
- preview/BOM/schematic privacy header 부재 → private/no-store/nosniff

애플리케이션 Python/TypeScript source에서 TODO/FIXME, 동적 `eval`/`exec`, shell execution, DOM injection, credential storage 패턴은 발견되지 않았다. 이는 전문 penetration test나 독립 보안 감사를 대체하지 않는다.

## 5. 통과한 local delivery gate

- 입력 decode/canonicalization/provenance/sufficiency가 성공해야 conversion 가능
- 지원 해상도와 fill mode만 계약에서 허용
- palette index 0은 air이며 occupied block에 사용할 수 없음
- 좌표 bounds와 semantic hash invariant 검증
- Sponge root/version/DataVersion/palette/VarInt/index order parse
- writer→reader semantic hash와 BOM 일치
- 모든 gate가 통과한 completed job만 artifact download 가능
- malformed identifier/path escape 거절
- generated asset을 observed evidence로 표시하지 않음

## 6. 아직 완료하지 않은 release gate

다음 항목이 남아 있으므로 production readiness나 계획 전체 완료로 해석하면 안 된다.

1. 실제 AI image generation 및 single-image/multi-view mesh reconstruction
2. model license/data policy, 20~24개 corpus, VRAM/quality benchmark
3. Postgres/Redis/S3, lease/fencing/retry/recovery와 multi-process durability
4. auth, tenant owner scope, signed upload/download, quota/rate/retention
5. SSE, binary voxel codec, Web Worker와 persisted reconnect
6. 실제 browser/WebGL GPU·접근성·FPS·leak 자동화 matrix
7. 실제 Minecraft Java 1.20.4 + WorldEdit 수동 import matrix
8. production containers, staging, observability, backup/restore/rollback/load/incident drill
9. 독립 code/security review와 release sign-off

## 7. 재현 명령

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
npm --prefix apps/web ci
make check
./scripts/dev.sh
```

CLI smoke:

```bash
.venv/bin/threecraft generate "blue crystal guardian" --out generated.png
.venv/bin/threecraft convert generated.png --max-axis 16 --fill hollow --out output
```
