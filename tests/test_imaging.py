from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image

from threecraft.errors import ThreeCraftError
from threecraft.imaging import analyze_canonical_image, canonicalize_image
from threecraft.sufficiency import assess_sufficiency


def test_valid_png_is_canonicalized_and_assessed(object_png: bytes) -> None:
    canonical = canonicalize_image(object_png, declared_content_type="image/png")
    assert canonical.source_format == "PNG"
    assert canonical.width == 320
    assert canonical.height == 280
    analysis = analyze_canonical_image(canonical.png_bytes, source_width=canonical.width, source_height=canonical.height)
    assert analysis.sense.source_mode == "alpha"
    assert 0.2 < analysis.sense.foreground_ratio < 0.8
    assert analysis.sense.foreground_bounds is not None
    report = assess_sufficiency(analysis.sense)
    assert report.sufficient is True
    assert report.agent_action == "continue"


def test_empty_alpha_is_rejected(empty_png: bytes) -> None:
    canonical = canonicalize_image(empty_png)
    analysis = analyze_canonical_image(canonical.png_bytes, source_width=300, source_height=300)
    report = assess_sufficiency(analysis.sense)
    assert report.verdict == "reject"
    assert report.agent_action == "abort"
    assert "FOREGROUND_EMPTY" in {issue.code for issue in report.issues}


def test_small_image_is_rejected() -> None:
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    for x in range(10, 54):
        for y in range(10, 54):
            image.putpixel((x, y), (255, 0, 0, 255))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    canonical = canonicalize_image(buffer.getvalue())
    analysis = analyze_canonical_image(canonical.png_bytes, source_width=64, source_height=64)
    report = assess_sufficiency(analysis.sense)
    assert report.verdict == "reject"
    assert "RESOLUTION_TOO_LOW" in {issue.code for issue in report.issues}


def test_invalid_and_mismatched_files_fail_closed(object_png: bytes) -> None:
    with pytest.raises(ThreeCraftError) as invalid:
        canonicalize_image(b"not an image")
    assert invalid.value.code == "IMAGE_DECODE_FAILED"

    with pytest.raises(ThreeCraftError) as mismatch:
        canonicalize_image(object_png, declared_content_type="image/jpeg")
    assert mismatch.value.code == "CONTENT_TYPE_MISMATCH"
