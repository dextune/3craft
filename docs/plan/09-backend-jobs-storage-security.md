# Backend, Jobs, Storage, and Security Plan

> [!NOTE]
> Sections describing Postgres, Redis, object storage, authentication, signed URLs, and durable recovery are target production architecture. The current executable MVP uses a process-local worker and private local filesystem store and must remain loopback-only.

## 1. Responsibility boundaries

API:

- authentication/owner in production;
- request validation;
- quota/rate limits;
- metadata transactions;
- upload/download authorization;
- job create/read/cancel;
- queue publication in production.

Worker:

- stage execution;
- artifact reads/writes;
- provider calls;
- stage profiles/heartbeats;
- gates and result manifests.

Object storage:

- binary/content artifacts.

Postgres:

- owner, asset/job/artifact metadata and state.

Redis/queue:

- minimal job references and delivery/leases.

Do not run long AI/geometry tasks in a production API request process. The current local worker uses a bounded thread pool behind an asynchronous job contract.

## 2. Common API rules

- Prefix: `/api/v1`.
- JSON is UTF-8.
- Mutations support `Idempotency-Key` where applicable.
- IDs are opaque.
- Dates are UTC ISO-8601.
- Production pagination is cursor-based.
- Error bodies have one shape.
- Responses carry request/correlation IDs.
- CORS/CSRF policy matches deployment topology.
- API versions and artifact-schema versions are distinct.

Error example:

```json
{
  "error": {
    "code": "FOREGROUND_EMPTY",
    "message": "No foreground subject was found for conversion.",
    "retryable": false,
    "remedies": ["upload-another-image", "edit-mask"],
    "requestId": "req_..."
  }
}
```

## 3. Source and Asset APIs

### 3.1 Current unified source resolution

```http
POST /api/v1/sources
Content-Type: multipart/form-data
```

Multipart fields:

- `file`: optional PNG/JPEG/WebP;
- `prompt`: optional string.

Contract:

1. If `file` exists, read and validate it; it wins even when `prompt` is present.
2. Empty/corrupt/unsupported supplied content fails closed.
3. If `file` is absent, generate from a nonblank prompt or the deterministic default.
4. A null provider still permits uploads but returns 503 for prompt-only fallback.
5. No URL source is accepted and no user image is sent externally.

A successful response is the same asset/sense/sufficiency summary returned by legacy source operations.

### 3.2 Current explicit asset operations

- `POST /api/v1/assets`: legacy direct upload/canonicalization.
- `GET /api/v1/assets/{id}`: asset, SensePack, and sufficiency.
- `GET /api/v1/assets/{id}/image`: private canonical source image with no-store/nosniff controls.

### 3.3 Target production upload session

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

Response:

```json
{
  "assetId": "ast_...",
  "upload": {"method": "PUT", "url": "signed", "headers": {}},
  "expiresAt": "..."
}
```

Completion:

```http
POST /api/v1/assets/{assetId}/complete
```

Never mark an object ready from HEAD alone. A validation job or safe API-side decoder checks signature, size, and decoding.

Production deletion uses `DELETE /api/v1/assets/{id}` and an asynchronous tombstone after checking active-job dependencies, retention, and lineage.

## 4. Image-generation API

Legacy current endpoint:

```http
POST /api/v1/image-generations
```

```json
{
  "prompt": "small fantasy dragon sculpture"
}
```

The current deterministic provider responds synchronously with a local procedural illustration and provenance. It is not AI generation.

Target production request:

```json
{
  "prompt": "small fantasy dragon sculpture",
  "count": 1,
  "aspectRatio": "1:1",
  "profile": "single-object"
}
```

The production response is `202` plus a job ID, with completed asset IDs. Never expose provider URLs or raw responses as the external contract. The image-generation endpoint is never used as an implicit retry for a supplied invalid image.

## 5. Conversion API

```http
POST /api/v1/conversions
Idempotency-Key: ...
```

The current request contains `sourceAssetId`, deterministic `strategy=relief`, `maxAxis`, `fillMode`, and `paletteProfile=safe-basic`. The target request expands toward [04-contracts-and-data-model.md](04-contracts-and-data-model.md).

Server validation:

- owner can access ReferenceSet assets in production;
- asset is ready;
- sufficiency policy/override permits conversion;
- strategy capability exists;
- resolution/quota is allowed;
- palette/target are compatible;
- concurrent-job limit allows admission;
- request hash is canonical.

