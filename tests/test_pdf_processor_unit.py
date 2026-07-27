from unittest.mock import patch

import pytest

from bank_receipt_extractor.processors.pdf_processor import PdfProcessor


def test_process_pdf_empty_pages_raises():
    with patch(
        "bank_receipt_extractor.processors.pdf_processor.convert_from_bytes",
        return_value=[],
    ), pytest.raises(ValueError, match="não contém páginas"):
        PdfProcessor.process(b"fake-pdf-bytes")
