"""Command-line entry point for source selection, conversion, and API serving."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Sequence

from .contracts import ConversionSettings, FillMode
from .imaging import read_image_file
from .pipeline import DEFAULT_GENERATION_PROMPT, ThreeCraftPipeline
from .storage import LocalArtifactStore


def _add_conversion_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--out", default="threecraft-output")
    parser.add_argument("--max-axis", type=int, choices=(16, 32, 64), default=32)
    parser.add_argument("--fill", choices=[mode.value for mode in FillMode], default=FillMode.HOLLOW.value)


def _copy_conversion_outputs(pipeline: ThreeCraftPipeline, result: dict, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    job_dir = pipeline.store.job_dir(result["jobId"])
    for file_name in ("model.schem", "preview.json", "blocks.json", "delivery.json"):
        shutil.copy2(job_dir / file_name, output / file_name)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="threecraft", description="Image-to-Minecraft relief pipeline")
    parser.add_argument("--data-dir", default=".threecraft-data", help="Private artifact directory")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser(
        "build",
        help="Use a supplied image when present; otherwise generate one, then convert it",
    )
    build.add_argument("--image", help="Optional PNG, JPEG, or WebP source; takes precedence over --prompt")
    build.add_argument("--prompt", default=DEFAULT_GENERATION_PROMPT, help="Generation fallback when --image is absent")
    _add_conversion_options(build)

    convert = sub.add_parser("convert", help="Convert an existing image into a .schem and preview")
    convert.add_argument("image")
    _add_conversion_options(convert)

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
        print(json.dumps({"assetId": asset_id, "output": str(output_path.resolve())}))
        return 0

    if args.command == "build":
        image_path = Path(args.image) if args.image else None
        source_summary = pipeline.resolve_source(
            image_data=read_image_file(image_path) if image_path is not None else None,
            prompt=args.prompt,
            file_name=image_path.name if image_path is not None else None,
            content_type=None,
        )
    elif args.command == "convert":
        image_path = Path(args.image)
        source_summary = pipeline.ingest_upload(
            read_image_file(image_path),
            file_name=image_path.name,
            content_type=None,
        )
    else:
        return 2

    asset = source_summary["asset"]
    settings = ConversionSettings(max_axis=args.max_axis, fill_mode=FillMode(args.fill))
    result = pipeline.convert(asset["assetId"], settings)
    output = Path(args.out)
    _copy_conversion_outputs(pipeline, result, output)
    print(
        json.dumps(
            {
                "output": str(output.resolve()),
                "sourceAssetId": asset["assetId"],
                "sourceOrigin": asset["origin"],
                **result["summary"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
