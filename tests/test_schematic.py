from __future__ import annotations

import gzip

import nbtlib
import pytest

from threecraft.contracts import FillMode, VoxelModel
from threecraft.errors import ThreeCraftError
from threecraft.schematic import decode_varints, encode_varint, read_schematic, write_schematic


def _model() -> VoxelModel:
    return VoxelModel(
        3,
        2,
        2,
        ("minecraft:air", "minecraft:stone", "minecraft:red_concrete"),
        {(0, 0, 0): 1, (2, 0, 1): 2, (1, 1, 0): 1},
        FillMode.HOLLOW,
    )


def test_varint_boundaries() -> None:
    values = [0, 1, 127, 128, 255, 300, 16384, 2**28 - 1]
    encoded = b"".join(encode_varint(value) for value in values)
    assert decode_varints(encoded, len(values)) == values
    with pytest.raises(ThreeCraftError, match="ends inside"):
        decode_varints(b"\x80", 1)


def test_schematic_semantic_round_trip_is_deterministic() -> None:
    model = _model()
    first = write_schematic(model, data_version=3700, minecraft_version="1.20.4")
    second = write_schematic(model, data_version=3700, minecraft_version="1.20.4")
    assert first == second
    document = read_schematic(first)
    assert document.version == 3
    assert document.data_version == 3700
    assert document.model.semantic_hash == model.semantic_hash
    assert document.model.bom() == model.bom()


def test_schematic_is_readable_by_independent_nbtlib(tmp_path) -> None:
    path = tmp_path / "model.schem"
    path.write_bytes(write_schematic(_model()))
    parsed = nbtlib.load(path, gzipped=True)
    schematic = parsed["Schematic"]
    assert int(schematic["Version"]) == 3
    assert int(schematic["DataVersion"]) == 3700
    assert int(schematic["Width"]) == 3
    assert set(schematic["Blocks"]["Palette"].keys()) == {
        "minecraft:air",
        "minecraft:red_concrete",
        "minecraft:stone",
    }
    assert len(bytes(schematic["Blocks"]["Data"])) == 12


def test_corrupt_schematic_is_rejected() -> None:
    with pytest.raises(ThreeCraftError) as invalid_gzip:
        read_schematic(b"not gzip")
    assert invalid_gzip.value.code == "SCHEMATIC_GZIP_INVALID"

    truncated_nbt = gzip.compress(b"\x0a\x00\x00")
    with pytest.raises(ThreeCraftError):
        read_schematic(truncated_nbt)
