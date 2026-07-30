# Operations와 Release Runbook

## 1. 목적

이 문서는 개발·staging·production 환경의 실행 계약과 장애 대응, release/rollback을 정의한다. 실제 package command와 cloud resource 이름은 M0 구현 후 갱신한다. 명령이 확정되기 전 문서 예시를 그대로 production에서 실행하지 않는다.

## 2. 환경

### Local

- Vite web
- Python API
- Python worker
- Postgres
- Redis
- S3-compatible local storage
- fixture provider
- optional local GPU adapter

### CI

- ephemeral DB/queue/storage
- fake deterministic provider
- independent schematic parser
- headless Chromium
- scheduled GPU runner 별도

### Staging

- production과 동일 topology/권한 모델
- 별도 account/project/bucket/key
- 제한 quota
- non-sensitive fixture
- 실제 provider staging key

### Production

- stateless web/API
- CPU/GPU worker pool
- managed 또는 HA DB/queue/storage
- private network/least privilege
- centralized logs/metrics/traces
- backup/lifecycle/cost alert

환경 간 bucket, DB, provider key를 공유하지 않는다.

## 3. Configuration category

```text
Application
  ENVIRONMENT
  RELEASE_VERSION
  PUBLIC_BASE_URL
  LOG_LEVEL

Database
  DATABASE_URL
  POOL_SIZE

Queue
  QUEUE_URL
  JOB_LEASE_SECONDS
  HEARTBEAT_SECONDS
  MAX_ATTEMPTS

Storage
  STORAGE_ENDPOINT
  STORAGE_BUCKET
  SIGNED_URL_TTL_SECONDS

Providers
  IMAGE_PROVIDER
  IMAGE_PROVIDER_KEY
  RECON_PROVIDER
  RECON_MODEL_PROFILE
  MODEL_PATH/CHECKSUM

Pipeline
  PIPELINE_VERSION
  SUFFICIENCY_POLICY_VERSION
  DEFAULT_RESOLUTION
  MAX_RESOLUTION
  PALETTE_VERSION
  TARGET_MINECRAFT_VERSION
  TARGET_DATA_VERSION

Retention/Quota
  SOURCE_RETENTION_HOURS
  INTERMEDIATE_RETENTION_HOURS
  DELIVERY_RETENTION_HOURS
  MAX_ACTIVE_JOBS
  MAX_GPU_SECONDS
```

실제 변수는 typed settings로 시작 시 validation한다. secret과 public config를 분리한다.

## 4. Local bootstrap 계약

최종 repository script가 제공해야 할 논리 명령:

```text
bootstrap/install
dev:services
db:migrate
dev:web
dev:api
dev:worker
test
test:integration
test:e2e
lint
typecheck
build
smoke
```

시작 순서:

1. pinned runtime 확인
2. locked dependency install
3. local env 생성
4. DB/Redis/storage 시작
5. migration
6. private bucket/prefix 초기화
7. API readiness
8. fixture worker
9. web
10. vertical smoke

shutdown은 worker lease와 temp artifact를 정리하고 service volume을 임의 삭제하지 않는다.

## 5. Health endpoint

### API liveness

- process/event loop만 확인
- dependency 장애로 무한 restart하지 않음

### API readiness

- typed config
- DB query
- queue publish capability
- storage metadata access

### Worker liveness

- process와 heartbeat loop

### Worker readiness

- queue/storage 접근
- temp disk
- provider/model configuration
- model load 또는 lazy-load 상태
- GPU/VRAM sanity

image generation provider 장애를 upload/relief API 전체 readiness 실패로 취급하지 않고 capability health로 분리한다.

## 6. 배포 artifact

- web static/container artifact
- API container digest
- worker CPU/GPU container digest
- DB migration version
- contract schema version
- model identifier/weight checksum
- palette content hash
- target Minecraft/DataVersion
- release manifest/SBOM

runtime에 승인되지 않은 최신 model/dependency를 자동 다운로드하지 않는다.

## 7. 배포 순서

