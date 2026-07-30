from __future__ import annotations

import pytest

from threecraft.contracts import ConversionSettings, JobStatus
from threecraft.errors import ThreeCraftError
from threecraft.jobs import LocalJobManager
from threecraft.pipeline import ThreeCraftPipeline
from threecraft.storage import LocalArtifactStore


def test_job_completes_and_persists(tmp_path) -> None:
    pipeline = ThreeCraftPipeline(LocalArtifactStore(tmp_path / "data"))
    asset_id = pipeline.generate_image("orange robot")["asset"]["assetId"]
    jobs = LocalJobManager(pipeline, max_workers=1)
    try:
        created = jobs.submit(asset_id, ConversionSettings(max_axis=16), idempotency_key="same")
        duplicate = jobs.submit(asset_id, ConversionSettings(max_axis=16), idempotency_key="same")
        assert duplicate.job_id == created.job_id
        completed = jobs.wait(created.job_id)
        assert completed.status == JobStatus.COMPLETED
        assert completed.progress == 100
        assert completed.result is not None
        persisted = pipeline.store.read_json(pipeline.store.job_dir(created.job_id) / "job.json")
        assert persisted["status"] == "completed"
    finally:
        jobs.shutdown()


def test_idempotency_conflict_and_missing_asset_fail_closed(tmp_path) -> None:
    pipeline = ThreeCraftPipeline(LocalArtifactStore(tmp_path / "data"))
    asset_id = pipeline.generate_image("blue robot")["asset"]["assetId"]
    jobs = LocalJobManager(pipeline, max_workers=1)
    try:
        jobs.submit(asset_id, ConversionSettings(max_axis=16), idempotency_key="key")
        with pytest.raises(ThreeCraftError) as conflict:
            jobs.submit(asset_id, ConversionSettings(max_axis=32), idempotency_key="key")
        assert conflict.value.code == "IDEMPOTENCY_CONFLICT"

        before = set((pipeline.store.root / "jobs").iterdir())
        with pytest.raises(ThreeCraftError) as missing:
            jobs.submit("ast_" + "f" * 32, ConversionSettings(max_axis=16))
        assert missing.value.code == "ASSET_NOT_FOUND"
        assert missing.value.status_code == 404
        assert set((pipeline.store.root / "jobs").iterdir()) == before
    finally:
        jobs.shutdown()


def test_job_domain_failure_is_persisted(tmp_path) -> None:
    pipeline = ThreeCraftPipeline(LocalArtifactStore(tmp_path / "data"))
    asset_id = pipeline.generate_image("rejected fixture")["asset"]["assetId"]
    sufficiency_path = pipeline.store.asset_dir(asset_id) / "sufficiency.json"
    sufficiency = pipeline.store.read_json(sufficiency_path)
    sufficiency["agentAction"] = "abort"
    sufficiency["issues"] = [{"remedies": ["provide-a-clearer-image"]}]
    pipeline.store.write_json(sufficiency_path, sufficiency)

    jobs = LocalJobManager(pipeline, max_workers=1)
    try:
        created = jobs.submit(asset_id, ConversionSettings(max_axis=16))
        failed = jobs.wait(created.job_id)
        assert failed.status == JobStatus.FAILED
        assert failed.error is not None
        assert failed.error["code"] == "SUFFICIENCY_REJECTED"
        persisted = pipeline.store.read_json(pipeline.store.job_dir(created.job_id) / "job.json")
        assert persisted["status"] == "failed"
        assert persisted["error"]["code"] == "SUFFICIENCY_REJECTED"
    finally:
        jobs.shutdown()
