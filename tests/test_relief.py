from __future__ import annotations

from threecraft.contracts import ConversionSettings, FillMode
from threecraft.imaging import analyze_canonical_image, canonicalize_image
from threecraft.relief import build_relief_voxel


def _inputs(data: bytes) -> tuple[bytes, bytes]:
    canonical = canonicalize_image(data)
    analysis = analyze_canonical_image(canonical.png_bytes, source_width=canonical.width, source_height=canonical.height)
    return canonical.png_bytes, analysis.mask_png


def test_relief_modes_have_expected_density(object_png: bytes) -> None:
    image, mask = _inputs(object_png)
    models = {
        mode: build_relief_voxel(image, mask, ConversionSettings(max_axis=16, fill_mode=mode))
        for mode in FillMode
    }
    assert len(models[FillMode.SURFACE].blocks) < len(models[FillMode.HOLLOW].blocks)
    assert len(models[FillMode.HOLLOW].blocks) <= len(models[FillMode.SOLID].blocks)
    for model in models.values():
        assert max(model.width, model.height, model.length) == 16
        assert model.palette[0] == "minecraft:air"
        assert model.blocks


def test_relief_is_deterministic(object_png: bytes) -> None:
    image, mask = _inputs(object_png)
    settings = ConversionSettings(max_axis=32, fill_mode=FillMode.HOLLOW)
    first = build_relief_voxel(image, mask, settings)
    second = build_relief_voxel(image, mask, settings)
    assert first.semantic_hash == second.semantic_hash
    assert first.to_preview() == second.to_preview()


def test_all_supported_resolutions(object_png: bytes) -> None:
    image, mask = _inputs(object_png)
    for axis in (16, 32, 64):
        model = build_relief_voxel(image, mask, ConversionSettings(max_axis=axis, fill_mode=FillMode.SURFACE))
        assert max(model.width, model.height, model.length) == axis
