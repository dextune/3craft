"""FastAPI application for the local 3Craft vertical slice."""

from __future__ import annotations

import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, Form, Header, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .contracts import ConversionSettings, FillMode, JobStatus
from .errors import ThreeCraftError
from .imaging import MAX_UPLOAD_BYTES
from .jobs import LocalJobManager
from .pipeline import ThreeCraftPipeline
from .providers import DeterministicDevImageProvider, ImageGenerationProvider, NullImageProvider
from .storage import LocalArtifactStore

_PRIVATE_ARTIFACT_HEADERS = {
    "Cache-Control": "private, no-store",
    "X-Content-Type-Options": "nosniff",
}


async def _read_upload(file: UploadFile) -> bytes:
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise ThreeCraftError("IMAGE_TOO_LARGE", "Image files must be 10 MB or smaller.", status_code=413)
    return data


class ImageGenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt: str = Field(min_length=1, max_length=1000)


class ConversionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sourceAssetId: str = Field(pattern=r"^ast_[0-9a-f]{32}$")
    strategy: Literal["relief"] = "relief"
    maxAxis: Literal[16, 32, 64] = 32
    fillMode: FillMode = FillMode.HOLLOW
    paletteProfile: Literal["safe-basic"] = "safe-basic"


def create_app(
    *,
    data_dir: str | Path | None = None,
    image_provider: ImageGenerationProvider | None = None,
) -> FastAPI:
    store = LocalArtifactStore(data_dir or os.getenv("THREECRAFT_DATA_DIR", ".threecraft-data"))
    provider_name = os.getenv("THREECRAFT_IMAGE_PROVIDER", "deterministic-dev")
    provider = image_provider
    if provider is None:
        provider = DeterministicDevImageProvider() if provider_name == "deterministic-dev" else NullImageProvider()
    pipeline = ThreeCraftPipeline(store, image_provider=provider)
    jobs = LocalJobManager(pipeline)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        jobs.shutdown()

    app = FastAPI(
        title="3Craft API",
        version="0.1.0",
        description="Deterministic local image-to-Minecraft relief vertical slice",
        lifespan=lifespan,
    )
    app.state.store = store
    app.state.pipeline = pipeline
    app.state.jobs = jobs
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Idempotency-Key"],
    )

    @app.exception_handler(ThreeCraftError)
    async def domain_error(request: Request, exc: ThreeCraftError) -> JSONResponse:
        request_id = request.headers.get("X-Request-Id") or f"req_{uuid.uuid4().hex}"
        return JSONResponse({"error": exc.to_dict(request_id)}, status_code=exc.status_code)

    @app.get("/api/v1/health")
    def health() -> dict[str, object]:
        return {"status": "ok", "service": "threecraft-api", "version": "0.1.0"}

    @app.get("/api/v1/capabilities")
    def capabilities() -> dict[str, object]:
        return {
            "strategies": [
                {
                    "id": "relief",
                    "available": True,
                    "kind": "deterministic-2.5d",
                    "notice": "Single-image AI mesh reconstruction is not configured in this MVP.",
                }
            ],
            "imageGeneration": {
                "provider": provider.name,
                "available": not isinstance(provider, NullImageProvider),
                "notice": "deterministic-dev creates local test illustrations, not AI images"
                if isinstance(provider, DeterministicDevImageProvider)
                else "No image generation provider configured",
            },
            "resolutions": [16, 32, 64],
            "fillModes": [mode.value for mode in FillMode],
            "paletteProfiles": ["safe-basic"],
            "target": {"edition": "java", "minecraftVersion": "1.20.4", "dataVersion": 3700},
        }

    @app.post("/api/v1/sources", status_code=201)
    async def resolve_source(
        file: UploadFile | None = File(default=None),
        prompt: str | None = Form(default=None),
    ) -> dict[str, object]:
        data = await _read_upload(file) if file is not None else None
        return pipeline.resolve_source(
            image_data=data,
            prompt=prompt,
            file_name=file.filename if file is not None else None,
            content_type=file.content_type if file is not None else None,
        )

    @app.post("/api/v1/assets", status_code=201)
    async def upload_asset(file: UploadFile = File(...)) -> dict[str, object]:
        data = await _read_upload(file)
        return pipeline.ingest_upload(data, file_name=file.filename, content_type=file.content_type)

    @app.get("/api/v1/assets/{asset_id}")
    def get_asset(asset_id: str) -> dict[str, object]:
        try:
            return pipeline.asset_summary(asset_id)
        except ValueError as exc:
            raise ThreeCraftError("ASSET_NOT_FOUND", "The image asset was not found.", status_code=404) from exc

    @app.post("/api/v1/image-generations", status_code=201)
    def generate_image(request: ImageGenerationRequest) -> dict[str, object]:
        return pipeline.generate_image(request.prompt)

    @app.get("/api/v1/assets/{asset_id}/image")
    def get_asset_image(asset_id: str) -> FileResponse:
        try:
            if not store.asset_exists(asset_id):
                raise ThreeCraftError("ASSET_NOT_FOUND", "The image asset was not found.", status_code=404)
            path = store.asset_dir(asset_id) / "source.png"
        except ValueError as exc:
            raise ThreeCraftError("ASSET_NOT_FOUND", "The image asset was not found.", status_code=404) from exc
        return FileResponse(
            path,
            media_type="image/png",
            headers={"Cache-Control": "private, max-age=300", "X-Content-Type-Options": "nosniff"},
        )

    @app.post("/api/v1/conversions", status_code=202)
    def create_conversion(
        request: ConversionRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key", min_length=1, max_length=128),
    ) -> dict[str, object]:
        try:
            settings = ConversionSettings(
                max_axis=request.maxAxis,
                fill_mode=request.fillMode,
                strategy=request.strategy,
                palette_profile=request.paletteProfile,
            )
            job = jobs.submit(request.sourceAssetId, settings, idempotency_key=idempotency_key)
        except ValueError as exc:
            raise ThreeCraftError("SETTINGS_INVALID", str(exc)) from exc
        return {
            "jobId": job.job_id,
            "status": job.status.value,
            "progress": job.progress,
            "links": {
                "self": f"/api/v1/jobs/{job.job_id}",
                "preview": f"/api/v1/jobs/{job.job_id}/preview",
                "bom": f"/api/v1/jobs/{job.job_id}/bom",
                "schematic": f"/api/v1/jobs/{job.job_id}/schematic",
            },
        }

    @app.get("/api/v1/jobs/{job_id}")
    def get_job(job_id: str) -> dict[str, object]:
        try:
            return jobs.get(job_id).to_dict()
        except ValueError as exc:
            raise ThreeCraftError("JOB_NOT_FOUND", "The conversion job was not found.", status_code=404) from exc

    @app.post("/api/v1/jobs/{job_id}/cancel")
    def cancel_job(job_id: str) -> dict[str, object]:
        return jobs.cancel(job_id).to_dict()

    def require_completed(job_id: str) -> None:
        job = jobs.get(job_id)
        if job.status != JobStatus.COMPLETED:
            raise ThreeCraftError("ARTIFACT_NOT_READY", "The conversion result is not ready yet.", status_code=409)

    @app.get("/api/v1/jobs/{job_id}/preview")
    def get_preview(job_id: str) -> FileResponse:
        require_completed(job_id)
        return FileResponse(
            pipeline.artifact_path(job_id, "preview.json"),
            media_type="application/json",
            headers=_PRIVATE_ARTIFACT_HEADERS,
        )

    @app.get("/api/v1/jobs/{job_id}/bom")
    def get_bom(job_id: str) -> FileResponse:
        require_completed(job_id)
        return FileResponse(
            pipeline.artifact_path(job_id, "blocks.json"),
            media_type="application/json",
            headers=_PRIVATE_ARTIFACT_HEADERS,
        )

    @app.get("/api/v1/jobs/{job_id}/schematic")
    def get_schematic(job_id: str) -> FileResponse:
        require_completed(job_id)
        return FileResponse(
            pipeline.artifact_path(job_id, "model.schem"),
            media_type="application/octet-stream",
            filename=f"threecraft-{job_id[-8:]}.schem",
            headers=_PRIVATE_ARTIFACT_HEADERS,
        )

    return app
