"""Deterministic 2.5D relief-to-voxel implementation."""

from __future__ import annotations

import math
from io import BytesIO

from PIL import Image, ImageOps

from .contracts import ConversionSettings, FillMode, VoxelModel
from .errors import ThreeCraftError
from .palette import block_states, nearest_palette_index

_NEIGHBORS = ((-1, 0, 0), (1, 0, 0), (0, -1, 0), (0, 1, 0), (0, 0, -1), (0, 0, 1))


def _open(data: bytes, mode: str) -> Image.Image:
    with Image.open(BytesIO(data)) as image:
        return image.convert(mode)


def build_relief_voxel(
    image_png: bytes,
    mask_png: bytes,
    settings: ConversionSettings,
) -> VoxelModel:
    image = _open(image_png, "RGB")
    mask = _open(mask_png, "L")
    if image.size != mask.size:
        image = image.resize(mask.size, Image.Resampling.LANCZOS)
    bbox = mask.getbbox()
    if bbox is None:
        raise ThreeCraftError("FOREGROUND_EMPTY", "No foreground subject is available for conversion.")

    image = image.crop(bbox)
    mask = mask.crop(bbox)
    source_width, source_height = image.size
    if source_width >= source_height:
        width = settings.max_axis
        height = max(1, round(settings.max_axis * source_height / source_width))
    else:
        height = settings.max_axis
        width = max(1, round(settings.max_axis * source_width / source_height))

    image = image.resize((width, height), Image.Resampling.LANCZOS)
    mask = mask.resize((width, height), Image.Resampling.NEAREST)
    grayscale = ImageOps.grayscale(image)
    max_depth = max(2, settings.max_axis // 4)

    solid: dict[tuple[int, int, int], int] = {}
    column_depth: dict[tuple[int, int], int] = {}
    column_palette: dict[tuple[int, int], int] = {}

    for image_y in range(height):
        for x in range(width):
            if mask.getpixel((x, image_y)) < 16:
                continue
            y = height - 1 - image_y
            nx = (x + 0.5) / width
            ny = (image_y + 0.5) / height
            dome = max(0.0, math.sin(math.pi * nx) * math.sin(math.pi * ny))
            darkness = (255 - grayscale.getpixel((x, image_y))) / 255.0
            depth = 1 + round((max_depth - 1) * min(1.0, 0.72 * math.sqrt(dome) + 0.28 * darkness))
            depth = max(1, min(max_depth, depth))
            palette_index = nearest_palette_index(image.getpixel((x, image_y)))
            column_depth[(x, y)] = depth
            column_palette[(x, y)] = palette_index
            for z in range(depth):
                solid[(x, y, z)] = palette_index

    if not solid:
        raise ThreeCraftError("VOXEL_EMPTY", "No voxels could be generated from the image.")

    if settings.fill_mode == FillMode.SOLID:
        selected = solid
    elif settings.fill_mode == FillMode.SURFACE:
        selected = {
            (x, y, depth - 1): column_palette[(x, y)]
            for (x, y), depth in column_depth.items()
        }
    else:
        selected = {}
        occupied = set(solid)
        for coordinate, palette_index in solid.items():
            x, y, z = coordinate
            if any((x + dx, y + dy, z + dz) not in occupied for dx, dy, dz in _NEIGHBORS):
                selected[coordinate] = palette_index

    max_z = max(z for _, _, z in selected)
    return VoxelModel(
        width=width,
        height=height,
        length=max_z + 1,
        palette=block_states(),
        blocks=selected,
        mode=settings.fill_mode,
    )
