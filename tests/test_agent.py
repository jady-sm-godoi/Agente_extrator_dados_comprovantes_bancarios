from unittest.mock import MagicMock, patch

import pytest

from bank_receipt_extractor.agent import extract_from_image, get_agent
from bank_receipt_extractor.schemas import BankReceipt


def test_get_agent_returns_agent():
    agent = get_agent()
    assert agent is not None
    assert hasattr(agent, "run")


def test_get_agent_singleton():
    a1 = get_agent()
    a2 = get_agent()
    assert a1 is a2


def test_get_agent_respects_env_model(monkeypatch):
    monkeypatch.setenv("GROQ_MODEL", "llama-3.2-90b-vision-preview")
    agent = get_agent()
    assert "llama-3.2-90b-vision-preview" in agent.model.id


def test_get_agent_sets_timeout(monkeypatch):
    import bank_receipt_extractor.agent as agent_mod

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_MODEL", "__test_timeout_model__")
    agent_mod._agent = None
    try:
        agent = agent_mod.get_agent()
        assert agent.model.timeout == 30
    finally:
        agent_mod._agent = None


def test_extract_from_image_success(sample_bank_receipt):
    mock_agent = MagicMock()
    mock_agent.run.return_value.content = sample_bank_receipt
    with patch("bank_receipt_extractor.agent.get_agent", return_value=mock_agent):
        result = extract_from_image(b"fake-image-bytes")
    assert isinstance(result, BankReceipt)
    assert result.valor == sample_bank_receipt.valor
    assert result.tipo == "PIX"


def test_extract_from_image_returns_dict(sample_receipt_data):
    mock_agent = MagicMock()
    mock_agent.run.return_value.content = sample_receipt_data
    with patch("bank_receipt_extractor.agent.get_agent", return_value=mock_agent):
        result = extract_from_image(b"fake-image-bytes")
    assert isinstance(result, BankReceipt)
    assert result.valor == sample_receipt_data["valor"]


def test_extract_from_image_no_content():
    mock_agent = MagicMock()
    mock_agent.run.return_value.content = None
    with patch("bank_receipt_extractor.agent.get_agent", return_value=mock_agent), pytest.raises(ValueError, match="não retornou dados"):
        extract_from_image(b"fake-image-bytes")


def test_extract_from_image_invalid_content_type():
    mock_agent = MagicMock()
    mock_agent.run.return_value.content = ["not", "valid"]
    with patch("bank_receipt_extractor.agent.get_agent", return_value=mock_agent), pytest.raises(ValueError, match="Resposta inesperada"):
        extract_from_image(b"fake-image-bytes")


def test_extract_from_image_invalid_dict():
    mock_agent = MagicMock()
    mock_agent.run.return_value.content = {"valor": "invalido"}
    with patch("bank_receipt_extractor.agent.get_agent", return_value=mock_agent), pytest.raises(ValueError):
        extract_from_image(b"fake-image-bytes")
