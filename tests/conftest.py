from collections.abc import Iterator
from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bank_receipt_extractor.agent import ExtractionResult
from bank_receipt_extractor.schemas import BankReceipt

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_receipt_data() -> dict:
    return {
        "valor": Decimal("1500.00"),
        "data_transacao": date(2024, 3, 15),
        "tipo": "PIX",
        "banco_origem": "Nu Pagamentos",
        "banco_destino": "Itaú Unibanco",
        "favorecido": "Maria Souza",
        "numero_controle": "A1B2C3D4",
    }


@pytest.fixture
def sample_bank_receipt(sample_receipt_data: dict) -> BankReceipt:
    return BankReceipt(**sample_receipt_data)


@pytest.fixture
def valid_jpeg_bytes() -> bytes:
    from PIL import Image

    img = Image.new("RGB", (100, 50), color="white")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return buf.getvalue()


@pytest.fixture
def whatsapp_receipt_path() -> Path:
    path = (
        Path(__file__).resolve().parent.parent
        / "WhatsApp Image 2026-07-14 at 06.34.29.jpeg"
    )
    if not path.exists():
        pytest.skip("WhatsApp receipt fixture not found")
    return path


@pytest.fixture
def mock_groq_agent(sample_bank_receipt: BankReceipt) -> Iterator[MagicMock]:
    mock_agent = MagicMock()
    mock_agent.run.return_value.content = sample_bank_receipt
    with patch("bank_receipt_extractor.integration.extract_from_image") as mock_extract:
        mock_extract.return_value = ExtractionResult(sample_bank_receipt)
        yield mock_extract


@pytest.fixture
def mock_groq_agent_fails() -> Iterator[MagicMock]:
    with patch("bank_receipt_extractor.integration.extract_from_image") as mock_extract:
        mock_extract.side_effect = ValueError("Falha simulada no Groq")
        yield mock_extract
