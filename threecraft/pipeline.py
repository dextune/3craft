"""End-to-end deterministic conversion pipeline."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from .contracts import (
    AssetManifest,
    AssetOrigin,
    ConversionSettings,
    EvidenceClass,
    JobStatus,
)
from .errors import ThreeCraftError
from .hashing import content_hash, sha256_bytes
from .imaging import analyze_canonical_image, canonicalize_image, safe_display_name
from .providers import DeterministicDevImageProvider, ImageGenerationProvider
from .relief import build_relief_voxel
from .schematic import read_schematic, write_schematic
from .storage import LocalArtifactStore
from .sufficiency import assess_sufficiency

ProgressCallback = Callable[[JobStatus, int], None]
DEFAULT_GENERATION_PROMPT = "a simple freestanding sculpture with a clear silhouette"


class ThreeCraftPipeline:
    def __init__(
        self,
        store: LocalArtifactStore | None = None,
        *,
        image_provider: ImageGenerationProvider | None = None,
    ) -> None:
        self.store = store or LocalArtifactStore()
        self.image_provider = image_provider or DeterministicDevImageProvider()

    def resolve_source(
        self,
        *,
        image_data: bytes | None = None,
        prompt: str | None = None,
        file_name: str | None = None,
        content_type: str | None = None,
    ) -> dict[str, Any]:
        """Use provided image bytes when present; generate only when absent."""

        if image_data is not None:
            return self.ingest_upload(
                image_data,
                file_name=file_name,
                content_type=content_type,
            )
        generation_prompt = prompt.strip() if prompt and prompt.strip() else DEFAULT_GENERATION_PROMPT
        return self.generate_image(generation_prompt)

    def ingest_upload(self, data: bytes, *, file_name: str | None, content_type: str | None) -> dict[str, Any]:
        return self._ingest(
            data,
            file_name=file_name,
            content_type=content_type,
            origin=AssetOrigin.UPLOAD,
            evidence_class=EvidenceClass.OBSERVED,
            provenance={"source": "user-upload"},
        )

    def generate_image(self, prompt: str) -> dict[str, Any]:
        generated = self.image_provider.generate(prompt)
        return self._ingest(
            generated.png_bytes,
            file_name="generated.png",
            content_type="image/png",
            origin=AssetOrigin.GENERATED,
            evidence_class=EvidenceClass.DESIGN_INTENT,
            provenance={
                "source": "generated",
                "provider": generated.provider,
                "model": generated.model,
                "seed": generated.seed,
                "prompt": generated.prompt,
                "notice": "Deterministic development illustration; not an AI reconstruction.",
            },
        )

    def _ingest(
        self,
        data: bytes,
        *,
        file_name: str | None,
        content_type: str | None,
        origin: AssetOrigin,
        evidence_class: EvidenceClass,
        provenance: dict[str, Any],
    ) -> dict[str, Any]:
        canonical = canonicalize_image(data, declared_content_type=content_type)
        analysis = analyze_canonical_image(
            canonical.png_bytes,
            source_width=canonical.width,
            source_height=canonical.height,
        )
        sufficiency = assess_sufficiency(analysis.sense, route="relief")
        asset_id = self.store.new_id("ast")
        manifest = AssetManifest(
            asset_id=asset_id,
            origin=origin,
            evidence_class=evidence_class,
            content_type="image/png",
            byte_size=len(canonical.png_bytes),
            sha256=canonical.canonical_sha256,
            width=canonical.width,
            height=canonical.height,
            original_file_name=safe_display_name(file_name),
            provenance={
                **provenance,
                "sourceFormat": canonical.source_format,
                "sourceSha256": canonical.source_sha256,
            },
        )
        directory = self.store.create_asset_dir(asset_id)
        self.store.write_bytes(directory / "source.png", canonical.png_bytes)
        self.store.write_bytes(directory / "mask.png", analysis.mask_png)
        self.store.write_bytes(directory / "depth.png", analysis.depth_png)
        self.store.write_json(directory / "sense.json", analysis.sense.to_dict())
        self.store.write_json(directory / "sufficiency.json", sufficiency.to_dict())
        self.store.write_json(directory / "manifest.json", manifest.to_dict())
        return self.asset_summary(asset_id)

    def asset_summary(self, asset_id: str) -> dict[str, Any]:
        if not self.store.asset_exists(asset_id):
            raise ThreeCraftError("ASSET_NOT_FOUND", "The image asset was not found.", status_code=404)
        directory = self.store.asset_dir(asset_id)
        return {
            "asset": self.store.read_json(directory / "manifest.json"),
            "sense": self.store.read_json(directory / "sense.json"),
            "sufficiency": self.store.read_json(directory / "sufficiency.json"),
        }

    def convert(
        self,
        asset_id: str,
        settings: ConversionSettings,
        *,
        job_id: str | None = None,
        progress: ProgressCallback | None = None,
    ) -> dict[str, Any]:
        if not self.store.asset_exists(asset_id):
            raise ThreeCraftError("ASSET_NOT_FOUND", "The image asset was not found.", status_code=404)
        asset_dir = self.store.asset_dir(asset_id)
        sufficiency = self.store.read_json(asset_dir / "sufficiency.json")
        if sufficiency.get("agentAction") == "abort":
            raise ThreeCraftError(
                "SUFFICIENCY_REJECTED",
                "The input image does not meet the minimum conversion requirements.",
                remedies=[remedy for issue in sufficiency.get("issues", []) for remedy in issue.get("remedies", [])],
            )

        active_job_id = job_id or self.store.new_id("job")
        job_dir = self.store.job_dir(active_job_id)
        if not job_dir.exists():
            self.store.create_job_dir(active_job_id)

        def report(status: JobStatus, value: int) -> None:
            if progress:
                progress(status, value)

        report(JobStatus.PREPROCESSING, 5)
        image_bytes = (asset_dir / "source.png").read_bytes()
        mask_bytes = (asset_dir / "mask.png").read_bytes()
        report(JobStatus.ASSESSING, 12)
        report(JobStatus.RECONSTRUCTING, 25)
        report(JobStatus.VOXELIZING, 48)
        model = build_relief_voxel(image_bytes, mask_bytes, settings)
        report(JobStatus.MAPPING_BLOCKS, 72)

        preview = model.to_preview()
        bom = {
            "schemaVersion": 1,
            "jobId": active_job_id,
            "target": settings.to_dict()["target"],
            "dimensions": preview["dimensions"],
            "totalOccupied": len(model.blocks),
            "blocks": model.bom(),
            "paletteVersion": model.palette_version,
            "semanticHash": model.semantic_hash,
        }
        report(JobStatus.EXPORTING, 84)
        schematic = write_schematic(
            model,
            data_version=settings.data_version,
            minecraft_version=settings.target_minecraft_version,
            name=f"3Craft {active_job_id[-8:]}",
        )
        self.store.write_json(job_dir / "preview.json", preview)
        self.store.write_json(job_dir / "blocks.json", bom)
        self.store.write_bytes(job_dir / "model.schem", schematic)

        report(JobStatus.VALIDATING, 95)
        round_trip = read_schematic(schematic)
        gates = {
            "GATE-VOX-SCHEMA": True,
            "GATE-EXP-PARSE": round_trip.version == 3,
            "GATE-EXP-DATA-VERSION": round_trip.data_version == settings.data_version,
            "GATE-EXP-SEMANTIC-ROUNDTRIP": round_trip.model.semantic_hash == model.semantic_hash,
            "GATE-EXP-BOM": round_trip.model.bom() == model.bom(),
        }
        if not all(gates.values()):
            raise ThreeCraftError(
                "DELIVERY_GATE_FAILED",
                "The generated schematic failed semantic validation.",
                status_code=500,
            )

        artifacts = {
            "preview": {"file": "preview.json", "sha256": sha256_bytes((job_dir / "preview.json").read_bytes())},
            "bom": {"file": "blocks.json", "sha256": sha256_bytes((job_dir / "blocks.json").read_bytes())},
            "schematic": {"file": "model.schem", "sha256": sha256_bytes(schematic)},
        }
        delivery = {
            "schemaVersion": 1,
            "jobId": active_job_id,
            "status": "passed",
            "sourceAssetId": asset_id,
            "sourceAssetHash": self.store.read_json(asset_dir / "manifest.json")["sha256"],
            "pipeline": {
                "version": "pipeline-v1",
                "strategy": "relief-v1",
                "voxelizer": "relief-voxel-v1",
                "palette": model.palette_version,
                "exporter": "sponge-v3-v1",
            },
            "settings": settings.to_dict(),
            "semanticHash": model.semantic_hash,
            "gates": gates,
            "warnings": [issue["code"] for issue in sufficiency.get("issues", [])],
            "artifacts": artifacts,
        }
        delivery["contentHash"] = content_hash(delivery)
        self.store.write_json(job_dir / "delivery.json", delivery)
        result = {
            "jobId": active_job_id,
            "assetId": asset_id,
            "status": "completed",
            "summary": {
                "dimensions": preview["dimensions"],
                "occupied": len(model.blocks),
                "blockTypes": len(model.bom()),
                "semanticHash": model.semantic_hash,
            },
            "artifacts": artifacts,
            "delivery": delivery,
        }
        self.store.write_json(job_dir / "result.json", result)
        return result

    def artifact_path(self, job_id: str, name: str) -> Path:
        allowed = {"preview.json", "blocks.json", "model.schem", "delivery.json", "result.json"}
        if name not in allowed:
            raise ThreeCraftError("ARTIFACT_NOT_FOUND", "The requested artifact was not found.", status_code=404)
        path = self.store.job_dir(job_id) / name
        if not path.is_file():
            raise ThreeCraftError("ARTIFACT_NOT_READY", "The artifact is not ready yet.", status_code=409)
        return path
