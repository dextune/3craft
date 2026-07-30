# Third-party notices

3Craft 자체 코드는 [MIT License](LICENSE)로 배포됩니다. 이 문서는 직접 사용하는 주요 dependency와 설계 참고 자료를 알리기 위한 요약이며, 각 package가 배포하는 license 원문과 lockfile이 최종 기준입니다. Transitive dependency는 `apps/web/package-lock.json`과 설치된 Python distribution metadata를 확인하세요.

## Runtime dependencies

| Component | Pinned version | License |
|---|---:|---|
| FastAPI | 0.136.1 | MIT |
| Pillow | 12.2.0 | HPND |
| Pydantic | 2.13.4 | MIT |
| python-multipart | 0.0.32 | Apache-2.0 |
| Uvicorn | 0.47.0 | BSD-3-Clause |
| React / React DOM | 19.2.8 | MIT |
| Three.js | 0.185.1 | MIT |

## Development and build dependencies

| Component | Pinned version | License |
|---|---:|---|
| setuptools | 83.0.0 | MIT |
| httpx | 0.28.1 | BSD-3-Clause |
| nbtlib | 2.0.4 | MIT |
| pytest | 9.1.0 | MIT |
| Vite | 8.2.0 | MIT |
| TypeScript | 7.0.2 | Apache-2.0 |
| @vitejs/plugin-react | 6.0.5 | MIT |
| @types/react, @types/react-dom, @types/three | pinned in `package.json` | MIT |

## Architectural reference

The planning phase studied [dextune/gpthreejs](https://github.com/dextune/gpthreejs) 0.2.0 (MIT) as an architectural reference. 3Craft adapts evidence classification, canonical hashing, sufficiency gating, fail-closed delivery and Three.js disposal patterns. It does not reuse the character blueprint, procedural geometry emitter or `createXxxForm.ts` output model. See [`docs/plan/01-gpthreejs-analysis.md`](docs/plan/01-gpthreejs-analysis.md) for the detailed analysis.

Minecraft is a trademark of Microsoft Corporation. 3Craft is an independent project and is not affiliated with or endorsed by Mojang Studios or Microsoft.