Response:

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

Current:

- `GET /api/v1/jobs/{id}`;
- `POST /api/v1/jobs/{id}/cancel`.

Production target:

- `GET /api/v1/jobs/{id}/events` via SSE;
- `POST /api/v1/jobs/{id}/retry`;
- `POST /api/v1/jobs/{id}/clone` for changed settings.

SSE event types:

- snapshot;
- stage_changed;
- progress;
- warning;
- retry_wait;
- completed;
- failed;
- cancelled;
- heartbeat.

SSE does not own the job. Execution continues after disconnect, and clients recover from the last event or polling.

## 7. Artifact API

Current validated artifact routes:

- `GET /api/v1/jobs/{id}/preview`;
- `GET /api/v1/jobs/{id}/bom`;
- `GET /api/v1/jobs/{id}/schematic`.

They require a completed job and return private/no-store data.

Production target:

- `GET /api/v1/jobs/{id}/artifacts`;
- `POST /api/v1/artifacts/{id}/download`.

A production download endpoint checks:

1. authentication/session;
2. owner scope;
3. artifact state is `published`;
4. expiry/retention;
5. safe content-disposition name;
6. short-lived signed URL or stream;
7. audit event.

IDOR tests are mandatory.

## 8. Postgres model (production target)

### 8.1 owners/sessions

- owner/user ID;
- anonymous session ID;
- plan/quota class;
- status;
- created/last-seen/expiry.

Anonymous alpha sessions use signed HttpOnly cookies, short retention, and low quotas.

### 8.2 assets

- ID/owner;
- kind/origin/evidence class;
- status;
- display filename;
- canonical MIME/size/hash/dimensions;
- private storage key;
- provenance JSON;
- created/ready/expires/deleted timestamps;
- version.

States:

- pending_upload;
- uploaded;
- validating;
- ready;
- rejected;
- expired;
- deleting;
- deleted.

### 8.3 reference_sets

- ID/owner;
- schema version;
- manifest JSON or artifact ID;
- content hash;
- primary asset;
- created timestamp.

### 8.4 jobs

- ID/owner/kind;
- status/stage/progress;
- request JSON/hash;
- idempotency key;
- pipeline version;
- active attempt;
- cancellation state;
- error code/public message/operator reference;
- timestamps;
- optimistic version.

Apply a unique constraint to owner + endpoint scope + idempotency key.

### 8.5 attempts

- ID/job/number;
- worker/lease expiry/heartbeat;
- state/stage cursor;
- retry cause;
- profile JSON;
- started/ended.

### 8.6 artifacts

- ID/job/owner;
- kind/state/schema version;
- storage key;
- MIME/bytes/hash/semantic hash;
- producer/parent metadata;
- created/validated/published/expires/deleted.

### 8.7 events/outbox

Commit job events and queue-publication outbox records in one transaction so a persisted job cannot lose its queue message. The outbox relay is idempotent.

## 9. Queue messages and delivery

```json
{
  "schemaVersion": 1,
  "jobId": "job_...",
  "attemptHint": 1,
  "requestedCapability": "gpu-reconstruction"
}
```

Forbidden in queue messages:

- image bytes;
- secrets;
- signed URLs;
- complete user prompts;
- mutable copies of settings.

Assume at-least-once delivery. A worker that cannot acquire the database lease by CAS does not execute a duplicate message.

Candidate queues:

- intake/CPU;
- reconstruction/GPU;
- voxel-export/CPU;
- image-generation/provider.

Start with one orchestration queue and capability routing; split only when metrics justify it.

## 10. Worker leases and heartbeats

1. Receive a message.
2. Check whether the job is terminal.
3. Acquire a lease with CAS.
4. Create/recover an attempt.
5. Start heartbeat loop.
6. Execute stage.
7. Commit stage manifest.
8. Move to the next stage or terminal transition.
9. Acknowledge message.

After a worker crash:

- wait for visibility/lease timeout;
- have a new worker validate the last completed stage manifest;
- verify candidate artifact checksums;
- rerun from a safe stage.

Check fencing token/attempt ID on artifact commit so a stale worker cannot write late output.

## 11. Retry

Retryable:

