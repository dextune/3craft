from __future__ import annotations

import time

from fastapi.testclient import TestClient

from threecraft.api import create_app
from threecraft.providers import NullImageProvider


def _wait(client: TestClient, job_id: str) -> dict:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        response = client.get(f"/api/v1/jobs/{job_id}")
        assert response.status_code == 200
        payload = response.json()
        if payload["terminal"]:
            return payload
        time.sleep(0.02)
    raise AssertionError("job did not reach a terminal state")


def test_api_upload_convert_and_download(tmp_path, object_png: bytes) -> None:
    app = create_app(data_dir=tmp_path / "data")
    with TestClient(app) as client:
        assert client.get("/api/v1/health").json()["status"] == "ok"
        capabilities = client.get("/api/v1/capabilities").json()
        assert capabilities["strategies"][0]["id"] == "relief"
        assert capabilities["imageGeneration"]["provider"] == "deterministic-dev"

        upload = client.post(
            "/api/v1/assets",
            files={"file": ("object.png", object_png, "image/png")},
        )
        assert upload.status_code == 201, upload.text
        asset = upload.json()["asset"]
        assert asset["evidenceClass"] == "observed"
        source_image = client.get(f"/api/v1/assets/{asset['assetId']}/image")
        assert source_image.status_code == 200
        assert source_image.headers["content-type"] == "image/png"
        assert source_image.headers["cache-control"].startswith("private")
        assert source_image.content.startswith(b"\x89PNG")
        assert client.get("/api/v1/assets/not-valid/image").status_code == 404

        request = {
            "sourceAssetId": asset["assetId"],
            "strategy": "relief",
            "maxAxis": 16,
            "fillMode": "hollow",
            "paletteProfile": "safe-basic",
        }
        created = client.post("/api/v1/conversions", json=request, headers={"Idempotency-Key": "api-test"})
        assert created.status_code == 202, created.text
        duplicate = client.post("/api/v1/conversions", json=request, headers={"Idempotency-Key": "api-test"})
        assert duplicate.json()["jobId"] == created.json()["jobId"]
        conflict_request = {**request, "maxAxis": 32}
        conflict = client.post("/api/v1/conversions", json=conflict_request, headers={"Idempotency-Key": "api-test"})
        assert conflict.status_code == 409
        assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
        missing_request = {**request, "sourceAssetId": f"ast_{'0' * 32}"}
        missing = client.post("/api/v1/conversions", json=missing_request)
        assert missing.status_code == 404
        assert missing.json()["error"]["code"] == "ASSET_NOT_FOUND"

        job = _wait(client, created.json()["jobId"])
        assert job["status"] == "completed", job
        job_id = job["jobId"]
        preview = client.get(f"/api/v1/jobs/{job_id}/preview")
        assert preview.status_code == 200
        assert preview.headers["cache-control"] == "private, no-store"
        assert preview.headers["x-content-type-options"] == "nosniff"
        assert preview.json()["statistics"]["occupied"] > 0
        bom = client.get(f"/api/v1/jobs/{job_id}/bom")
        assert bom.status_code == 200
        assert bom.json()["totalOccupied"] == preview.json()["statistics"]["occupied"]
        schematic = client.get(f"/api/v1/jobs/{job_id}/schematic")
        assert schematic.status_code == 200
        assert schematic.content.startswith(b"\x1f\x8b")
        assert schematic.headers["cache-control"] == "private, no-store"
        assert schematic.headers["x-content-type-options"] == "nosniff"
        assert ".schem" in schematic.headers["content-disposition"]


def test_api_generation_and_invalid_upload(tmp_path) -> None:
    app = create_app(data_dir=tmp_path / "data")
    with TestClient(app) as client:
        generated = client.post("/api/v1/image-generations", json={"prompt": "green crystal"})
        assert generated.status_code == 201
        assert generated.json()["asset"]["evidenceClass"] == "design-intent"
        assert generated.json()["asset"]["provenance"]["provider"] == "deterministic-dev"

        invalid = client.post(
            "/api/v1/assets",
            files={"file": ("bad.png", b"not-an-image", "image/png")},
        )
        assert invalid.status_code == 400
        assert invalid.json()["error"]["code"] == "IMAGE_DECODE_FAILED"


def test_api_null_provider_is_fail_closed(tmp_path) -> None:
    app = create_app(data_dir=tmp_path / "data", image_provider=NullImageProvider())
    with TestClient(app) as client:
        capabilities = client.get("/api/v1/capabilities")
        assert capabilities.status_code == 200
        assert capabilities.json()["imageGeneration"] == {
            "provider": "null",
            "available": False,
            "notice": "No image generation provider configured",
        }
        generated = client.post("/api/v1/image-generations", json={"prompt": "unused"})
        assert generated.status_code == 503
        assert generated.json()["error"]["code"] == "IMAGE_PROVIDER_UNAVAILABLE"
