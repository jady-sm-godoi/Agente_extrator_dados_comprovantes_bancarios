from unittest.mock import MagicMock, patch

import pytest

from bank_receipt_extractor.agent import (
    _build_agent,
    _classificar_falha,
    _parse_model_list,
    _run_agent,
    extract_from_image,
    get_agent,
    reset_agent,
)
from bank_receipt_extractor.errors import ProviderError
from bank_receipt_extractor.schemas import BankReceipt


@pytest.fixture(autouse=True)
def _reset_agent():
    reset_agent()
    yield
    reset_agent()


def test_parse_model_list_default(monkeypatch):
    monkeypatch.delenv("MODEL_FALLBACK_LIST", raising=False)
    assert _parse_model_list() == ["deepseek:deepseek-flash"]


def test_parse_model_list_override(monkeypatch):
    monkeypatch.setenv(
        "MODEL_FALLBACK_LIST",
        "deepseek:deepseek-flash,groq:qwen/qwen3.8-27b",
    )
    assert _parse_model_list() == [
        "deepseek:deepseek-flash",
        "groq:qwen/qwen3.8-27b",
    ]


def test_parse_model_list_blank(monkeypatch):
    monkeypatch.setenv("MODEL_FALLBACK_LIST", "   , , ")
    assert _parse_model_list() == ["deepseek:deepseek-flash"]


def test_parse_model_list_dedupes_case_insensitive(monkeypatch):
    monkeypatch.setenv(
        "MODEL_FALLBACK_LIST",
        "deepseek:deepseek-flash,DEEPSEEK:deepseek-flash,groq:qwen/qwen3.8-27b",
    )
    assert _parse_model_list() == [
        "deepseek:deepseek-flash",
        "groq:qwen/qwen3.8-27b",
    ]


