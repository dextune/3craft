from __future__ import annotations

import json

import pytest

from threecraft.contracts import ConversionSettings, FillMode
from threecraft.errors import ThreeCraftError
from threecraft.pipeline import ThreeCraftPipeline
from threecraft.storage import LocalArtifactStore


def test_generated_asset_pipeline_and_delivery(tmp_path) -> None:
    pipeline = ThreeCraftPipeline(LocalArtifactStore(tmp_path / "data"))
    asset_summary = pipeline.generate_image("purple guardian crystal")
    asset = asset_summary["asset"]
    assert asset["origin"] == "generated"
    assert asset["evidenceClass"] == "design-intent"
    assert asset["provenance"]["provider"] == "deterministic-dev"
    assert "not an AI reconstruction" in asset["provenance"]["notice"]

    result = pipeline.convert(
        asset["assetId"],
        ConversionSettings(max_axis=16, fill_mode=FillMode.HOLLOW),
    )
    assert result["status"] == "completed"
    assert all(result["delivery"]["gates"].values())
    job_dir = pipeline.store.job_dir(result["jobId"])
    assert (job_dir / "model.schem").stat().st_size > 0
    assert json.loads((job_dir / "blocks.json").read_text())["totalOccupied"] == result["summary"]["occupied"]


def test_uploaded_asset_is_observed(tmp_path, object_png: bytes) -> None:
    pipeline = ThreeCraftPipeline(LocalArtifactStore(tmp_path / "data"))
    summary = pipeline.ingest_upload(object_png, file_name="../../object.png", content_type="image/png")
    assert summary["asset"]["origin"] == "upload"
    assert summary["asset"]["evidenceClass"] == "observed"
    assert summary["asset"]["originalFileName"] == "object.png"


def test_rejected_asset_cannot_convert(tmp_path, empty_png: bytes) -> None:
    pipeline = ThreeCraftPipeline(LocalArtifactStore(tmp_path / "data"))
    summary = pipeline.ingest_upload(empty_png, file_name="empty.png", content_type="image/png")
    assert summary["sufficiency"]["agentAction"] == "abort"
    with pytest.raises(ThreeCraftError) as rejected:
        pipeline.convert(summary["asset"]["assetId"], ConversionSettings(max_axis=16))
    assert rejected.value.code == "SUFFICIENCY_REJECTED"
