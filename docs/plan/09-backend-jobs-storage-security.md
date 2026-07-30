# Backend, Job, Storage와 Security 계획

## 1. 책임 경계

API:

- 인증/owner
- request validation
- quota/rate limit
- metadata transaction
- upload/download authorization
- job 생성/조회/cancel
- queue publish

Worker:

- stage 실행
- artifact read/write
- provider 호출
- stage profile/heartbeat
- gate와 결과 manifest

Object storage:

- binary/content artifact

Postgres:

- owner, asset/job/artifact metadata와 state

Redis/queue:

- 최소 job reference와 delivery/lease

장시간 AI/geometry를 API request process에서 실행하지 않는다.

## 2. API 공통 규칙

- prefix: `/api/v1`
- JSON은 UTF-8
- mutation은 `Idempotency-Key` 지원
- opaque ID
- ISO-8601 UTC
- pagination은 cursor 기반
- 오류 body 통일
- request/correlation ID 응답
- CORS/CSRF 정책은 배포 topology에 맞춤
- API version과 artifact schema version을 구분

오류 예:

```json
{
  "error": {
    "code": "FOREGROUND_EMPTY",
    "message": "이미지에서 변환할 물체를 찾지 못했습니다.",
    "retryable": false,
    "remedies": ["upload-another-image", "edit-mask"],
    "requestId": "req_..."
  }
}
```

## 3. Asset API

### 3.1 Upload 생성

```http
POST /api/v1/assets/uploads
Idempotency-Key: ...
```

```json
{
  "fileName": "object.png",
  "contentType": "image/png",
  "byteSize": 123456,
  "sha256": "optional-client-hash"
}
```

응답:

```json
{
  "assetId": "ast_...",
  "upload": {"method": "PUT", "url": "signed", "headers": {}},
  "expiresAt": "..."
}
```

### 3.2 Upload complete

```http
POST /api/v1/assets/{assetId}/complete
```

서버가 object HEAD만 보고 ready로 만들지 않는다. validation job 또는 안전한 API-side decoder가 signature/size/decode를 확인한다.

### 3.3 Asset 조회/삭제

- `GET /api/v1/assets/{id}`
- `DELETE /api/v1/assets/{id}`

삭제는 실행 중 job dependency, retention과 artifact lineage를 확인하고 asynchronous tombstone으로 처리한다.

## 4. Image generation API

```http
POST /api/v1/image-generations
```

```json
{
  "prompt": "작은 판타지 용 조각상",
  "count": 1,
  "aspectRatio": "1:1",
  "profile": "single-object"
}
```

응답은 `202`와 job ID다. 완료 artifact는 asset ID 목록이다. provider URL/response를 외부 계약에 직접 노출하지 않는다.

## 5. Conversion API

```http
POST /api/v1/conversions
Idempotency-Key: ...
```

body는 [04-contracts-and-data-model.md](04-contracts-and-data-model.md)의 `ConversionRequest`를 따른다.

서버 validation:

- owner가 ReferenceSet asset에 접근 가능
- asset ready
- sufficiency policy/override
- strategy capability
- resolution/quota
- palette/target compatibility
- concurrent job limit
- canonical request hash

응답:

```json
{
  "jobId": "job_...",
  "status": "queued",
  "progress": 0,
  "links": {
    "self": "/api/v1/jobs/job_...",
    "events": "/api/v1/jobs/job_.../events",
    "cancel": "/api/v1/jobs/job_.../cancel"
  }
}
```

## 6. Job API

- `GET /api/v1/jobs/{id}`
- `GET /api/v1/jobs/{id}/events` SSE
- `POST /api/v1/jobs/{id}/cancel`
- `POST /api/v1/jobs/{id}/retry`
- `POST /api/v1/jobs/{id}/clone` 설정 변경용

SSE event:

- snapshot
- stage_changed
- progress
- warning
- retry_wait
- completed
- failed
- cancelled
- heartbeat

SSE가 job을 소유하지 않는다. 연결 종료 후에도 실행되며 client는 last event/polling으로 복구한다.

## 7. Artifact API

- `GET /api/v1/jobs/{id}/artifacts`
- `POST /api/v1/artifacts/{id}/download`

다운로드 endpoint:

1. auth/session
2. owner scope
3. artifact `published`
4. expiry/retention
5. content disposition safe name
6. 짧은 signed URL 또는 stream
7. audit event

IDOR 테스트를 필수로 둔다.

## 8. Postgres 모델

### 8.1 owners/sessions

- owner/user ID
- anonymous session ID
- plan/quota class
- status
- created/last seen/expiry

anonymous alpha는 signed HttpOnly session cookie, 짧은 retention과 낮은 quota를 사용한다.

### 8.2 assets

- id/owner
- kind/origin/evidence class
- status
- display filename
- canonical MIME/size/hash/dimensions
- private storage key
- provenance JSON
- created/ready/expires/deleted timestamps
- version

status:

- pending_upload
- uploaded
- validating
- ready
- rejected
- expired
- deleting
- deleted

### 8.3 reference_sets

- id/owner
- schema version
- manifest JSON 또는 artifact ID
- content hash
- primary asset
- created

### 8.4 jobs

- id/owner/kind
- status/stage/progress
- request JSON/hash
- idempotency key
- pipeline version
- active attempt
- cancellation
- error code/public message/operator reference
- timestamps
- optimistic version

unique constraint는 owner + endpoint scope + idempotency key에 둔다.

### 8.5 attempts

- id/job/number
- worker/lease expiry/heartbeat
- state/stage cursor
- retry cause
- profile JSON
- started/ended

### 8.6 artifacts

