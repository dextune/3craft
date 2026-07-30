# 3Craft 기여 가이드

3Craft에 관심을 가져주셔서 감사합니다. 현재 저장소는 이미지에서 Minecraft Java Edition용 2.5D relief와 Sponge v3 `.schem`을 만드는 **local MVP**입니다. 실제 AI mesh reconstruction이나 production multi-tenant service로 오해될 변경은 받지 않습니다.

## 시작하기

요구 사항:

- Python 3.12+
- Node.js 20.19+, 22.12+ 또는 24+
- npm

개발 환경:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
npm --prefix apps/web ci
make check
```

로컬 API와 Web을 함께 실행하려면 다음을 사용합니다.

```bash
./scripts/dev.sh
```

두 server는 loopback에만 bind합니다. runtime artifact는 `.threecraft-data/`에 저장되며 Git에 포함하면 안 됩니다.

## Issue와 보안 보고

- 재현 가능한 bug와 일반 feature 제안은 GitHub Issue template을 사용해 주세요.
- 취약점, path traversal, malicious upload bypass, artifact disclosure 가능성은 공개 Issue에 작성하지 말고 [보안 정책](SECURITY.md)을 따라 주세요.
- 실제 AI provider, hosted storage 또는 외부 URL fetch를 추가하는 변경은 data policy, license, cost와 egress 검토가 먼저 필요합니다.

## 핵심 불변조건

변경 시 다음 계약을 유지해야 합니다.

1. generated/edited asset을 `observed` evidence로 표시하지 않습니다.
2. invalid input, sufficiency blocker 또는 delivery gate 실패 시 결과 다운로드를 공개하지 않습니다.
3. semantic hash는 palette index 순서가 아니라 block state와 좌표 의미를 반영합니다.
4. palette index 0은 `minecraft:air`이며 occupied block에 사용할 수 없습니다.
5. 지원되는 export는 Java 1.20.4/DataVersion 3700의 Sponge Schematic v3입니다.
6. frontend는 block마다 React component를 만들지 않고 instancing을 사용합니다.
7. Three.js geometry, material, controls, observer와 animation loop를 명시적으로 정리합니다.
8. 임의 URL image fetch, secret 하드코딩과 사용자 파일의 외부 전송을 추가하지 않습니다.

## 변경 절차

1. 관련 Issue가 있으면 먼저 연결합니다.
2. 한 변경에는 한 가지 목적을 유지합니다.
3. 동작이나 계약을 바꾸면 테스트와 문서를 같은 변경에 포함합니다.
4. source file만 stage하고 `.venv`, `node_modules`, `dist`, runtime artifact를 제외합니다.
5. PR 본문에 검증 명령과 결과, 알려진 한계 및 보안 영향을 적습니다.

권장 commit 형식은 `type(scope): summary`입니다. 예:

```text
feat(export): validate Sponge v3 block data
fix(viewer): dispose instanced resources on rebuild
docs(readme): clarify local MVP limitations
```

## 필수 검증

최소 검증:

```bash
.venv/bin/python -m pytest -q
npm --prefix apps/web run build
```

dependency나 설치 절차를 바꿨다면 clean venv와 `npm ci`에서도 재현해야 합니다. Schematic 변경은 자체 reader뿐 아니라 독립 `nbtlib` parse를 통과해야 합니다.

## 문서

- [현재 구현 상태와 검증 증거](docs/implementation-status.md)
- [전체 제품·기술 계획](docs/plan/README.md)
- [보안 정책](SECURITY.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)

기여를 제출하면 해당 기여물을 저장소의 [MIT License](LICENSE)로 배포하는 데 동의하는 것으로 간주합니다.
