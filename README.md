# 3Craft

[![CI](https://github.com/dextune/3craft/actions/workflows/ci.yml/badge.svg)](https://github.com/dextune/3craft/actions/workflows/ci.yml)
[MIT License](LICENSE)

이미지를 **Minecraft Java Edition 블록 조형물**로 변환하고, 브라우저 미리보기·재료 목록(BOM)·Sponge Schematic v3 `.schem`을 제공하는 실행 가능한 local MVP입니다.

> [!IMPORTANT]
> 현재 구현은 결정적인 **2.5D relief pipeline**입니다. 실제 AI image generation이나 single-image 360° mesh reconstruction을 구현한 것처럼 표시하지 않습니다. 생성 탭의 `deterministic-dev`는 외부 AI가 아닌 로컬 procedural fixture provider입니다.

## 주요 기능

```text
PNG/JPEG/WebP 업로드 또는 deterministic-dev 이미지 생성
  → SHA-256 provenance와 observed/design-intent 구분
  → canonical RGBA PNG + matte/depth SensePack
  → route-aware fail-closed sufficiency
  → 16/32/64 relief voxel (surface/hollow/solid)
  → Java-safe full-cube palette + BOM
  → Sponge Schematic v3 / DataVersion 3700
  → 자체 reader + 독립 nbtlib semantic 검증
  → FastAPI async local job + React/Three.js preview
```

| 영역 | 구현 |
|---|---|
| 입력 | PNG/JPEG/WebP magic, MIME, decode, EXIF, byte/pixel/frame validation |
| provenance | upload=`observed`, generated=`design-intent`, canonical SHA-256 |
| voxel | 16/32/64축, surface/hollow/solid, deterministic semantic hash |
| Minecraft | Java 1.20.4, DataVersion 3700, Sponge Schematic v3 |
| backend | FastAPI, process-local worker, private local artifact store |
| frontend | React, strict TypeScript, lazy Three.js `InstancedMesh` viewer |
| 도구 | Web UI, CLI, API/OpenAPI, BOM, `.schem` download |

구현 milestone과 실제 검증 출력은 [구현 상태 및 검증 증거](docs/implementation-status.md)를 참고하세요.

## 빠른 시작

### 요구 사항

- Python 3.12+
- Node.js 20.19+, 22.12+ 또는 24+
- npm
- Linux/macOS shell (`scripts/dev.sh` 기준; 검증 환경은 Linux)

### 설치

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
npm --prefix apps/web ci
```

### 실행

```bash
./scripts/dev.sh
```

- Web: <http://127.0.0.1:5173>
- API/OpenAPI: <http://127.0.0.1:8000/docs>
- Health: <http://127.0.0.1:8000/api/v1/health>

API와 Web은 loopback에만 bind합니다. 5173 또는 8000 port가 이미 사용 중이면 다른 port로 자동 이동하지 않고 실패하며, launcher 종료 시 두 child process를 정리합니다.

> [!WARNING]
> 현재 API에는 production 인증·tenant isolation·rate limit이 없습니다. 인터넷이나 신뢰할 수 없는 LAN에 노출하지 마세요. 자세한 내용은 [보안 정책](SECURITY.md)을 확인하세요.

별도 실행:

```bash
.venv/bin/python -m uvicorn services.api.main:app --host 127.0.0.1 --port 8000
npm --prefix apps/web run dev
```

runtime artifact는 기본적으로 `.threecraft-data/`에 directory `0700`, file `0600` 권한으로 저장되며 Git에서 제외됩니다.

## 사용법

### CLI 이미지 변환

```bash
.venv/bin/threecraft convert image.png \
  --max-axis 32 \
  --fill hollow \
  --out threecraft-output
```

출력 디렉터리에는 `model.schem`, `preview.json`, `blocks.json`, `delivery.json`이 생성됩니다.

### 개발용 이미지 생성

```bash
.venv/bin/threecraft generate \
  "blue crystal guardian" \
  --out generated-dev.png
```

### CLI로 API 실행

```bash
.venv/bin/threecraft --data-dir .threecraft-data serve
```

환경 변수는 [`.env.example`](.env.example)을 참고하세요. 실제 provider adapter를 검토·구현하기 전에는 `THREECRAFT_IMAGE_PROVIDER=null`로 generation을 비활성화할 수 있습니다.

## API 개요

| Method | Path | 설명 |
|---|---|---|
| `GET` | `/api/v1/health` | service health |
| `GET` | `/api/v1/capabilities` | 지원 strategy/provider/target |
| `POST` | `/api/v1/assets` | image upload/canonicalization |
| `GET` | `/api/v1/assets/{id}` | provenance/SensePack/sufficiency |
| `GET` | `/api/v1/assets/{id}/image` | private canonical source image |
| `POST` | `/api/v1/image-generations` | deterministic-dev image generation |
| `POST` | `/api/v1/conversions` | async conversion 생성 |
| `GET` | `/api/v1/jobs/{id}` | progress/terminal state polling |
| `POST` | `/api/v1/jobs/{id}/cancel` | safe cancellation 시도 |
| `GET` | `/api/v1/jobs/{id}/{preview\|bom\|schematic}` | 검증된 artifact |

정확한 request/response schema는 실행 중인 OpenAPI 문서에서 확인할 수 있습니다.

## 검증

```bash
make check
```

또는 개별 실행:

```bash
.venv/bin/python -m pytest -q
npm --prefix apps/web run build
```

현재 기준은 Python **29 tests**, clean `npm ci`, strict TypeScript/Vite build, 실제 local HTTP/CLI smoke와 독립 `nbtlib` parse입니다. CI는 push와 pull request에서 Python tests와 Web build를 실행합니다.

## 저장소 구조

```text
threecraft/                    Python domain, pipeline, API와 export
services/api/                  ASGI entrypoint
apps/web/                      React/Vite/Three.js frontend
tests/                         unit/integration/API/CLI tests
docs/implementation-status.md 현재 구현 범위와 검증 증거
docs/plan/                     제품·기술·운영 roadmap
scripts/dev.sh                 loopback-only local launcher
```

## 문서

- [구현 상태와 concrete 검증 증거](docs/implementation-status.md)
- [전체 제품·기술 계획](docs/plan/README.md)
- [변경 기록](CHANGELOG.md)
- [기여 가이드](CONTRIBUTING.md)
- [보안 정책](SECURITY.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)

## 현재 한계

- AI 기반 image generation과 360° mesh reconstruction은 아직 연결되지 않았습니다.
- Postgres, Redis, S3, durable retry/recovery와 production auth가 없습니다.
- 실제 Minecraft/WorldEdit 수동 import matrix는 production backlog입니다.
- 실제 browser/GPU별 WebGL 품질·FPS 자동화와 독립 보안 review는 수행하지 않았습니다.
- Java Edition 1.20.4/DataVersion 3700 및 safe concrete full-cube palette만 목표로 합니다.

production roadmap은 [계획 문서](docs/plan/README.md)와 [구현 상태 문서](docs/implementation-status.md)에 명시되어 있습니다.

## 기여와 라이선스

기여 전 [CONTRIBUTING.md](CONTRIBUTING.md)를 읽어 주세요. 보안 취약점은 공개 Issue 대신 [SECURITY.md](SECURITY.md)의 private reporting 절차를 사용하세요.

3Craft는 [MIT License](LICENSE)로 배포됩니다. Minecraft는 Microsoft Corporation의 상표이며, 3Craft는 Mojang Studios 또는 Microsoft와 제휴하거나 보증받은 프로젝트가 아닙니다.