def test_build_agent_deepseek_default_provider(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    agent = _build_agent("deepseek-flash")
    assert isinstance(agent.model.id, str)
    assert agent.model.provider == "DeepSeek"


def test_build_agent_groq(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    agent = _build_agent("groq:qwen/qwen3.8-27b")
    assert agent.model.provider == "Groq"


def test_build_agent_invalid_provider():
    with pytest.raises(ValueError, match="não suportado"):
        _build_agent("bogus:model")


def test_get_agent_returns_agent(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    agent = get_agent()
    assert agent is not None
    assert hasattr(agent, "run")


def test_get_agent_singleton(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    a1 = get_agent()
    a2 = get_agent()
    assert a1 is a2


def test_extract_from_image_success(sample_bank_receipt, monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    mock_agent = MagicMock()
    mock_agent.model.provider = "DeepSeek"
    mock_agent.model.id = "deepseek-flash"
    mock_agent.run.return_value.content = sample_bank_receipt
    with patch("bank_receipt_extractor.agent._build_agent", return_value=mock_agent):
        result = extract_from_image(b"fake-image-bytes")
    assert isinstance(result.receipt, BankReceipt)
    assert result.receipt.valor == sample_bank_receipt.valor
    assert result.receipt.tipo == "PIX"
    assert result.provedores_falhos == []
    assert result.motivo == ""


def test_extract_from_image_returns_dict(sample_receipt_data, monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    mock_agent = MagicMock()
    mock_agent.model.provider = "DeepSeek"
    mock_agent.model.id = "deepseek-flash"
    mock_agent.run.return_value.content = sample_receipt_data
    with patch("bank_receipt_extractor.agent._build_agent", return_value=mock_agent):
        result = extract_from_image(b"fake-image-bytes")
    assert isinstance(result.receipt, BankReceipt)
    assert result.receipt.valor == sample_receipt_data["valor"]


def test_extract_from_image_no_content(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    mock_agent = MagicMock()
    mock_agent.model.provider = "DeepSeek"
    mock_agent.model.id = "deepseek-flash"
    mock_agent.run.return_value.content = None
    with patch("bank_receipt_extractor.agent._build_agent", return_value=mock_agent), pytest.raises(
        ProviderError, match="Serviço de extração indisponível"
    ):
        extract_from_image(b"fake-image-bytes")


def test_run_agent_raises_on_api_error_str(monkeypatch):
    mock_agent = MagicMock()
    mock_agent.run.return_value.content = (
        "Authentication Fails, Your api key: ****af52 is invalid"
    )
    with pytest.raises(ValueError, match="Authentication"):
        _run_agent(mock_agent, b"fake-image-bytes")


def test_run_agent_raises_unexpected_str(monkeypatch):
    mock_agent = MagicMock()
    mock_agent.run.return_value.content = "texto livre"
    with pytest.raises(ValueError, match="Resposta inesperada"):
        _run_agent(mock_agent, b"fake-image-bytes")


def test_extract_from_image_invalid_content_type(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    mock_agent = MagicMock()
    mock_agent.model.provider = "DeepSeek"
    mock_agent.model.id = "deepseek-flash"
    mock_agent.run.return_value.content = ["not", "valid"]
    with patch("bank_receipt_extractor.agent._build_agent", return_value=mock_agent), pytest.raises(
        ProviderError
    ):
        extract_from_image(b"fake-image-bytes")


def test_extract_from_image_invalid_dict(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    mock_agent = MagicMock()
    mock_agent.model.provider = "DeepSeek"
    mock_agent.model.id = "deepseek-flash"
    mock_agent.run.return_value.content = {"valor": "invalido"}
    with patch("bank_receipt_extractor.agent._build_agent", return_value=mock_agent), pytest.raises(
        ProviderError
    ):
        extract_from_image(b"fake-image-bytes")


def test_extract_from_image_fallback_order(sample_bank_receipt, monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    monkeypatch.setenv(
        "MODEL_FALLBACK_LIST",
        "deepseek:deepseek-flash,groq:qwen/qwen3.8-27b",
    )
    failing = MagicMock()
    failing.model.provider = "DeepSeek"
    failing.model.id = "deepseek-flash"
    failing.run.side_effect = RuntimeError("boom")
    working = MagicMock()
    working.model.provider = "Groq"
    working.model.id = "qwen/qwen3.8-27b"
    working.run.return_value.content = sample_bank_receipt

    built: list = []

    def fake_build(spec):
        built.append(spec)
        return failing if "deepseek" in spec else working

    with patch("bank_receipt_extractor.agent._build_agent", side_effect=fake_build):
        result = extract_from_image(b"fake-image-bytes")
    assert result.receipt == sample_bank_receipt
    assert result.provedores_falhos == ["deepseek:deepseek-flash"]
    assert result.motivo == "unknown"
    assert built[0] == "deepseek:deepseek-flash"
    assert built[1] == "groq:qwen/qwen3.8-27b"


def test_extract_from_image_caches_working_agent(sample_bank_receipt, monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    import bank_receipt_extractor.agent as agent_mod

    monkeypatch.setattr(agent_mod, "_working_agent", None)
    mock_agent = MagicMock()
    mock_agent.model.provider = "DeepSeek"
    mock_agent.model.id = "deepseek-flash"
    mock_agent.run.return_value.content = sample_bank_receipt
    with patch("bank_receipt_extractor.agent._build_agent", return_value=mock_agent):
        extract_from_image(b"fake-image-bytes")
        extract_from_image(b"fake-image-bytes")
    assert agent_mod._working_agent is mock_agent
    assert mock_agent.run.call_count == 2


def test_extract_from_image_force_retry_resets_cache(sample_bank_receipt, monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    import bank_receipt_extractor.agent as agent_mod

    monkeypatch.setattr(agent_mod, "_working_agent", None)
    mock_agent = MagicMock()
    mock_agent.model.provider = "DeepSeek"
    mock_agent.model.id = "deepseek-flash"
    mock_agent.run.return_value.content = sample_bank_receipt
    with patch("bank_receipt_extractor.agent._build_agent", return_value=mock_agent) as m:
        extract_from_image(b"fake-image-bytes")
        assert m.call_count == 1
        extract_from_image(b"fake-image-bytes")
        assert m.call_count == 1
        extract_from_image(b"fake-image-bytes", force_retry=True)
        assert m.call_count == 2
    assert agent_mod._working_agent is mock_agent


def test_extract_from_image_cached_fails_recovered_same_provider(
    sample_bank_receipt, monkeypatch
):
    """Cache falha, mas o mesmo modelo responde no retry: não é fallback."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("MODEL_FALLBACK_LIST", "DeepSeek:deepseek-flash")
    import bank_receipt_extractor.agent as agent_mod

    cached = MagicMock()
    cached.model.provider = "DeepSeek"
    cached.model.id = "deepseek-flash"
    cached.run.side_effect = RuntimeError("boom transitório")
    recovered = MagicMock()
    recovered.model.provider = "DeepSeek"
    recovered.model.id = "deepseek-flash"
    recovered.run.return_value.content = sample_bank_receipt

    monkeypatch.setattr(agent_mod, "_working_agent", cached)
    with patch("bank_receipt_extractor.agent._build_agent", return_value=recovered):
        result = extract_from_image(b"fake-image-bytes")
    assert result.receipt == sample_bank_receipt
    assert result.provedores_falhos == []
    assert result.motivo == ""
    assert agent_mod._working_agent is recovered


def test_extract_from_image_cached_fails_then_real_fallback(
    sample_bank_receipt, monkeypatch
):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    monkeypatch.setenv(
        "MODEL_FALLBACK_LIST",
        "deepseek:deepseek-flash,groq:qwen/qwen3.8-27b",
    )
    import bank_receipt_extractor.agent as agent_mod

    cached = MagicMock()
    cached.model.provider = "DeepSeek"
    cached.model.id = "deepseek-flash"
    cached.run.side_effect = RuntimeError("boom")
    failing = MagicMock()
    failing.model.provider = "DeepSeek"
    failing.model.id = "deepseek-flash"
    failing.run.side_effect = RuntimeError("boom de novo")
    working = MagicMock()
    working.model.provider = "Groq"
    working.model.id = "qwen/qwen3.8-27b"
    working.run.return_value.content = sample_bank_receipt

    def fake_build(spec):
        return failing if "deepseek" in spec else working

    monkeypatch.setattr(agent_mod, "_working_agent", cached)
    with patch("bank_receipt_extractor.agent._build_agent", side_effect=fake_build):
        result = extract_from_image(b"fake-image-bytes")
    assert result.receipt == sample_bank_receipt
    assert result.provedores_falhos == ["deepseek:deepseek-flash"]
    assert result.motivo == "unknown"
    assert agent_mod._working_agent is working


def test_extract_from_image_all_fail(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    failing = MagicMock()
    failing.model.provider = "DeepSeek"
    failing.model.id = "deepseek-flash"
    failing.run.side_effect = RuntimeError("boom")
    with patch("bank_receipt_extractor.agent._build_agent", return_value=failing), pytest.raises(
        ProviderError
    ):
        extract_from_image(b"fake-image-bytes")


def test_classificar_falha_authentication():
    exc = ValueError(
        "Authentication Fails, Your api key: ****af52 is invalid (request_id: ...)"
    )
    assert _classificar_falha(exc) == "authentication"


def test_classificar_falha_timeout():
    assert _classificar_falha(TimeoutError("timed out")) == "timeout"
    assert _classificar_falha(ValueError("request timed out")) == "timeout"


def test_classificar_falha_parse():
    assert _classificar_falha(ValueError("Resposta inesperada do agente")) == "parse"
    assert _classificar_falha(ValueError("Agente não retornou dados válidos")) == "parse"


def test_classificar_falha_unknown():
    assert _classificar_falha(RuntimeError("boom")) == "unknown"


def test_extract_from_image_fallback_motivo_authentication(sample_bank_receipt, monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    monkeypatch.setenv(
        "MODEL_FALLBACK_LIST",
        "deepseek:deepseek-flash,groq:qwen/qwen3.8-27b",
    )
    failing = MagicMock()
    failing.model.provider = "DeepSeek"
    failing.model.id = "deepseek-flash"
    failing.run.side_effect = ValueError("Authentication Fails, invalid api key")
    working = MagicMock()
    working.model.provider = "Groq"
    working.model.id = "qwen/qwen3.8-27b"
    working.run.return_value.content = sample_bank_receipt

    def fake_build(spec):
        return failing if "deepseek" in spec else working

    import bank_receipt_extractor.agent as agent_mod

    monkeypatch.setattr(agent_mod, "_working_agent", None)
    with patch("bank_receipt_extractor.agent._build_agent", side_effect=fake_build):
        result = extract_from_image(b"fake-image-bytes")
    assert result.provedores_falhos == ["deepseek:deepseek-flash"]
    assert result.motivo == "authentication"