- id/job/owner
- kind/state/schema version
- storage key
- MIME/byte/hash/semantic hash
- producer/parent metadata
- created/validated/published/expires/deleted

### 8.7 events/outbox

job event와 queue publish outbox를 transaction으로 연결해 DB job은 생겼지만 queue message가 사라지는 문제를 막는다. outbox relay는 idempotent해야 한다.

## 9. Queue message와 delivery

```json
{
  "schemaVersion": 1,
  "jobId": "job_...",
  "attemptHint": 1,
  "requestedCapability": "gpu-reconstruction"
}
```

금지:

- image bytes
- secret
- signed URL
- user prompt 전체
- mutable settings copy

queue는 at-least-once로 가정한다. worker가 DB lease를 CAS로 얻지 못하면 메시지를 중복 실행하지 않는다.

queue 분리 후보:

- intake/cpu
- reconstruction/gpu
- voxel-export/cpu
- image-generation/provider

초기에는 단일 orchestration queue와 capability routing으로 시작하고 지표가 필요성을 보여주면 분리한다.

## 10. Worker lease와 heartbeat

1. message 수신
2. terminal job 여부 확인
3. lease 획득(CAS)
4. attempt 생성/복구
5. heartbeat loop
6. stage 실행
7. stage manifest commit
8. 다음 stage 또는 terminal transition
9. message ack

worker crash:

- visibility/lease timeout
- 새 worker가 마지막 completed stage manifest 검증
- candidate artifact checksum 확인
- 안전 stage부터 재실행

stale worker가 늦게 결과를 쓰지 못하도록 fencing token/attempt ID를 artifact commit에 검사한다.

## 11. Retry

retryable:

- provider transient timeout
- rate limit with bounded retry-after
- storage/DB temporary error
- worker crash
- queue lease timeout

non-retryable:

- invalid input
- policy/license block
- empty/invalid mesh 반복
- unsupported target block/version
- deterministic export validation failure
- quota 초과

exponential backoff + jitter, max attempts와 총 budget을 둔다. provider 호출 전후 idempotency/correlation을 확인해 중복 비용을 제한한다.

## 12. Cancellation

- queued: 즉시 cancelled
- running: cancel_requested flag
- stage는 checkpoint에서 flag 확인
- provider cancel capability 사용
- GPU process 강제 kill은 worker isolation 전략과 함께 사용
- cancelled job은 published artifact를 만들지 않음
- 이미 completed된 job cancel은 delete가 아님

cancel/complete 경쟁은 하나의 versioned transition만 성공한다.

## 13. Storage architecture

bucket/prefix 분류:

- source-original
- source-canonical
- internal-evidence
- internal-reconstruction
- internal-voxel
- published-delivery

하나의 bucket을 쓰더라도 IAM prefix와 lifecycle을 분리한다.

원칙:

- public access block
- encryption at rest
- TLS
- server-side checksum 검증
- signed URL TTL 최소화
- multipart incomplete cleanup
- lifecycle/retention
- user filename 미사용
- candidate→published는 DB state + immutable object, rename 의존 금지

## 14. Security control

### 14.1 Upload

- magic/decode/pixel limit
- re-encode/metadata strip
- animation/zip/archive 거부
- parser sandbox
- path traversal 무관한 generated key

### 14.2 API

- schema validation
- authz owner scope
- rate limit/quota
- CSRF if cookie auth
- CORS allowlist
- security header
- error redaction
- audit sensitive action

### 14.3 Worker

- non-root
- read-only root filesystem
- isolated temp dir
- CPU/RAM/GPU/time limit
- restricted egress
- no user-controlled shell command
- model weight checksum
- temp cleanup

### 14.4 Secret

- secret manager/CI protected secret
- client env prefix 금지
- log/sentry redaction
- rotation
- provider별 scope

### 14.5 Supply chain

- exact dependency pin + lockfile
- package name 검토
- image digest
- SBOM/license report
- model/texture checksum과 license
- vulnerability scan

## 15. Quota와 abuse

- upload byte/pixel
- active jobs
- image generation count
- GPU seconds
- 64/128 resolution
- artifact storage
- download bandwidth
- IP/session/user rate

quota 거부는 job을 만든 후 실패시키기보다 admission에서 처리한다. 실제 소비량은 attempt profile에 기록한다.

## 16. Privacy와 retention

기본 제안이며 제품 정책 승인 필요:

- failed/pending upload: 짧은 시간
- source image: 완료 후 24시간 기본
- intermediate mesh/voxel: 디버깅 목적의 단기 보존
- final delivery: 더 긴 기간 또는 사용자 저장 여부
- logs/events: prompt/content 없이 제한 기간

삭제:

1. tombstone
2. 실행 중 dependency 확인
3. storage delete
4. 결과 확인/retry
5. metadata 최소 audit 보존

외부 provider로 보내는 이미지/prompt와 provider retention을 사용자에게 고지한다.

## 17. Observability

공통 field:

- environment/service/version
- request/job/attempt ID
- owner는 pseudonymous ID
- stage/version
- model/provider/palette
- duration/resource
- error code/retryable

금지:

- image binary
- full prompt 기본 log
- auth header/API key
- signed URL query
- absolute temp path

metric/alert는 [13-operations-and-release.md](13-operations-and-release.md)를 따른다.

## 18. Backend 완료 조건

- idempotent conversion 생성
- owner scope/IDOR test
- outbox/queue message 손실 복구
- duplicate delivery에서 한 attempt만 lease
- worker kill 후 stage recovery
- cancel/complete race test
- candidate는 gate 전 다운로드 불가
- signed URL scope/expiry
- retention end-to-end
- secrets가 API/client/log에 없음
