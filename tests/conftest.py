from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image, ImageDraw


@pytest.fixture
def object_png() -> bytes:
    image = Image.new("RGBA", (320, 280), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((70, 35, 250, 250), radius=35, fill=(40, 130, 220, 255))
    draw.ellipse((115, 80, 145, 110), fill=(250, 250, 245, 255))
    draw.ellipse((175, 80, 205, 110), fill=(250, 250, 245, 255))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def empty_png() -> bytes:
    image = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
