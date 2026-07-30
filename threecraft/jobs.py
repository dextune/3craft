"""Durable-enough local job manager with an interface compatible with a future queue."""

from __future__ import annotations

import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .contracts import ConversionSettings, JobStatus, TERMINAL_JOB_STATUSES
from .errors import ThreeCraftError
from .hashing import content_hash
from .pipeline import ThreeCraftPipeline

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(slots=True)
class JobRecord:
    job_id: str
    asset_id: str
    request_hash: str
    status: JobStatus = JobStatus.QUEUED
    stage: str = JobStatus.QUEUED.value
    progress: int = 0
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": 1,
            "jobId": self.job_id,
            "kind": "conversion",
            "assetId": self.asset_id,
            "status": self.status.value,
            "stage": self.stage,
            "progress": self.progress,
            "terminal": self.status in TERMINAL_JOB_STATUSES,
            "requestHash": self.request_hash,
            "result": self.result,
            "error": self.error,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }


class LocalJobManager:
    def __init__(self, pipeline: ThreeCraftPipeline, *, max_workers: int = 2) -> None:
        self.pipeline = pipeline
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="threecraft-worker")
        self._lock = threading.RLock()
        self._jobs: dict[str, JobRecord] = {}
        self._futures: dict[str, Future[dict[str, Any]]] = {}
        self._idempotency: dict[str, tuple[str, str]] = {}

    def submit(
        self,
        asset_id: str,
        settings: ConversionSettings,
        *,
        idempotency_key: str | None = None,
    ) -> JobRecord:
        try:
            asset_exists = self.pipeline.store.asset_exists(asset_id)
        except ValueError as exc:
            raise ThreeCraftError(
                "ASSET_NOT_FOUND", "이미지 asset을 찾을 수 없습니다.", status_code=404
            ) from exc
        if not asset_exists:
            raise ThreeCraftError(
                "ASSET_NOT_FOUND", "이미지 asset을 찾을 수 없습니다.", status_code=404
            )
        request_hash = content_hash({"assetId": asset_id, "settings": settings.to_dict()})
        with self._lock:
            if idempotency_key:
                previous = self._idempotency.get(idempotency_key)
                if previous:
                    previous_hash, previous_job_id = previous
                    if previous_hash != request_hash:
                        raise ThreeCraftError(
                            "IDEMPOTENCY_CONFLICT",
                            "같은 Idempotency-Key가 다른 요청에 사용되었습니다.",
                            status_code=409,
                        )
                    return self._jobs[previous_job_id]
            job_id = self.pipeline.store.new_id("job")
            self.pipeline.store.create_job_dir(job_id)
            job = JobRecord(job_id=job_id, asset_id=asset_id, request_hash=request_hash)
            self._jobs[job_id] = job
            if idempotency_key:
                self._idempotency[idempotency_key] = (request_hash, job_id)
            self._persist(job)
            self._futures[job_id] = self._executor.submit(self._run, job_id, asset_id, settings)
            return job

    def _persist(self, job: JobRecord) -> None:
        self.pipeline.store.write_json(self.pipeline.store.job_dir(job.job_id) / "job.json", job.to_dict())

    def _update(self, job_id: str, status: JobStatus, progress: int) -> None:
        with self._lock:
            job = self._jobs[job_id]
            if job.status in TERMINAL_JOB_STATUSES:
                return
            job.status = status
            job.stage = status.value
            job.progress = max(job.progress, min(100, progress))
            job.updated_at = _now()
            self._persist(job)

    def _run(self, job_id: str, asset_id: str, settings: ConversionSettings) -> dict[str, Any]:
        try:
            result = self.pipeline.convert(
                asset_id,
                settings,
                job_id=job_id,
                progress=lambda status, value: self._update(job_id, status, value),
            )
            with self._lock:
                job = self._jobs[job_id]
                job.status = JobStatus.COMPLETED
                job.stage = JobStatus.COMPLETED.value
                job.progress = 100
                job.result = result
                job.updated_at = _now()
                self._persist(job)
            return result
        except ThreeCraftError as exc:
            error = exc.to_dict()
        except Exception:
            logger.exception("Unhandled pipeline error for job %s", job_id)
            error = {
                "code": "INTERNAL_PIPELINE_ERROR",
                "message": "변환 중 내부 오류가 발생했습니다.",
                "retryable": False,
                "remedies": [],
            }
        with self._lock:
            job = self._jobs[job_id]
            job.status = JobStatus.FAILED
            job.stage = JobStatus.FAILED.value
            job.error = error
            job.updated_at = _now()
            self._persist(job)
        return {"jobId": job_id, "status": "failed", "error": error}

    def get(self, job_id: str) -> JobRecord:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                raise ThreeCraftError("JOB_NOT_FOUND", "변환 job을 찾을 수 없습니다.", status_code=404)
            return job

    def wait(self, job_id: str, timeout: float = 30.0) -> JobRecord:
        with self._lock:
            future = self._futures.get(job_id)
        if not future:
            return self.get(job_id)
        future.result(timeout=timeout)
        return self.get(job_id)

    def cancel(self, job_id: str) -> JobRecord:
        with self._lock:
            job = self.get(job_id)
            if job.status in TERMINAL_JOB_STATUSES:
                return job
            future = self._futures.get(job_id)
            if future and future.cancel():
                job.status = JobStatus.CANCELLED
                job.stage = JobStatus.CANCELLED.value
                job.updated_at = _now()
                self._persist(job)
                return job
            raise ThreeCraftError(
                "CANCEL_NOT_SAFE",
                "현재 단계는 즉시 취소할 수 없습니다.",
                status_code=409,
                remedies=["wait-for-current-stage"],
            )

    def shutdown(self) -> None:
        self._executor.shutdown(wait=True, cancel_futures=False)
