from io import BytesIO
from unittest.mock import patch

from bank_receipt_extractor.integration import extract_receipt


def test_extract_receipt_str_path(whatsapp_receipt_path, mock_groq_agent):
    result = extract_receipt(str(whatsapp_receipt_path))
    assert "erro" not in result
    assert result["tipo"] == "PIX"
    assert result["valor"] == 1500.00


def test_extract_receipt_path_object(whatsapp_receipt_path, mock_groq_agent):
    result = extract_receipt(whatsapp_receipt_path)
    assert "erro" not in result
    assert result["valor"] == 1500.00


def test_extract_receipt_bytesio(valid_jpeg_bytes, mock_groq_agent):
    buf = BytesIO(valid_jpeg_bytes)
    buf.name = "comprovante.jpg"
    result = extract_receipt(buf)
    assert "erro" not in result
    assert result["tipo"] == "PIX"


def test_extract_receipt_file_like(valid_jpeg_bytes, mock_groq_agent):
    class FileLike:
        def __init__(self, data):
            self.data = data
            self.name = "receipt.png"

        def read(self):
            return self.data

    result = extract_receipt(FileLike(valid_jpeg_bytes))
    assert "erro" not in result


def test_extract_receipt_unsupported_format(mock_groq_agent):
    buf = BytesIO(b"some text content")
    buf.name = "arquivo.txt"
    result = extract_receipt(buf)
    assert "erro" in result


def test_extract_receipt_file_not_found():
    result = extract_receipt("/caminho/inexistente/arquivo.pdf")
    assert "erro" in result


def test_extract_receipt_serialization(sample_bank_receipt):
    with (
        patch("bank_receipt_extractor.integration._read_file") as mock_read,
        patch("bank_receipt_extractor.integration._identify_type") as mock_type,
        patch("bank_receipt_extractor.processors.image_processor.ImageProcessor.process") as mock_processor,
        patch("bank_receipt_extractor.integration.extract_from_image") as mock_extract,
    ):
        mock_read.return_value = b"fake-bytes"
        mock_type.return_value = "image"
        mock_processor.return_value = b"processed-image-bytes"
        mock_extract.return_value = sample_bank_receipt
        result = extract_receipt("dummy.jpg")
    assert isinstance(result["valor"], float)
    assert isinstance(result["data_transacao"], str)
    assert result["valor"] == 1500.00
    assert result["data_transacao"] == "2024-03-15"


def test_extract_receipt_agent_error(valid_jpeg_bytes):
    with patch("bank_receipt_extractor.integration.extract_from_image") as mock_extract:
        mock_extract.side_effect = ValueError("Falha simulada no Groq")
        buf = BytesIO(valid_jpeg_bytes)
        buf.name = "test.jpg"
        result = extract_receipt(buf)
        assert "erro" in result
        assert "Falha simulada" in result["erro"]


def test_extract_receipt_unsupported_file_type():
    result = extract_receipt(42)
    assert "erro" in result
    assert "não suportado" in result["erro"]


def test_extract_receipt_bytesio_without_name(valid_jpeg_bytes, mock_groq_agent):
    buf = BytesIO(valid_jpeg_bytes)
    result = extract_receipt(buf)
    assert "erro" not in result
    assert result["tipo"] == "PIX"


def test_extract_receipt_unexpected_exception():
    with (
        patch("bank_receipt_extractor.integration._read_file") as mock_read,
    ):
        mock_read.side_effect = RuntimeError("explodiu")
        result = extract_receipt("dummy.jpg")
    assert "erro" in result
    assert "inesperado" in result["erro"]


def test_extract_receipt_pdf_flow(sample_bank_receipt):
    with (
        patch("bank_receipt_extractor.integration._read_file") as mock_read,
        patch("bank_receipt_extractor.integration._identify_type") as mock_type,
        patch("bank_receipt_extractor.processors.pdf_processor.PdfProcessor.process") as mock_pdf,
        patch("bank_receipt_extractor.integration.extract_from_image") as mock_extract,
    ):
        mock_read.return_value = b"%PDF-fake-bytes"
        mock_type.return_value = "pdf"
        mock_pdf.return_value = b"fake-image-bytes"
        mock_extract.return_value = sample_bank_receipt
        result = extract_receipt("receipt.pdf")
    assert "erro" not in result
    mock_pdf.assert_called_once()
    mock_extract.assert_called_once()


def test_extract_receipt_image_flow(sample_bank_receipt):
    with (
        patch("bank_receipt_extractor.integration._read_file") as mock_read,
        patch("bank_receipt_extractor.integration._identify_type") as mock_type,
        patch("bank_receipt_extractor.processors.image_processor.ImageProcessor.process") as mock_img,
        patch("bank_receipt_extractor.integration.extract_from_image") as mock_extract,
    ):
        mock_read.return_value = b"fake-image-bytes"
        mock_type.return_value = "image"
        mock_img.return_value = b"processed-image-bytes"
        mock_extract.return_value = sample_bank_receipt
        result = extract_receipt("receipt.jpg")
    assert "erro" not in result
    mock_img.assert_called_once()
    mock_extract.assert_called_once()
