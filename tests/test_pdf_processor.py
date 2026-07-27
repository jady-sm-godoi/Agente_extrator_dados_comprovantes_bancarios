from io import BytesIO

import pytest
from PIL import Image

from bank_receipt_extractor.processors.pdf_processor import PdfProcessor


def make_dummy_pdf() -> bytes:
    buf = BytesIO()
    buf.write(b"%PDF-1.4\n")
    buf.write(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    buf.write(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    buf.write(b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n")
    buf.write(b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n")
    buf.write(b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n190\n%%EOF")
    return buf.getvalue()


def test_process_valid_pdf_returns_bytes():
    pdf_bytes = make_dummy_pdf()
    result = PdfProcessor.process(pdf_bytes)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_process_valid_pdf_returns_jpeg():
    pdf_bytes = make_dummy_pdf()
    result = PdfProcessor.process(pdf_bytes)
    img = Image.open(BytesIO(result))
    assert img.format == "JPEG"


def test_process_valid_pdf_dimensions():
    pdf_bytes = make_dummy_pdf()
    result = PdfProcessor.process(pdf_bytes)
    img = Image.open(BytesIO(result))
    assert img.size[0] > 0
    assert img.size[1] > 0
    assert max(img.size) <= 2048


def test_process_invalid_pdf_raises_value_error():
    with pytest.raises(ValueError, match="processar o PDF"):
        PdfProcessor.process(b"\x00\x01\x02\x03")


def test_process_empty_bytes_raises_value_error():
    with pytest.raises(ValueError, match="processar o PDF"):
        PdfProcessor.process(b"")
