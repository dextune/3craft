"""Image generation provider ports.

The deterministic provider is deliberately labelled as a development illustration
provider. It never claims to be an AI image generator.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from io import BytesIO
from typing import Protocol

from PIL import Image, ImageDraw

from .errors import ThreeCraftError


@dataclass(frozen=True, slots=True)
class GeneratedImage:
    png_bytes: bytes
    provider: str
    model: str
    seed: int
    prompt: str


class ImageGenerationProvider(Protocol):
    name: str

    def generate(self, prompt: str) -> GeneratedImage: ...


class NullImageProvider:
    name = "null"

    def generate(self, prompt: str) -> GeneratedImage:
        raise ThreeCraftError(
            "IMAGE_PROVIDER_UNAVAILABLE",
            "No image generation provider is configured.",
            status_code=503,
            remedies=["upload-an-image", "configure-image-provider"],
        )


class DeterministicDevImageProvider:
    """Generate a labelled local test illustration from a prompt hash."""

    name = "deterministic-dev"
    model = "procedural-shapes-v1"

    def generate(self, prompt: str) -> GeneratedImage:
        normalized = prompt.strip()
        if not normalized:
            raise ThreeCraftError("PROMPT_EMPTY", "Enter an image-generation description.")
        if len(normalized) > 1000:
            raise ThreeCraftError("PROMPT_TOO_LONG", "The image-generation description must be 1,000 characters or fewer.")

        digest = hashlib.sha256(normalized.encode("utf-8")).digest()
        seed = int.from_bytes(digest[:8], "big")
        colors = (
            (214, 64, 69, 255),
            (45, 142, 214, 255),
            (90, 180, 95, 255),
            (225, 156, 50, 255),
            (145, 85, 205, 255),
        )
        primary = colors[digest[8] % len(colors)]
        accent = colors[digest[9] % len(colors)]
        image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image, "RGBA")
        draw.ellipse((120, 405, 392, 455), fill=(0, 0, 0, 42))

        shape = digest[10] % 4
        if shape == 0:
            draw.rounded_rectangle((155, 145, 357, 395), radius=48, fill=primary, outline=(35, 38, 44, 255), width=10)
            draw.rounded_rectangle((185, 85, 327, 205), radius=38, fill=accent, outline=(35, 38, 44, 255), width=10)
            draw.ellipse((213, 125, 241, 153), fill=(245, 245, 235, 255))
            draw.ellipse((271, 125, 299, 153), fill=(245, 245, 235, 255))
            draw.rectangle((105, 210, 155, 335), fill=accent, outline=(35, 38, 44, 255), width=8)
            draw.rectangle((357, 210, 407, 335), fill=accent, outline=(35, 38, 44, 255), width=8)
        elif shape == 1:
            draw.ellipse((130, 170, 380, 400), fill=primary, outline=(35, 38, 44, 255), width=10)
            draw.polygon(((175, 190), (115, 85), (225, 165)), fill=accent, outline=(35, 38, 44, 255))
            draw.polygon(((337, 190), (397, 85), (287, 165)), fill=accent, outline=(35, 38, 44, 255))
            draw.ellipse((190, 245, 225, 280), fill=(245, 245, 235, 255))
            draw.ellipse((287, 245, 322, 280), fill=(245, 245, 235, 255))
        elif shape == 2:
            draw.polygon(((256, 65), (382, 200), (335, 405), (177, 405), (130, 200)), fill=primary, outline=(35, 38, 44, 255))
            draw.polygon(((256, 65), (285, 215), (256, 365), (190, 215)), fill=accent)
            draw.line(((130, 200), (382, 200)), fill=(245, 245, 235, 180), width=8)
        else:
            draw.ellipse((115, 90, 397, 405), fill=primary, outline=(35, 38, 44, 255), width=12)
            draw.ellipse((175, 150, 337, 330), fill=accent, outline=(245, 245, 235, 220), width=8)
            draw.polygon(((256, 170), (282, 235), (352, 240), (298, 283), (315, 350), (256, 310), (197, 350), (214, 283), (160, 240), (230, 235)), fill=(245, 245, 235, 240))

        output = BytesIO()
        image.save(output, format="PNG", optimize=False, compress_level=9)
        return GeneratedImage(output.getvalue(), self.name, self.model, seed, normalized)
