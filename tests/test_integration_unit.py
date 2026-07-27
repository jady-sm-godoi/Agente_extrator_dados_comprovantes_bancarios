from io import BytesIO
from pathlib import Path

from bank_receipt_extractor.integration import _identify_type


def test_identify_type_pdf_by_extension():
    assert _identify_type("receipt.pdf", b"") == "pdf"


def test_identify_type_image_by_extension():
    assert _identify_type("photo.jpg", b"") == "image"


def test_identify_type_png_by_extension():
    assert _identify_type("photo.png", b"") == "image"


def test_identify_type_pdf_by_magic_bytes():
    assert _identify_type("unknown.txt", b"%PDF-1.4") == "pdf"


def test_identify_type_image_fallback():
    assert _identify_type("unknown.txt", b"random data") == "image"


def test_identify_type_bytesio_with_name():
    buf = BytesIO(b"data")
    buf.name = "comprovante.pdf"
    assert _identify_type(buf, b"data") == "pdf"


def test_identify_type_bytesio_without_name_fallback_image():
    buf = BytesIO(b"data")
    assert _identify_type(buf, b"data") == "image"


def test_identify_type_bytesio_without_name_pdf_magic():
    buf = BytesIO(b"data")
    assert _identify_type(buf, b"%PDF-1.4") == "pdf"


def test_identify_type_path_object():
    assert _identify_type(Path("doc.pdf"), b"") == "pdf"


def test_identify_type_jfif_extension():
    assert _identify_type("scan.jfif", b"") == "image"
