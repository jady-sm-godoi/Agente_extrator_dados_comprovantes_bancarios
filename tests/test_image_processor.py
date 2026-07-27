from io import BytesIO

import pytest
from PIL import Image

from bank_receipt_extractor.processors.image_processor import ImageProcessor


def test_process_rgb_jpeg_returns_bytes():
    img = Image.new("RGB", (100, 50), color="white")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    result = ImageProcessor.process(buf.getvalue())
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_process_valid_jpeg():
    result = ImageProcessor.process(_make_jpeg_bytes(200, 100))
    img = Image.open(BytesIO(result))
    assert img.format == "JPEG"


def test_process_rgba_converts_to_rgb():
    img = Image.new("RGBA", (100, 50), color=(255, 0, 0, 128))
    buf = BytesIO()
    img.save(buf, format="PNG")
    result = ImageProcessor.process(buf.getvalue())
    img_out = Image.open(BytesIO(result))
    assert img_out.mode == "RGB"


def test_process_p_converts_to_rgb():
    img = Image.new("P", (100, 50))
    buf = BytesIO()
    img.save(buf, format="PNG")
    result = ImageProcessor.process(buf.getvalue())
    img_out = Image.open(BytesIO(result))
    assert img_out.mode == "RGB"


def test_process_resize_large_image():
    result = ImageProcessor.process(_make_jpeg_bytes(4000, 3000))
    img = Image.open(BytesIO(result))
    assert max(img.size) <= ImageProcessor.MAX_DIMENSION


def test_process_resize_preserves_aspect_ratio():
    result = ImageProcessor.process(_make_jpeg_bytes(4000, 2000))
    img = Image.open(BytesIO(result))
    w, h = img.size
    original_ratio = 4000 / 2000
    new_ratio = w / h
    assert abs(new_ratio - original_ratio) < 0.01


def test_process_small_image_no_resize():
    result = ImageProcessor.process(_make_jpeg_bytes(800, 600))
    img = Image.open(BytesIO(result))
    assert img.size == (800, 600)


def test_process_quality_acceptable_size():
    result = ImageProcessor.process(_make_jpeg_bytes(2048, 2048, color="white"))
    img = Image.open(BytesIO(result))
    assert img.size == (2048, 2048)


def test_process_invalid_bytes_raises():
    with pytest.raises(OSError):
        ImageProcessor.process(b"\x00\x01\x02\x03")


def test_uses_jpeg_quality_85():
    result = ImageProcessor.process(_make_jpeg_bytes(500, 500, color=(128, 128, 128)))
    img = Image.open(BytesIO(result))
    assert img.format == "JPEG"


def test_process_whatsapp_receipt(whatsapp_receipt_path):
    raw = whatsapp_receipt_path.read_bytes()
    result = ImageProcessor.process(raw)
    img = Image.open(BytesIO(result))
    assert img.format == "JPEG"
    assert max(img.size) <= ImageProcessor.MAX_DIMENSION
    assert img.mode == "RGB"


def _make_jpeg_bytes(width: int, height: int, color=(0, 0, 0)) -> bytes:
    img = Image.new("RGB", (width, height), color=color)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()
