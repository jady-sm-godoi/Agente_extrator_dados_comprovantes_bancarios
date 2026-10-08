import logging
import os

from agno.agent import Agent
from agno.media import Image as AgnoImage
from agno.models.deepseek import DeepSeek
from agno.models.groq import Groq

from bank_receipt_extractor.schemas import BankReceipt

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é um especialista em extração de dados de comprovantes bancários brasileiros.

Analise a imagem do comprovante e extraia as seguintes informações:
- valor: Valor da transação (ex: 1234.56)
- data_transacao: Data da transação (formato ISO YYYY-MM-DD)
- numero_controle: Número de controle/autenticação do comprovante (se visível)
- banco_origem: Nome do banco que enviou a transferência
- tipo: Tipo da transferência — PIX, TED, DOC ou DESCONHECIDO
- banco_destino: Nome do banco de destino (se visível)
- favorecido: Nome do favorecido/beneficiário (se visível)

Regras:
- Se algum campo não estiver visível, retorne null (não invente)
- O valor deve estar em formato Decimal (ex: 1500.00)
- O tipo deve ser classificado como PIX, TED, DOC ou DESCONHECIDO
- Número de controle geralmente é um código alfanumérico após "Controle" ou "Autenticação"
- Banco de origem é o banco que aparece como "origem", "remetente" ou "de"."""

DEFAULT_MODEL_LIST = ["deepseek:deepseek-flash"]

DEFAULT_TIMEOUT = 30

# Cache do agente que já funcionou (evita re-iterar o fallback a cada chamada)
_working_agent: Agent | None = None


def _parse_model_list() -> list[str]:
    """Lê MODEL_FALLBACK_LIST (provedor:modelo, separado por vírgulas).

    Retorna a lista padrão se a env var não estiver definida.
    """
    raw = os.getenv("MODEL_FALLBACK_LIST")
    if not raw:
        return list(DEFAULT_MODEL_LIST)
    specs = [item.strip() for item in raw.split(",") if item.strip()]
    if not specs:
        return list(DEFAULT_MODEL_LIST)
    return specs


def _build_agent(spec: str) -> Agent:
    """Instancia um Agent com base em uma spec 'provedor:modelo'.

    Provedores suportados: deepseek, groq. Sem prefixo, assume deepseek.
    """
    provider, sep, model_id = spec.partition(":")
    if not sep:
        provider, model_id = "deepseek", spec
    provider = provider.strip().lower()
    model_id = model_id.strip()

    if provider == "groq":
        model: Groq | DeepSeek = Groq(
            id=model_id,
            api_key=os.getenv("GROQ_API_KEY"),
            timeout=DEFAULT_TIMEOUT,
        )
    elif provider == "deepseek":
        model = DeepSeek(
            id=model_id,
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            timeout=DEFAULT_TIMEOUT,
            use_thinking=False,
        )
    else:
        raise ValueError(
            f"Provedor de modelo não suportado: {provider!r}. "
            "Use 'deepseek' ou 'groq'."
        )
    # DeepSeek não tem structured output nativo: JSON mode força parsing p/ BankReceipt.
    # Groq tem structured output nativo, então mantém o comportamento padrão.
    return Agent(
        model=model,
        description=SYSTEM_PROMPT,
        markdown=True,
        use_json_mode=provider == "deepseek",
    )


def get_agent() -> Agent:
    """Retorna o agente cacheado (o último que funcionou)."""
    global _working_agent
    if _working_agent is None:
        _working_agent = _build_agent(_parse_model_list()[0])
    return _working_agent


def reset_agent() -> None:
    """Zera o cache do agente (força nova tentativa no próximo uso)."""
    global _working_agent
    _working_agent = None


def _run_agent(agent: Agent, image_bytes: bytes) -> BankReceipt:
    response = agent.run(
        "Extraia os dados deste comprovante bancário.",
        images=[AgnoImage(content=image_bytes)],
        output_schema=BankReceipt,
    )
    if response and response.content:
        if isinstance(response.content, BankReceipt):
            return response.content
        if isinstance(response.content, dict):
            return BankReceipt(**response.content)
        if isinstance(response.content, str) and (
            "Authentication" in response.content
            or "invalid" in response.content.lower()
            or "not set" in response.content.lower()
            or "error" in response.content.lower()
        ):
            raise ValueError(response.content.strip()[:300])
        raise ValueError(f"Resposta inesperada do agente: {type(response.content)}")
    raise ValueError("Agente não retornou dados válidos.")


def extract_from_image(image_bytes: bytes, force_retry: bool = False) -> BankReceipt:
    """Extrai dados de um comprovante a partir da imagem.

    Percorre a lista de modelos de MODEL_FALLBACK_LIST em ordem de prioridade.
    Cacheia o primeiro modelo que funcionar e o reutiliza nas chamadas seguintes.
    force_retry ignora o cache e recomeça da lista.
    """
    global _working_agent
    if force_retry:
        _working_agent = None

    failures: list[str] = []

    if _working_agent is not None:
        try:
            return _run_agent(_working_agent, image_bytes)
        except Exception as e:
            cached = _working_agent
            model = cached.model
            assert model is not None
            spec_name = f"{model.provider}:{model.id}"
            failures.append(f"{spec_name}: {e}")
            logger.warning(
                "Falha com modelo cacheado %s: %s", spec_name, e, exc_info=True
            )
            _working_agent = None

    for spec in _parse_model_list():
        try:
            agent = _build_agent(spec)
            receipt = _run_agent(agent, image_bytes)
            _working_agent = agent
            return receipt
        except Exception as e:
            failures.append(f"{spec}: {e}")
            logger.warning("Falha com modelo %s: %s", spec, e, exc_info=True)
            continue

    raise RuntimeError(
        "Todos os modelos falharam na extração do comprovante. "
        f"Falhas: {' | '.join(failures)}"
    )