1. release commit/tag와 immutable artifact 생성
2. unit/integration/E2E/security scan
3. migration backward compatibility review
4. staging deploy
5. fixture smoke
6. actual provider/GPU smoke
7. schematic parser + WorldEdit smoke
8. dashboards/alerts 확인
9. canary API/worker
10. queue age/error/cost 관찰
11. full rollout
12. release note/known limitation 게시

worker와 queue payload compatibility를 먼저 본다. 새로운 worker가 기존 job을 읽지 못하면 versioned queue 또는 drain 계획이 필요하다.

## 8. Migration 원칙

- expand→migrate/backfill→contract
- rolling deploy 중 old/new code가 공존 가능
- destructive migration은 별도 승인/backup/rollback
- artifact schema와 DB schema를 혼동하지 않음
- large backfill은 online throttling
- migration metric과 lock time 관찰

## 9. Smoke test

### 일반

1. valid PNG upload
2. canonical asset ready
3. 16축 relief conversion
4. queued→completed event
5. preview/BOM
6. schematic download
7. independent parser
8. BOM equality
9. invalid upload reject
10. cross-owner deny
11. log secret 없음

### GPU

- 실제 single-image reconstruction 1건
- model/version/checksum 확인
- duration/VRAM
- raw/repaired mesh valid
- 후속 job 수신
- temp/GPU memory 정리

### Minecraft

- supported WorldEdit/Minecraft 환경에서 paste
- orientation/ground/offset
- expected block count spot check
- unsupported block 없음

## 10. Observability

### Logs

필드:

- timestamp/level/service/environment/release
- request/job/attempt/stage
- owner pseudonymous ID
- duration/resource
- provider/model/palette/target
- error code/retryable

redaction:

- API key/token/cookie
- signed URL
- prompt 전체 기본 제외
- image/mesh bytes
- 사용자 파일명 필요 이상 제외
- absolute temp path

### Metrics

API:

- request rate/latency/status
- DB pool
- upload/download bytes
- auth/rate limit

Queue/job:

- queue depth/oldest age
- state/stage count
- success/fail/cancel/retry
- stage duration
- lease expiry/stale attempt

Worker/provider:

- utilization/concurrency
- CPU/RAM/GPU/VRAM
- model load/inference
- provider latency/rate/error/cost
- OOM/restart

Artifact/export:

- storage bytes/count
- candidate orphan
- validation failure
- schematic size/block count
- download success

Viewer client telemetry는 사용자 콘텐츠 없이 load/decode/FPS/context error를 aggregate한다.

## 11. Alert

Critical:

- authorization/storage public exposure
- export validation 실패 급증
- DB unavailable/data integrity
- secret leak signal

High:

- oldest queue age SLO 초과
- worker OOM/restart loop
- provider failure spike
- storage write failure
- completion rate 급락
- 비용 budget 초과

Medium:

- 64 viewer performance regression
- retention backlog
- high retry/cancel
- low disk/temp capacity

alert는 owner, dashboard, runbook link와 severity를 포함한다.

## 12. Queue backlog runbook

진단:

1. queue별 depth/oldest
2. worker readiness/replica
3. GPU utilization/VRAM
4. stage/model/resolution 분포
5. provider rate limit
6. poison job/retry loop

대응:

- safe capacity 내 worker scale
- 64/고비용 admission 제한
- poison job 격리
- retry storm circuit breaker
- 사용자 status 공지
- 예상 복구 후 admission 점진 재개

무조건 replica를 늘려 provider rate limit/DB를 더 악화시키지 않는다.

## 13. GPU OOM runbook

진단:

- model/release/input resolution
- concurrent jobs
- 이전 job memory release
- driver/runtime
- input/output complexity

대응:

1. affected worker drain
2. 동시성 감소
3. 반복 job non-retryable 처리
4. lower profile/relief 제안
5. known-good worker image rollback
6. model/resource budget 수정은 benchmark/ADR 후

OOM job을 같은 설정으로 무한 retry하지 않는다.

## 14. Provider outage runbook

