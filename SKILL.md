---
name: threecraft-image-to-schematic
description: Convert a supplied PNG, JPEG, or WebP into a validated Minecraft Java Sponge v3 schematic, or create a deterministic local fallback image only when no image is supplied. Use for image-to-Minecraft voxel sculpture, block bill-of-materials, preview, and .schem requests.
---

# 3Craft Image-to-Schematic Skill

Use the 3Craft repository in this skill folder to create a deterministic Minecraft Java Edition block relief, JSON preview, bill of materials, delivery manifest, and Sponge Schematic v3 file.

## Non-negotiable source policy

1. Inspect the files made available with the user request.
2. If the user supplied or explicitly referenced a supported image, use that image. Supported inputs are PNG, JPEG, and WebP.
3. A supplied image always takes precedence over a text prompt. Pass the prompt only as context; the pipeline ignores it while image bytes are present.
4. If no supported image is available, derive a short object description from the user request and use deterministic local generation.
5. If neither an image nor a useful description is available, use the built-in default prompt rather than stopping.
6. If a supplied image is corrupt, unsupported, oversized, or insufficient, report that validation result. Never silently replace an invalid supplied image with a generated one.
7. Never fetch an arbitrary image URL and never transmit user files to an external provider.

When several images are available, use the image explicitly named by the user. Otherwise use the most recently supplied supported image and state which file was selected.

## Environment preparation

Treat the directory containing this `SKILL.md` as `SKILL_DIR`. Run commands from that directory.

Before installing anything, check whether `.venv/bin/threecraft` exists. If it does not exist and package installation is allowed, prepare the local environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
```

Do not install frontend dependencies unless the user asks to run or modify the Web UI.

## Build workflow

Choose a new output directory. Do not delete or overwrite an unrelated existing directory.

### With a supplied image

```bash
.venv/bin/threecraft build \
  --image "$IMAGE_PATH" \
  --prompt "$USER_OBJECT_DESCRIPTION" \
  --max-axis 32 \
  --fill hollow \
  --out "$OUTPUT_DIR"
```

The `--image` value is authoritative. The prompt is not used to generate a replacement while an image is present.

### Without a supplied image

```bash
.venv/bin/threecraft build \
  --prompt "$USER_OBJECT_DESCRIPTION" \
  --max-axis 32 \
  --fill hollow \
  --out "$OUTPUT_DIR"
```

This uses the repository's `deterministic-dev` procedural provider. It is not an external AI image generator.

### Settings

- Default to `--max-axis 32`; use 16 for a small/fast result or 64 only when the user asks for more detail.
- Default to `--fill hollow` for a closed shell with a moderate block count.
- Use `surface` for the fewest blocks and a front-only relief.
- Use `solid` only when the user requests a filled result and accepts the larger block count.
- The target is Minecraft Java Edition 1.20.4, DataVersion 3700, Sponge Schematic v3.

## Required validation

A successful CLI exit is necessary but not sufficient. Confirm that all of these files exist in the output directory:

- `model.schem`
- `preview.json`
- `blocks.json`
- `delivery.json`

Read `delivery.json` and require:

- `status` is `passed`;
- every value in `gates` is `true`;
- the schematic artifact has a SHA-256 entry;
- a non-empty `semanticHash` is present.

Read `blocks.json` and report the total occupied block count and number of block types. Do not claim success or present `model.schem` as validated if any delivery gate fails.

If independent verification is requested, parse the output using the pinned `nbtlib` dependency and confirm Schematic version 3 and DataVersion 3700.

## Output handling

Return a concise result containing:

1. whether the source was `upload` or `generated`;
2. the selected image path, when applicable;
3. voxel dimensions, occupied block count, and block-type count;
4. fill mode and maximum axis;
5. the semantic hash;
6. paths to `model.schem`, `preview.json`, `blocks.json`, and `delivery.json`;
7. any sufficiency warnings or known limitations.

Keep uploaded images and generated artifacts local. Do not publish, upload, or share them unless the user explicitly requests that separate action.

## Accuracy and safety boundaries

- This implementation creates deterministic 2.5D reliefs. It does not reconstruct unseen 3D surfaces.
- Generated fallback images are design intent, never observed evidence.
- Do not describe `deterministic-dev` as AI generation.
- Do not claim WorldEdit compatibility beyond the validated Sponge v3 structure unless an actual Minecraft/WorldEdit import was performed.
- Do not expose the unauthenticated local API outside loopback.
- Preserve fail-closed behavior: candidate artifacts are usable only after all delivery gates pass.
