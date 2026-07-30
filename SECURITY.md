# 3Craft 보안 정책

## 지원 범위

3Craft는 현재 인증이나 tenant isolation이 없는 **local MVP**이며 production service가 아닙니다.

| 대상 | 보안 수정 |
|---|---|
| GitHub default branch의 최신 코드 | 지원 |
| 이전 commit, fork 또는 변경된 배포 | 지원하지 않음 |
| 공개 release artifact | 아직 제공하지 않음 |

## 배포 주의사항

- API와 Vite는 기본 설정처럼 `127.0.0.1`에만 bind하세요.
- 현재 API를 인터넷, 공용 LAN 또는 신뢰할 수 없는 multi-user 환경에 노출하지 마세요.
- production 배포 전 auth, owner scope, CSRF/IDOR 방어, rate limit, quota, retention 및 object storage authorization이 필요합니다.
- `.threecraft-data/`와 업로드 이미지는 private data로 취급하고 공유 저장소에 commit하지 마세요.
- 실제 provider adapter를 구현하기 전에는 `THREECRAFT_IMAGE_PROVIDER=null`을 사용하세요.

구현된 방어와 남은 release gate는 [구현 상태 문서](docs/implementation-status.md)에 기록되어 있습니다.

## 취약점 보고

취약점은 공개 Issue에 작성하지 마세요. 저장소의 **Security → Report a vulnerability**에서 private security advisory를 생성해 주세요.

보고서에는 가능한 범위에서 다음을 포함해 주세요.

- 영향을 받는 commit 또는 버전
- 재현 조건과 최소 단계
- 기대 동작과 실제 동작
- 영향 범위와 공격 전제
- 가능한 완화책

실제 secret, 개인 이미지 또는 개인정보를 첨부하지 말고 안전한 fixture로 대체하세요. 보고 내용은 수정과 공개 시점이 합의될 때까지 비공개로 다룹니다. 현재는 응답 SLA를 보장하지 않지만 확인 가능한 보고는 우선 검토합니다.

## 주요 관심 영역

특히 다음 문제를 중요하게 다룹니다.

- image parser/decompression bomb 또는 validation bypass
- artifact ID/path traversal과 private file disclosure
- incomplete job artifact의 조기 공개
- generated evidence를 observed로 오분류하는 provenance bypass
- schematic parser/writer의 bounds 또는 VarInt 처리 오류
- Vite proxy나 CORS를 통한 의도하지 않은 network exposure
- dependency supply-chain 문제

일반 bug와 feature 요청은 GitHub Issue template을 사용해 주세요.
