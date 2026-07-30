"""Command-line entry point for local conversion and API serving."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Sequence

from .contracts import ConversionSettings, FillMode
from .imaging import read_image_file
from .pipeline import ThreeCraftPipeline
from .storage import LocalArtifactStore


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="threecraft", description="Image-to-Minecraft relief pipeline")
    parser.add_argument("--data-dir", default=".threecraft-data", help="Private artifact directory")
    sub = parser.add_subparsers(dest="command", required=True)

    convert = sub.add_parser("convert", help="Convert an image into a .schem and preview")
    convert.add_argument("image")
    convert.add_argument("--out", default="threecraft-output")
    convert.add_argument("--max-axis", type=int, choices=(16, 32, 64), default=32)
    convert.add_argument("--fill", choices=[mode.value for mode in FillMode], default=FillMode.HOLLOW.value)

    generate = sub.add_parser("generate", help="Create a deterministic development illustration")
    generate.add_argument("prompt")
    generate.add_argument("--out", default="generated-dev.png")

    serve = sub.add_parser("serve", help="Run the local FastAPI server")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    if args.command == "serve":
        import os
        import uvicorn

        os.environ["THREECRAFT_DATA_DIR"] = str(Path(args.data_dir).resolve())
        uvicorn.run("threecraft.api:create_app", factory=True, host=args.host, port=args.port, reload=False)
        return 0

    store = LocalArtifactStore(args.data_dir)
    pipeline = ThreeCraftPipeline(store)

    if args.command == "generate":
        summary = pipeline.generate_image(args.prompt)
        asset_id = summary["asset"]["assetId"]
        source = store.asset_dir(asset_id) / "source.png"
        output_path = Path(args.out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, output_path)
        print(json.dumps({"assetId": asset_id, "output": str(output_path.resolve())}, ensure_ascii=False))
        return 0

    if args.command == "convert":
        image_path = Path(args.image)
        summary = pipeline.ingest_upload(
            read_image_file(image_path),
            file_name=image_path.name,
            content_type=None,
        )
        asset_id = summary["asset"]["assetId"]
        settings = ConversionSettings(max_axis=args.max_axis, fill_mode=FillMode(args.fill))
        result = pipeline.convert(asset_id, settings)
        output = Path(args.out)
        output.mkdir(parents=True, exist_ok=True)
        job_dir = store.job_dir(result["jobId"])
        for file_name in ("model.schem", "preview.json", "blocks.json", "delivery.json"):
            shutil.copy2(job_dir / file_name, output / file_name)
        print(json.dumps({"output": str(output.resolve()), **result["summary"]}, ensure_ascii=False))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
