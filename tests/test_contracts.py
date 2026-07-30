from __future__ import annotations

import pytest

from threecraft.contracts import (
    AssetManifest,
    AssetOrigin,
    ConversionSettings,
    EvidenceClass,
    FillMode,
    VoxelModel,
)
from threecraft.hashing import canonical_json_text, content_hash


def test_canonical_hash_is_key_order_independent() -> None:
    assert content_hash({"b": 2, "a": 1}) == content_hash({"a": 1, "b": 2})
    assert canonical_json_text({"message": "café"}).endswith("\n")


def test_canonical_json_rejects_nan() -> None:
    with pytest.raises(ValueError):
        canonical_json_text({"value": float("nan")})


def test_generated_asset_cannot_be_observed() -> None:
    with pytest.raises(ValueError, match="cannot be classified"):
        AssetManifest(
            asset_id="ast_" + "a" * 32,
            origin=AssetOrigin.GENERATED,
            evidence_class=EvidenceClass.OBSERVED,
            content_type="image/png",
            byte_size=1,
            sha256="x",
            width=1,
            height=1,
        )


def test_conversion_settings_fail_closed() -> None:
    with pytest.raises(ValueError, match="max_axis"):
        ConversionSettings(max_axis=24)
    with pytest.raises(ValueError, match="only the deterministic relief"):
        ConversionSettings(strategy="single-image-mesh")


def test_voxel_semantic_hash_uses_states_not_palette_order() -> None:
    first = VoxelModel(
        2,
        1,
        1,
        ("minecraft:air", "minecraft:red_concrete", "minecraft:blue_concrete"),
        {(0, 0, 0): 1, (1, 0, 0): 2},
        FillMode.SOLID,
    )
    second = VoxelModel(
        2,
        1,
        1,
        ("minecraft:air", "minecraft:blue_concrete", "minecraft:red_concrete"),
        {(0, 0, 0): 2, (1, 0, 0): 1},
        FillMode.SOLID,
    )
    assert first.semantic_hash == second.semantic_hash
    assert first.bom() == second.bom()


def test_voxel_rejects_out_of_bounds_and_air_as_occupied() -> None:
    with pytest.raises(ValueError, match="out of bounds"):
        VoxelModel(1, 1, 1, ("minecraft:air", "minecraft:stone"), {(1, 0, 0): 1}, FillMode.SOLID)
    with pytest.raises(ValueError, match="occupied palette"):
        VoxelModel(1, 1, 1, ("minecraft:air", "minecraft:stone"), {(0, 0, 0): 0}, FillMode.SOLID)
