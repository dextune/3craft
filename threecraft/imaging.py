"""Safe image canonicalization and deterministic CPU sense analysis."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps, UnidentifiedImageError

from .contracts import SensePack
from .errors import ThreeCraftError
from .hashing import sha256_bytes

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 24_000_000
MAX_ANALYSIS_SIDE = 512
_ALLOWED_FORMATS = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}


@dataclass(frozen=True, slots=True)
class CanonicalizedImage:
    png_bytes: bytes
    width: int
    height: int
    source_format: str
    source_sha256: str
    canonical_sha256: str


@dataclass(frozen=True, slots=True)
class ImageAnalysis:
    sense: SensePack
    mask_png: bytes
    depth_png: bytes


def safe_display_name(file_name: str | None) -> str | None:
    if not file_name:
        return None
    value = file_name.replace("\\", "/").split("/")[-1].strip()
    return value[:200] or None


def canonicalize_image(data: bytes, *, declared_content_type: str | None = None) -> CanonicalizedImage:
    if not data:
        raise ThreeCraftError("FILE_EMPTY", "The uploaded file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise ThreeCraftError("IMAGE_TOO_LARGE", "Image files must be 10 MB or smaller.", status_code=413)

    try:
        with Image.open(BytesIO(data)) as source:
            source_format = str(source.format or "").upper()
            if source_format not in _ALLOWED_FORMATS:
                raise ThreeCraftError("FILE_UNSUPPORTED", "Only PNG, JPEG, and WebP images are supported.")
            if getattr(source, "n_frames", 1) != 1:
                raise ThreeCraftError("ANIMATED_IMAGE_UNSUPPORTED", "Animated images are not supported.")
            if source.width <= 0 or source.height <= 0 or source.width * source.height > MAX_PIXELS:
                raise ThreeCraftError("IMAGE_DIMENSIONS_INVALID", "The image dimensions are outside the allowed range.", status_code=413)
            expected_type = _ALLOWED_FORMATS[source_format]
            if declared_content_type and declared_content_type not in {expected_type, "application/octet-stream"}:
                raise ThreeCraftError("CONTENT_TYPE_MISMATCH", "The file content does not match the declared image type.")
            source.load()
            oriented = ImageOps.exif_transpose(source)
            rgba = oriented.convert("RGBA")
    except ThreeCraftError:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ThreeCraftError("IMAGE_DECODE_FAILED", "The image file could not be decoded.") from exc

    output = BytesIO()
    rgba.save(output, format="PNG", optimize=False, compress_level=9)
    canonical = output.getvalue()
    return CanonicalizedImage(
        png_bytes=canonical,
        width=rgba.width,
        height=rgba.height,
        source_format=source_format,
        source_sha256=sha256_bytes(data),
        canonical_sha256=sha256_bytes(canonical),
    )


def _analysis_image(png_bytes: bytes) -> Image.Image:
    with Image.open(BytesIO(png_bytes)) as source:
        image = source.convert("RGBA")
    image.thumbnail((MAX_ANALYSIS_SIDE, MAX_ANALYSIS_SIDE), Image.Resampling.LANCZOS)
    return image


def _heuristic_mask(image: Image.Image) -> tuple[Image.Image, str]:
    alpha = image.getchannel("A")
    minimum, maximum = alpha.getextrema()
    if minimum < 250 and maximum > 0:
        mask = alpha.point(lambda value: 255 if value >= 16 else 0, mode="L")
        return mask, "alpha"

    rgb = image.convert("RGB")
    width, height = rgb.size
    sample_points = (
        (0, 0),
        (width - 1, 0),
        (0, height - 1),
        (width - 1, height - 1),
    )
    samples = [rgb.getpixel(point) for point in sample_points]
    background = tuple(sum(pixel[channel] for pixel in samples) // len(samples) for channel in range(3))
    values = []
    for red, green, blue in rgb.get_flattened_data():
        distance = abs(red - background[0]) + abs(green - background[1]) + abs(blue - background[2])
        values.append(255 if distance >= 42 else 0)
    mask = Image.new("L", rgb.size)
    mask.putdata(values)
    if width >= 3 and height >= 3:
        mask = mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    return mask, "corner-background"


def _component_count(mask: Image.Image) -> int:
    width, height = mask.size
    occupied = bytearray(1 if value else 0 for value in mask.get_flattened_data())
    count = 0
    for start, value in enumerate(occupied):
        if not value:
            continue
        count += 1
        occupied[start] = 0
        queue: deque[int] = deque([start])
        while queue:
            current = queue.popleft()
            x, y = current % width, current // width
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < width and 0 <= ny < height:
                    index = ny * width + nx
                    if occupied[index]:
                        occupied[index] = 0
                        queue.append(index)
    return count


def analyze_canonical_image(png_bytes: bytes, *, source_width: int, source_height: int) -> ImageAnalysis:
    image = _analysis_image(png_bytes)
    mask, source_mode = _heuristic_mask(image)
    bbox = mask.getbbox()
    occupied = sum(1 for value in mask.get_flattened_data() if value)
    total = max(1, mask.width * mask.height)
    ratio = occupied / total

    touches = False
    if bbox:
        left, top, right, bottom = bbox
        touches = left == 0 or top == 0 or right == mask.width or bottom == mask.height

    confidence = 0.96 if source_mode == "alpha" else 0.78
    if touches:
        confidence -= 0.15
    if ratio < 0.01 or ratio > 0.97:
        confidence -= 0.25
    confidence = max(0.0, min(1.0, confidence))

    sense = SensePack(
        width=source_width,
        height=source_height,
        analysis_width=image.width,
        analysis_height=image.height,
        foreground_ratio=ratio,
        foreground_bounds=bbox,
        touches_frame=touches,
        component_count=_component_count(mask) if occupied else 0,
        matte_confidence=confidence,
        source_mode=source_mode,
    )

    mask_buffer = BytesIO()
    mask.save(mask_buffer, format="PNG", optimize=False, compress_level=9)
    grayscale = ImageOps.grayscale(image.convert("RGB"))
    depth = ImageOps.invert(grayscale)
    depth = Image.composite(depth, Image.new("L", depth.size, 0), mask)
    depth_buffer = BytesIO()
    depth.save(depth_buffer, format="PNG", optimize=False, compress_level=9)
    return ImageAnalysis(sense=sense, mask_png=mask_buffer.getvalue(), depth_png=depth_buffer.getvalue())


def open_canonical(png_bytes: bytes) -> Image.Image:
    with Image.open(BytesIO(png_bytes)) as source:
        return source.convert("RGBA")


def read_image_file(path: str | Path) -> bytes:
    try:
        return Path(path).read_bytes()
    except OSError as exc:
        raise ThreeCraftError("FILE_MISSING", f"The image file could not be read: {path}") from exc