- provider status/rate-limit 확인
- circuit breaker open
- 신규 해당 capability job 제한
- queue retry storm 방지
- upload/relief/기존 download 유지
- 대체 provider는 결과 차이를 고지
- 복구 후 canary 요청
- 비용/중복 request audit

## 15. Storage/DB 장애

Storage:

- completed 전환 중단
- candidate/published 상태 확인
- partial multipart cleanup은 복구 후
- checksum으로 손상 확인

DB:

- API mutation admission 중단
- worker가 DB lease 없이 새 stage를 실행하지 않음
- 복구 후 lease/fencing 검사
- backup restore는 isolated 환경에서 검증 후 결정

데이터 삭제나 hard reset은 명시적 고위험 승인 없이 수행하지 않는다.

## 16. Export validation incident

1. 해당 exporter/release의 publish 즉시 제한
2. 이미 공개된 artifact 범위 식별
3. model/palette/DataVersion/serializer 기록
4. 실패 fixture와 parser report 보존
5. known-good exporter rollback
6. 사용자 영향/재생성 정책 결정
7. regression test 추가

reconstruction quality issue와 format corruption을 구분한다.

## 17. Retention과 orphan cleanup

cleanup 순서:

1. expiry candidate 조회
2. active job/reference/hold 제외
3. storage delete
4. delete 결과 확인
5. artifact tombstone
6. retry/alert

정기 orphan audit:

- object without DB row
- DB artifact without object
- writing/candidate 장기 정체
- expired signed upload
- incomplete multipart

삭제 전에 DB row를 완전히 없애면 orphan 추적이 어려우므로 tombstone을 유지한다.

## 18. Backup과 restore

- Postgres encrypted scheduled backup
- point-in-time 정책
- object version/lifecycle 또는 필요한 delivery backup
- config/schema/model/palette manifest 보존
- 분기별 restore drill 제안

restore 검증:

- owner/job/artifact 관계
- object checksum
- published download
- queue message는 복원 후 중복 실행되지 않음
- deleted/tombstone privacy 정책

## 19. Rollback

사전 질문:

- migration이 backward compatible한가?
- 새 queue/artifact schema가 이전 code와 호환되는가?
- 새 model/palette output을 이전 API가 읽는가?
- 진행 중 job을 drain해야 하는가?

절차:

1. 신규 고위험 job admission 제한
2. 영향/metric snapshot
3. worker canary/전체를 known-good digest로 rollback
4. API/web rollback
5. incompatible queue 격리
6. artifact validation
7. admission 점진 재개
8. incident timeline/postmortem

`git reset`, DB destructive down migration, storage bulk delete는 rollback 기본 수단이 아니다.

## 20. Release checklist

### Engineering

- [ ] lint/type/unit/contract
- [ ] integration/E2E
- [ ] web/API/worker build
- [ ] schema drift 없음
- [ ] schematic round-trip
- [ ] browser runtime/dispose

### Compatibility

- [ ] target Minecraft/DataVersion
- [ ] WorldEdit smoke
- [ ] model/palette/export version
- [ ] old job/artifact compatibility

### Security/privacy

- [ ] dependency/license/secret scan
- [ ] owner/IDOR
- [ ] upload adversarial
- [ ] private storage/signed URL
- [ ] retention/delete
- [ ] provider data policy

### Operations

- [ ] staging smoke
- [ ] dashboard/alert
- [ ] capacity/cost
- [ ] backup/restore status
- [ ] rollback digest/rehearsal
- [ ] on-call/runbook

### Product

- [ ] known limitation
- [ ] input guide
- [ ] progress/error/remedy
- [ ] import guide
- [ ] target version 표시
- [ ] 보존/외부 provider 고지

## 21. Release 후 관찰

최소 canary/초기 기간에 비교:

- completion/export validation
- queue age/stage latency
- OOM/provider error
- job당 비용
- retry/cancel
- 32/64 사용 비율
- viewer error/FPS
- download/import support ticket
- storage 성장/cleanup

기준을 벗어나면 feature flag/admission으로 64, 특정 model/provider 또는 image generation을 제한할 수 있어야 한다.
