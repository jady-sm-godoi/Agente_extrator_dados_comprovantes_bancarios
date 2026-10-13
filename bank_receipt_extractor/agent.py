import logging
import os
from dataclasses import dataclass, field

from agno.agent import Agent
from agno.media import Image as AgnoImage
from agno.models.deepseek import DeepSeek
from agno.models.groq import Groq

from bank_receipt_extractor.errors import ProviderError
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


@dataclass
class ExtractionResult:
    """Resultado da extração com dados de fallback (seguro para o cliente).

    `provedores_falhos` lista as specs dos provedores que falharam antes do
    sucesso (ex.: "deepseek:deepseek-flash"). `motivo` é a categoria genérica
    da primeira falha. Nenhum detalhe técnico (chave, request_id, texto cru
    do provedor) é exposto aqui — isso fica restrito ao log do servidor.
    """

    receipt: BankReceipt
    provedores_falhos: list[str] = field(default_factory=list)
    motivo: str = ""


def _parse_model_list() -> list[str]:
    """Lê MODEL_FALLBACK_LIST (provedor:modelo, separado por vírgulas).

    Retorna a lista padrão se a env var não estiver definida. Specs duplicadas
    (comparação case-insensitive) são removidas preservando a ordem.
    """
    raw = os.getenv("MODEL_FALLBACK_LIST")
    if not raw:
        return list(DEFAULT_MODEL_LIST)
    specs = [item.strip() for item in raw.split(",") if item.strip()]
    if not specs:
        return list(DEFAULT_MODEL_LIST)
    unique: list[str] = []
    seen: set[str] = set()
    for spec in specs:
        key = spec.casefold()
        if key not in seen:
            seen.add(key)
            unique.append(spec)
    return unique


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


def _classificar_falha(exc: Exception) -> str:
    """Classifica uma falha de modelo em uma categoria genérica.

    A categoria é segura para o cliente (sem chave, sem request_id, sem
    texto cru do provedor). Usada para preencher `ExtractionResult.motivo`.
    """
    msg = str(exc).lower()
    if isinstance(exc, TimeoutError) or "timeout" in msg or "timed out" in msg:
        return "timeout"
    if (
        "authentication" in msg
        or "invalid" in msg
        or "api key" in msg
        or "not set" in msg
    ):
        return "authentication"
    if "inesperada" in msg or "não retornou" in msg or "did not" in msg:
        return "parse"
    return "unknown"


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


def extract_from_image(
    image_bytes: bytes, force_retry: bool = False
) -> ExtractionResult:
    """Extrai dados de um comprovante a partir da imagem.

    Percorre a lista de modelos de MODEL_FALLBACK_LIST em ordem de prioridade.
    Cacheia o primeiro modelo que funcionar e o reutiliza nas chamadas seguintes.
    force_retry ignora o cache e recomeça da lista.

    Em caso de sucesso com fallback, `ExtractionResult.provedores_falhos` traz
    as specs dos provedores que falharam e `motivo` a categoria da primeira
    falha. Recuperação no mesmo modelo (retry) não é reportada como fallback.
    O detalhe técnico fica apenas no log do servidor.
    """
    global _working_agent
    if force_retry:
        _working_agent = None

    provedores_falhos: list[str] = []
    falhas_tecnicas: list[str] = []
    primeira_falha: Exception | None = None

    if _working_agent is not None:
        try:
            receipt = _run_agent(_working_agent, image_bytes)
            return ExtractionResult(receipt)
        except Exception as e:
            cached = _working_agent
            model = cached.model
            assert model is not None
            # Provider em minúsculas para alinhar com o formato de MODEL_FALLBACK_LIST.
            spec_name = f"{str(model.provider).lower()}:{model.id}"
            provedores_falhos.append(spec_name)
            falhas_tecnicas.append(f"{spec_name}: {e}")
            primeira_falha = primeira_falha or e
            logger.warning(
                "Falha com modelo cacheado %s: %s", spec_name, e, exc_info=True
            )
            _working_agent = None

    for spec in _parse_model_list():
        try:
            agent = _build_agent(spec)
            receipt = _run_agent(agent, image_bytes)
            _working_agent = agent
            # Recuperação no mesmo modelo não é fallback: a spec vencedora sai
            # do relatório antes de montar o ExtractionResult. `fallback` só
            # aparece quando o modelo que respondeu difere dos que falharam.
            falhas_anteriores = [
                p for p in provedores_falhos if p.casefold() != spec.casefold()
            ]
            return ExtractionResult(
                receipt,
                provedores_falhos=falhas_anteriores,
                motivo=_classificar_falha(primeira_falha)
                if falhas_anteriores and primeira_falha is not None
                else "",
            )
        except Exception as e:
            if spec.casefold() not in {p.casefold() for p in provedores_falhos}:
                provedores_falhos.append(spec)
            falhas_tecnicas.append(f"{spec}: {e}")
            primeira_falha = primeira_falha or e
            logger.warning("Falha com modelo %s: %s", spec, e, exc_info=True)
            continue

    raise ProviderError(causa=" | ".join(falhas_tecnicas))