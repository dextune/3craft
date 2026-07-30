# Pull request

## 변경 요약

<!-- 무엇을 왜 변경했는지 설명해 주세요. -->

## 관련 Issue

<!-- 예: Closes #123 -->

## 검증

- [ ] `.venv/bin/python -m pytest -q`
- [ ] `npm --prefix apps/web run build`
- [ ] 변경에 필요한 targeted smoke/independent parser 검증

실행한 명령과 결과:

```text

```

## 계약 및 위험 검토

- [ ] provenance/evidence class 불변조건을 유지합니다.
- [ ] fail-closed delivery와 private artifact 정책을 유지합니다.
- [ ] user content, secret 또는 local runtime artifact를 포함하지 않습니다.
- [ ] dependency/provider 추가 시 버전, license, data egress와 cost를 검토했습니다.
- [ ] Three.js resource 또는 async polling을 추가했다면 cleanup을 검증했습니다.

## 문서와 호환성

- [ ] 사용자 동작이나 공개 계약 변경에 맞춰 문서를 갱신했습니다.
- [ ] Java 1.20.4/DataVersion 3700/Sponge v3 호환성 영향을 설명했습니다.
- [ ] 알려진 한계와 후속 작업을 기록했습니다.

## 스크린샷 또는 artifact 정보

<!-- 필요할 때만 첨부하고 개인 이미지나 private runtime artifact는 제거하세요. -->
