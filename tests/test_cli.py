from __future__ import annotations

import json

import nbtlib

from threecraft.cli import main
from threecraft.schematic import read_schematic


def test_cli_generate_then_convert(tmp_path, capsys) -> None:
    data_dir = tmp_path / "private-data"
    generated = tmp_path / "nested" / "generated.png"

    assert main([
        "--data-dir",
        str(data_dir),
        "generate",
        "blue crystal guardian",
        "--out",
        str(generated),
    ]) == 0
    generated_result = json.loads(capsys.readouterr().out)
    assert generated_result["assetId"].startswith("ast_")
    assert generated_result["output"] == str(generated.resolve())
    assert generated.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")

    output = tmp_path / "converted"
    assert main([
        "--data-dir",
        str(data_dir),
        "convert",
        str(generated),
        "--max-axis",
        "16",
        "--fill",
        "hollow",
        "--out",
        str(output),
    ]) == 0
    converted_result = json.loads(capsys.readouterr().out)
    assert converted_result["output"] == str(output.resolve())
    assert converted_result["occupied"] > 0
    assert converted_result["blockTypes"] > 0
    assert {path.name for path in output.iterdir()} == {
        "blocks.json",
        "delivery.json",
        "model.schem",
        "preview.json",
    }

    schematic_path = output / "model.schem"
    document = read_schematic(schematic_path.read_bytes())
    assert document.version == 3
    assert document.data_version == 3700
    assert len(document.model.blocks) == converted_result["occupied"]

    independent = nbtlib.load(schematic_path, gzipped=True)["Schematic"]
    assert int(independent["Version"]) == 3
    assert int(independent["DataVersion"]) == 3700
