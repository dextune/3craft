# 변경 기록

이 프로젝트는 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/) 형식을 따르며, 안정적인 공개 API가 정해지기 전까지 변경은 `Unreleased`에 기록합니다.

## [Unreleased]

### Added

- PNG/JPEG/WebP upload와 deterministic development image generation
- provenance, canonicalization, SensePack와 fail-closed sufficiency
- 16/32/64 surface/hollow/solid deterministic relief voxelization
- Java-safe concrete palette, BOM과 Sponge Schematic v3 export
- FastAPI local async jobs, CLI와 React/Three.js preview
- 독립 `nbtlib` semantic validation과 29-test regression suite
- GitHub CI, contribution/security policy와 issue/PR templates

### Known limitations

- 실제 AI image/mesh reconstruction 미구현
- production DB/queue/object storage/auth 미구현
- 실제 Minecraft/WorldEdit 및 browser GPU matrix 미검증

상세 구현 상태는 [`docs/implementation-status.md`](docs/implementation-status.md)를 참고하세요.
