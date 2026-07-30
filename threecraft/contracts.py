"""Versioned domain contracts for the local MVP."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .hashing import content_hash


class EvidenceClass(StrEnum):
    OBSERVED = "observed"
    DESIGN_INTENT = "design-intent"
    DESIGN_HYPOTHESIS = "design-hypothesis"
    INFERRED = "inferred"


class AssetOrigin(StrEnum):
    UPLOAD = "upload"
    GENERATED = "generated"
    EDITED = "edited"
    DERIVED = "derived"
    FIXTURE = "fixture"


class FillMode(StrEnum):
    SURFACE = "surface"
    HOLLOW = "hollow"
    SOLID = "solid"


class JobStatus(StrEnum):
    QUEUED = "queued"
    PREPROCESSING = "preprocessing"
    ASSESSING = "assessing"
    RECONSTRUCTING = "reconstructing"
    VOXELIZING = "voxelizing"
    MAPPING_BLOCKS = "mapping_blocks"
    EXPORTING = "exporting"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_JOB_STATUSES = {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}


@dataclass(frozen=True, slots=True)
class Issue:
    code: str
    severity: str
    message: str
    remedies: tuple[str, ...] = ()
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "remedies": list(self.remedies),
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True, slots=True)
class SufficiencyReport:
    verdict: str
    sufficient: bool
    agent_action: str
    score: float
    route: str
    issues: tuple[Issue, ...] = ()
    policy_version: str = "sufficiency-v1"

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "schemaVersion": 1,
            "policyVersion": self.policy_version,
            "route": self.route,
            "verdict": self.verdict,
            "sufficient": self.sufficient,
            "agentAction": self.agent_action,
            "score": round(self.score, 4),
            "issues": [issue.to_dict() for issue in self.issues],
        }
        payload["contentHash"] = content_hash(payload)
        return payload


@dataclass(frozen=True, slots=True)
class SensePack:
    width: int
    height: int
    analysis_width: int
    analysis_height: int
    foreground_ratio: float
    foreground_bounds: tuple[int, int, int, int] | None
    touches_frame: bool
    component_count: int
    matte_confidence: float
    source_mode: str

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "schemaVersion": 1,
            "source": {"width": self.width, "height": self.height},
            "analysisSize": [self.analysis_width, self.analysis_height],
            "diagnostics": {
                "foregroundRatio": round(self.foreground_ratio, 6),
                "foregroundBounds": list(self.foreground_bounds) if self.foreground_bounds else None,
                "touchesFrame": self.touches_frame,
                "componentCount": self.component_count,
                "matteConfidence": round(self.matte_confidence, 4),
                "sourceMode": self.source_mode,
            },
        }
        payload["contentHash"] = content_hash(payload)
        return payload


@dataclass(frozen=True, slots=True)
class AssetManifest:
    asset_id: str
    origin: AssetOrigin
    evidence_class: EvidenceClass
    content_type: str
    byte_size: int
    sha256: str
    width: int
    height: int
    original_file_name: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.origin in {AssetOrigin.GENERATED, AssetOrigin.EDITED} and self.evidence_class == EvidenceClass.OBSERVED:
            raise ValueError("generated or edited assets cannot be classified as observed")

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "schemaVersion": 1,
            "assetId": self.asset_id,
            "kind": "image",
            "origin": self.origin.value,
            "evidenceClass": self.evidence_class.value,
            "contentType": self.content_type,
            "byteSize": self.byte_size,
            "sha256": self.sha256,
            "width": self.width,
            "height": self.height,
            "originalFileName": self.original_file_name,
            "provenance": dict(self.provenance),
        }
        payload["contentHash"] = content_hash(payload)
        return payload


@dataclass(frozen=True, slots=True)
class ConversionSettings:
    max_axis: int = 32
    fill_mode: FillMode = FillMode.HOLLOW
    strategy: str = "relief"
    palette_profile: str = "safe-basic"
    target_minecraft_version: str = "1.20.4"
    data_version: int = 3700

    def __post_init__(self) -> None:
        if self.max_axis not in {16, 32, 64}:
            raise ValueError("max_axis must be one of 16, 32, or 64")
        if self.strategy != "relief":
            raise ValueError("only the deterministic relief strategy is available in the local MVP")
        if self.palette_profile != "safe-basic":
            raise ValueError("only safe-basic palette is available in the local MVP")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": 1,
            "strategy": self.strategy,
            "resolution": {"mode": "max-axis", "value": self.max_axis},
            "fill": {"mode": self.fill_mode.value, "shellThickness": 1},
            "palette": {"profileId": self.palette_profile, "version": "java-safe-v1"},
            "target": {
                "edition": "java",
                "minecraftVersion": self.target_minecraft_version,
                "dataVersion": self.data_version,
            },
        }


@dataclass(slots=True)
class VoxelModel:
    width: int
    height: int
    length: int
    palette: tuple[str, ...]
    blocks: dict[tuple[int, int, int], int]
    mode: FillMode
    palette_version: str = "java-safe-v1"

    def __post_init__(self) -> None:
        if min(self.width, self.height, self.length) <= 0:
            raise ValueError("voxel dimensions must be positive")
        if not self.palette or self.palette[0] != "minecraft:air":
            raise ValueError("palette index zero must be minecraft:air")
        for (x, y, z), palette_index in self.blocks.items():
            if not (0 <= x < self.width and 0 <= y < self.height and 0 <= z < self.length):
                raise ValueError(f"block coordinate out of bounds: {(x, y, z)}")
            if not (0 < palette_index < len(self.palette)):
                raise ValueError(f"invalid occupied palette index: {palette_index}")

    def semantic_payload(self) -> dict[str, Any]:
        canonical_blocks = [
            [x, y, z, self.palette[index]]
            for (x, y, z), index in sorted(self.blocks.items(), key=lambda item: (item[0][1], item[0][2], item[0][0]))
        ]
        return {
            "schemaVersion": 1,
            "dimensions": [self.width, self.height, self.length],
            "axis": {"x": "right", "y": "up", "z": "front"},
            "mode": self.mode.value,
            "paletteVersion": self.palette_version,
            "blocks": canonical_blocks,
        }

    @property
    def semantic_hash(self) -> str:
        return content_hash(self.semantic_payload())

    def bom(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for index in self.blocks.values():
            state = self.palette[index]
            counts[state] = counts.get(state, 0) + 1
        return dict(sorted(counts.items()))

    def to_preview(self) -> dict[str, Any]:
        return {
            "schemaVersion": 1,
            "dimensions": {"width": self.width, "height": self.height, "length": self.length},
            "axis": {"x": "right", "y": "up", "z": "front"},
            "paletteVersion": self.palette_version,
            "palette": list(self.palette),
            "mode": self.mode.value,
            "blocks": [
                [x, y, z, index]
                for (x, y, z), index in sorted(self.blocks.items(), key=lambda item: (item[0][1], item[0][2], item[0][0]))
            ],
            "statistics": {
                "occupied": len(self.blocks),
                "blockTypes": len(self.bom()),
                "bom": self.bom(),
            },
            "semanticHash": self.semantic_hash,
        }
