# Operations and Release Runbook

## 1. Purpose

This document defines execution contracts, incident response, release, and rollback for development, staging, and production. Commands and cloud-resource names for the production target must be updated after their milestones are implemented. Do not execute illustrative production commands unchanged.

> [!WARNING]
> The current repository is a loopback-only local MVP without authentication, tenant isolation, production database/queue/object storage, or a real AI provider. Do not expose it to the Internet or an untrusted LAN.

## 2. Environments

### Current local MVP

- Vite Web app on `127.0.0.1:5173`;
- Python FastAPI service on `127.0.0.1:8000`;
- process-local bounded worker pool;
- private `.threecraft-data/` artifact store;
- deterministic local illustration provider or null provider;
- deterministic CPU relief/voxel/export.

### Target production-development environment

- Vite Web app;
- Python API;
- Python worker;
- Postgres;
- Redis;
- S3-compatible local storage;
- fixture provider;
- optional local GPU adapter.

### CI

- deterministic local/fixture provider;
- independent schematic parser;
- clean Python and Node installs;
- strict TypeScript/Vite build;
- future ephemeral database/queue/storage and headless browser;
- separate scheduled GPU runner only after a model is selected.

### Staging target

- same topology and permission model as production;
- separate account/project/bucket/keys;
- limited quotas;
- non-sensitive fixtures;
- separately scoped staging provider keys.

### Production target

- stateless Web/API;
- CPU/GPU worker pools;
- managed or highly available database/queue/storage;
- private network and least privilege;
- centralized logs, metrics, and traces;
- backup, lifecycle, and cost alerts.

Never share buckets, databases, or provider keys between environments.

## 3. Configuration categories

Target categories:

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

The current local MVP uses documented `THREECRAFT_*` settings, including its data directory and image-provider selection. Validate actual variables through typed settings at startup as the production configuration grows. Keep secrets separate from public configuration.

## 4. Local bootstrap contract

