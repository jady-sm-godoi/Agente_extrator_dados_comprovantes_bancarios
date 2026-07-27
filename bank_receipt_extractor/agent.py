import os

from agno.agent import Agent
from agno.media import Image as AgnoImage
from agno.models.groq import Groq

from bank_receipt_extractor.schemas import BankReceipt

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


_agent: Agent | None = None


def get_agent() -> Agent:
    global _agent
    model_id = os.getenv("GROQ_MODEL", "qwen/qwen3.6-27b")
    api_key = os.getenv("GROQ_API_KEY")
    if _agent is None or _agent.model.id != model_id:  # type: ignore[union-attr]
        _agent = Agent(
            model=Groq(id=model_id, api_key=api_key),
            description=SYSTEM_PROMPT,
            markdown=True,
        )
    return _agent


def extract_from_image(image_bytes: bytes) -> BankReceipt:
    agent = get_agent()
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
        raise ValueError(f"Resposta inesperada do agente: {type(response.content)}")
    raise ValueError("Agente não retornou dados válidos.")
