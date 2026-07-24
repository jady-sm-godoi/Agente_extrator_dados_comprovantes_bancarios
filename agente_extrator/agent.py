import os

from agno.agent import Agent
from agno.media import Image as AgnoImage
from agno.models.groq import Groq

from agente_extrator.schemas import BankReceipt

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
    if _agent is None:
        _agent = Agent(
            model=Groq(
                id="llama-3.2-90b-vision-preview",
                api_key=os.getenv("GROQ_API_KEY"),
            ),
            description=SYSTEM_PROMPT,
            response_model=BankReceipt,
            markdown=True,
        )
    return _agent


def extract_from_image(image_bytes: bytes) -> BankReceipt:
    agent = get_agent()
    response = agent.run(
        "Extraia os dados deste comprovante bancário.",
        images=[AgnoImage(content=image_bytes)],
    )
    if response and response.content:
        return response.content
    raise ValueError("Agente não retornou dados válidos.")
