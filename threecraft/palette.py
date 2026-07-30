"""Curated safe full-cube Minecraft palette and deterministic color mapping."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PaletteEntry:
    block_state: str
    rgb: tuple[int, int, int]


SAFE_PALETTE: tuple[PaletteEntry, ...] = (
    PaletteEntry("minecraft:white_concrete", (207, 213, 214)),
    PaletteEntry("minecraft:light_gray_concrete", (125, 125, 115)),
    PaletteEntry("minecraft:gray_concrete", (54, 57, 61)),
    PaletteEntry("minecraft:black_concrete", (8, 10, 15)),
    PaletteEntry("minecraft:brown_concrete", (96, 59, 31)),
    PaletteEntry("minecraft:red_concrete", (142, 33, 33)),
    PaletteEntry("minecraft:orange_concrete", (224, 97, 0)),
    PaletteEntry("minecraft:yellow_concrete", (241, 175, 21)),
    PaletteEntry("minecraft:lime_concrete", (94, 169, 24)),
    PaletteEntry("minecraft:green_concrete", (73, 91, 36)),
    PaletteEntry("minecraft:cyan_concrete", (21, 119, 136)),
    PaletteEntry("minecraft:light_blue_concrete", (36, 137, 199)),
    PaletteEntry("minecraft:blue_concrete", (44, 46, 143)),
    PaletteEntry("minecraft:purple_concrete", (100, 31, 156)),
    PaletteEntry("minecraft:magenta_concrete", (169, 48, 159)),
    PaletteEntry("minecraft:pink_concrete", (214, 101, 143)),
)


def block_states() -> tuple[str, ...]:
    return ("minecraft:air",) + tuple(entry.block_state for entry in SAFE_PALETTE)


def _linear(channel: int) -> float:
    value = channel / 255.0
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def rgb_to_lab(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    r, g, b = (_linear(channel) for channel in rgb)
    x = (0.4124564 * r + 0.3575761 * g + 0.1804375 * b) / 0.95047
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = (0.0193339 * r + 0.1191920 * g + 0.9503041 * b) / 1.08883

    def f(value: float) -> float:
        delta = 6 / 29
        return value ** (1 / 3) if value > delta**3 else value / (3 * delta**2) + 4 / 29

    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


_PALETTE_LAB = tuple(rgb_to_lab(entry.rgb) for entry in SAFE_PALETTE)


def nearest_palette_index(rgb: tuple[int, int, int]) -> int:
    """Return an occupied VoxelModel palette index; zero is reserved for air."""

    lab = rgb_to_lab(rgb)
    best = min(
        range(len(SAFE_PALETTE)),
        key=lambda index: math.dist(lab, _PALETTE_LAB[index]),
    )
    return best + 1