- transient provider timeout;
- rate limit with bounded retry-after;
- temporary storage/database error;
- worker crash;
- queue lease timeout.

Non-retryable:

- invalid input;
- policy/license block;
- repeated empty/invalid mesh;
- unsupported target block/version;
- deterministic export-validation failure;
- quota exceeded.

Use exponential backoff with jitter, maximum attempts, and a total budget. Check provider idempotency/correlation before and after calls to limit duplicate cost.

## 12. Cancellation

- queued: immediately cancelled;
- running: set `cancel_requested`;
- stages check the flag at checkpoints;
- use provider cancellation when supported;
- pair forced GPU-process termination with worker isolation;
- cancelled jobs create no published artifact;
- cancellation of an already completed job is not deletion.

Only one versioned transition wins a cancel/complete race.

## 13. Storage architecture

Bucket/prefix classes:

- source-original;
- source-canonical;
- internal-evidence;
- internal-reconstruction;
- internal-voxel;
- published-delivery.

Even in one bucket, separate IAM prefixes and lifecycle policies.

Principles:

- public-access block;
- encryption at rest;
- TLS;
- server-side checksum verification;
- minimal signed-URL TTL;
- incomplete multipart cleanup;
- lifecycle/retention;
- no user filenames in storage keys;
- candidate → published is database state plus immutable object, not rename semantics.

The local store mirrors privacy with `0700` directories, `0600` files, validated opaque IDs, and path-containment checks.

## 14. Security controls

### 14.1 Upload

- magic/decode/pixel limits;
- re-encode and metadata stripping;
- reject animation/ZIP/archive input;
- parser sandbox in production;
- generated keys immune to path traversal.

### 14.2 API

- schema validation;
- owner-scoped authorization in production;
- rate limits/quotas;
- CSRF defense with cookie authentication;
- CORS allowlist;
- security headers;
- error redaction;
- audit sensitive actions.

### 14.3 Worker

- non-root;
- read-only root filesystem;
- isolated temporary directory;
- CPU/RAM/GPU/time limits;
- restricted egress;
- no user-controlled shell commands;
- model-weight checksums;
- temporary cleanup.

### 14.4 Secrets

- secret manager/CI-protected secrets;
- no client-exposed environment prefixes;
- log/error-report redaction;
- rotation;
- provider-specific scopes.

### 14.5 Supply chain

- exact dependency pins and lockfiles;
- package-name review;
- image digests;
- SBOM/license report;
- model/texture checksums and licenses;
- vulnerability scanning.

## 15. Quotas and abuse

- upload bytes/pixels;
- active jobs;
- image-generation count;
- GPU-seconds;
- 64/128 resolution;
- artifact storage;
- download bandwidth;
- per-IP/session/user rate.

Reject at admission rather than creating a doomed job. Record actual consumption in the attempt profile.

## 16. Privacy and retention

Proposed defaults requiring product-policy approval:

- failed/pending upload: short period;
- source image: default 24 hours after completion;
- intermediate mesh/voxel: short debugging retention;
- final delivery: longer or based on explicit user storage;
- logs/events: limited period without prompts/content.

Deletion:

1. Create tombstone.
2. Check active dependencies.
3. Delete storage objects.
4. Confirm/retry.
5. Preserve only minimal audit metadata.

Disclose any image/prompt sent to an external provider and provider retention before such an adapter can be enabled. The current local MVP keeps data local.

## 17. Observability

Common fields:

- environment/service/version;
- request/job/attempt ID;
- pseudonymous owner ID;
- stage/version;
- model/provider/palette;
- duration/resources;
- error code/retryability.

Forbidden:

- image binaries;
- full prompts in default logs;
- authorization headers/API keys;
- signed-URL queries;
- absolute temporary paths.

Metrics and alerts follow [13-operations-and-release.md](13-operations-and-release.md).

## 18. Backend completion criteria

Current local gates include image-first precedence, invalid-image fail-closed behavior, idempotent conversion submission, private local permissions, path containment, terminal job errors, and candidate-free failure handling.

Production completion additionally requires:

- owner-scope/IDOR tests;
- outbox/queue message-loss recovery;
- a single lease under duplicate delivery;
- stage recovery after worker termination;
- cancel/complete race tests;
- candidate unavailable before gates;
- signed-URL scope/expiry;
- end-to-end retention;
- no secrets in API/client/log output.