Current executable commands:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
npm --prefix apps/web ci
./scripts/dev.sh
```

Validation:

```bash
make check
```

Or separately:

```bash
.venv/bin/python -m pytest -q
npm --prefix apps/web run build
```

Run services independently when needed:

```bash
.venv/bin/python -m uvicorn services.api.main:app --host 127.0.0.1 --port 8000
npm --prefix apps/web run dev
```

The launcher uses strict ports and cleans up both children. It must not silently bind publicly or choose an unexpected port.

The eventual production repository should also expose logical operations for:

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

Target startup order:

1. Verify pinned runtimes.
2. Install locked dependencies.
3. Create local environment.
4. Start database, Redis, and storage.
5. Run migrations.
6. Initialize private bucket/prefixes.
7. Verify API readiness.
8. Start fixture worker.
9. Start Web app.
10. Run vertical smoke.

Shutdown cleans up worker leases and temporary artifacts without arbitrarily deleting service volumes.

## 5. Health endpoints

### Current API health

`GET /api/v1/health` reports service liveness. `GET /api/v1/capabilities` separately reports route, image-provider, settings, and target capabilities. Provider unavailability does not make supplied-image conversion unavailable.

### Target API liveness

- Check only process/event-loop liveness.
- Do not create endless restarts after dependency failures.

### Target API readiness

- typed configuration;
- database query;
- queue publication capability;
- storage metadata access.

### Target worker liveness

- process and heartbeat loop.

### Target worker readiness

- queue/storage access;
- temporary disk;
- provider/model configuration;
- model-load or lazy-load state;
- GPU/VRAM sanity.

Treat an image-generation provider failure as capability health, not failure of all upload/relief API readiness.

## 6. Deployment artifacts

Target release inventory:

- Web static/container artifact;
- API container digest;
- CPU/GPU worker container digests;
- database migration version;
- contract-schema version;
- model identifier/weight checksum;
- palette content hash;
- target Minecraft/DataVersion;
- release manifest/SBOM.

Never download an unapproved “latest” model or dependency at runtime.

The current Python wheel must include package metadata and LICENSE; the Web build must be reproducible from its lockfile.

## 7. Deployment order

1. Create release commit/tag and immutable artifacts.
2. Run unit/integration/E2E/security scans appropriate to implemented scope.
3. Review migration backward compatibility.
4. Deploy to staging.
5. Run fixture smoke.
6. Run real provider/GPU smoke only when configured and approved.
7. Run schematic parser plus actual WorldEdit smoke.
8. Verify dashboards/alerts.
9. Canary API/workers.
10. Observe queue age, errors, and cost.
11. Complete rollout.
12. Publish release notes and known limitations.

Check worker/queue-payload compatibility first. If new workers cannot read existing jobs, use a versioned queue or drain plan.

For the current GitHub-hosted local MVP, release means a reviewed commit on a safe branch, successful Python and Web CI jobs, clean annotations, matching local/remote SHA, and no runtime artifacts in Git. It is not a production deployment.

## 8. Migration principles

- expand → migrate/backfill → contract;
- old and new code coexist during rolling deployment;
- destructive migrations require separate approval, backup, and rollback;
- distinguish artifact schemas from database schemas;
- throttle large backfills online;
- observe migration metrics and lock time.

## 9. Smoke tests

### Current local source-to-delivery smoke

1. Create a valid PNG fixture.
2. Submit image plus prompt to `/api/v1/sources`; confirm origin `upload`.
3. Confirm the generation provider was not needed.
4. Submit prompt only; confirm origin `generated`, or explicit 503 with null provider.
5. Submit invalid supplied bytes plus prompt; confirm validation failure without fallback.
6. Create a 16- or 32-axis relief conversion.
7. Observe queued → completed.
8. Retrieve preview and BOM.
9. Download schematic.
10. Parse independently with `nbtlib`.
11. Verify Sponge version 3, DataVersion 3700, semantic hash, and BOM equality.
12. Confirm no secrets, absolute local paths, or user images entered tracked output.

### Target production smoke

1. Valid PNG upload.
2. Canonical asset ready.
3. 16-axis relief conversion.
4. Queued → completed event.
5. Preview/BOM.
6. Schematic download.
7. Independent parser.
8. BOM equality.
9. Invalid-upload rejection.
10. Cross-owner denial.
11. No secrets in logs.

### GPU smoke

- one real single-image reconstruction;
- model/version/checksum verified;
- duration/VRAM measured;
- raw/repaired mesh valid;
- next job accepted;
- temporary/GPU memory released.

Do not run or claim this smoke until a provider/model passes its ADR gates.

### Minecraft smoke

- paste in a supported WorldEdit/Minecraft environment;
- verify orientation, ground, and offset;
- spot-check expected block count;
- verify no unsupported blocks.

This remains a production compatibility backlog item.

## 10. Observability

### Logs

Fields:

- timestamp/level/service/environment/release;
- request/job/attempt/stage;
- pseudonymous owner ID;
- duration/resources;
- provider/model/palette/target;
- error code/retryability.

Redact:

- API keys, tokens, cookies;
- signed URLs;
- complete prompts by default;
- image/mesh bytes;
- unnecessary user filenames;
- absolute temporary paths.

### Metrics

API:

- request rate/latency/status;
- database pool;
- upload/download bytes;
- authentication/rate limiting.

Queue/job:

- queue depth/oldest age;
- state/stage counts;
- success/fail/cancel/retry;
- stage duration;
- lease expiry/stale attempts.

Worker/provider:

- utilization/concurrency;
- CPU/RAM/GPU/VRAM;
- model load/inference;
- provider latency/rate/error/cost;
- OOM/restarts.

Artifact/export:

- storage bytes/count;
- candidate orphans;
- validation failures;
- schematic size/block count;
- download success.

Aggregate viewer load/decode/FPS/context-error telemetry without user content.

## 11. Alerts

Critical:

- authorization or public-storage exposure;
- sharp rise in export-validation failures;
- database unavailable/data-integrity failure;
- secret-leak signal.

High:

- oldest queue age exceeds SLO;
- worker OOM/restart loop;
- provider-failure spike;
- storage-write failure;
- sharp completion-rate decline;
- cost-budget breach.

Medium:

- 64-axis viewer performance regression;
- retention backlog;
- high retry/cancel rate;
- low disk/temporary capacity.

Every alert includes owner, dashboard, runbook link, and severity.

## 12. Queue-backlog runbook

Diagnose:

1. depth/oldest age by queue;
2. worker readiness/replicas;
3. GPU utilization/VRAM;
4. stage/model/resolution distribution;
5. provider rate limits;
6. poison jobs/retry loops.

Respond:

- scale workers within safe capacity;
- limit 64/high-cost admission;
- isolate poison jobs;
- open retry-storm circuit breaker;
- publish user-facing status;
- resume admission gradually after expected recovery.

Do not blindly add replicas when that would worsen provider or database limits.

## 13. GPU OOM runbook

Diagnose:

- model/release/input resolution;
- concurrent jobs;
- memory release after previous jobs;
- driver/runtime;
- input/output complexity.

Respond:

1. Drain affected worker.
2. Reduce concurrency.
3. Mark repeated job non-retryable.
4. Suggest lower profile or relief.
5. Roll back to a known-good worker image.
6. Change model/resource budgets only after benchmark/ADR review.

Never retry an OOM job indefinitely with identical settings.

## 14. Provider-outage runbook

- Check provider status/rate limits.
- Open circuit breaker.
- Limit new jobs requiring that capability.
- Prevent queue retry storms.
- Preserve uploads, relief, and existing downloads.
- Disclose result differences before switching provider.
- Send a canary after recovery.
- Audit cost and duplicate requests.

For the current null-provider configuration, a prompt-only request returns explicit unavailability while supplied images continue to work.

## 15. Storage/database failure

Storage:

- stop completed transitions;
- inspect candidate/published state;
- defer partial multipart cleanup until recovery;
- verify corruption by checksum.

Database:

- stop API mutation admission;
- workers do not run a new stage without a database lease;
- inspect leases/fencing after recovery;
- decide on backup restore only after isolated validation.

Do not delete data or perform a hard reset without explicit high-risk approval.

For the local store, preserve the same fail-closed rule: a write or read validation failure cannot produce completed delivery.

## 16. Export-validation incident

1. Immediately restrict publication by the affected exporter/release.
2. Identify already published artifacts in scope.
3. Record model, palette, DataVersion, and serializer.
4. Preserve failing fixture and parser report.
5. Roll back to a known-good exporter.
6. Decide user impact and regeneration policy.
7. Add a regression test.

Distinguish reconstruction-quality issues from format corruption.

## 17. Retention and orphan cleanup

Cleanup order:

1. Query expired candidates.
2. Exclude active jobs, references, and holds.
3. Delete storage object.
4. Verify deletion.
5. Tombstone artifact.
6. Retry/alert.

Periodic orphan audit:

- object without database row;
- database artifact without object;
- long-stalled writing/candidate state;
- expired signed upload;
- incomplete multipart upload.

Keep tombstones; deleting database rows first makes orphan tracking difficult.

The local `.threecraft-data/` directory has no automated production retention policy. Treat it as private and remove it manually only when no needed job/artifact remains.

## 18. Backup and restore

Production target:

- encrypted scheduled Postgres backups;
- point-in-time policy;
- object versions/lifecycle or required delivery backup;
- preserved configuration/schema/model/palette manifests;
- proposed quarterly restore drill.

Restore verification:

- owner/job/artifact relationships;
- object checksums;
- published downloads;
- restored queue messages do not duplicate execution;
- deleted/tombstoned privacy policy.

## 19. Rollback

Preflight questions:

- Is the migration backward-compatible?
- Are new queue/artifact schemas compatible with previous code?
- Can the previous API read new model/palette output?
- Must active jobs drain?

Procedure:

1. Restrict new high-risk job admission.
2. Capture impact/metric snapshot.
3. Roll worker canaries/all workers back to known-good digests.
4. Roll back API/Web.
5. Isolate incompatible queues.
6. Validate artifacts.
7. Resume admission gradually.
8. Produce incident timeline/postmortem.

`git reset`, destructive database down-migrations, and bulk storage deletion are not default rollback mechanisms.

For repository publication, use a new corrective commit rather than rewriting already pushed history.

## 20. Release checklist

### Engineering

- [ ] lint/type/unit/contract checks
- [ ] integration/E2E appropriate to scope
- [ ] Web/API/worker build
- [ ] no schema drift
- [ ] schematic round-trip
- [ ] browser runtime/disposal where available
- [ ] source-precedence CLI and HTTP smoke
- [ ] exactly one valid `SKILL.md`
- [ ] zero tracked non-English user-facing text

### Compatibility

- [ ] target Minecraft/DataVersion
- [ ] WorldEdit smoke before making production compatibility claims
- [ ] model/palette/export versions
- [ ] old job/artifact compatibility

### Security/privacy

- [ ] dependency/license/secret scan
- [ ] owner/IDOR in production
- [ ] adversarial upload tests
- [ ] private storage/signed URLs where applicable
- [ ] retention/deletion
- [ ] provider data policy
- [ ] no arbitrary URL fetch or external user-image transmission

### Operations

- [ ] staging smoke for production releases
- [ ] dashboards/alerts
- [ ] capacity/cost
- [ ] backup/restore status
- [ ] rollback digest/rehearsal
- [ ] on-call/runbook

### Product

- [ ] known limitations
- [ ] input guide
- [ ] progress/errors/remedies
- [ ] import guide
- [ ] target version displayed
- [ ] retention/external-provider disclosure
- [ ] supplied-image precedence clearly displayed

## 21. Post-release observation

During the canary/initial period compare:

- completion and export-validation rates;
- queue age/stage latency;
- OOM/provider errors;
- cost per job;
- retry/cancel rates;
- 32/64 usage;
- viewer errors/FPS;
- download/import support tickets;
- storage growth/cleanup;
- unexpected generated origin on requests that included image bytes.

When thresholds are exceeded, feature flags/admission controls must be able to restrict 64-axis output, a specific model/provider, or image generation without disabling supplied-image relief conversion.
