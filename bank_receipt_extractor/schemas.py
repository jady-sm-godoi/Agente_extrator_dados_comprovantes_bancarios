from decimal import Decimal
from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field


class BankReceipt(BaseModel):
    valor: Decimal = Field(
        ...,
        description="Valor da transação em formato Decimal",
        gt=0,
    )
    data_transacao: date = Field(
        ...,
        description="Data da transação no formato ISO (YYYY-MM-DD)",
    )
    numero_controle: Optional[str] = Field(
        None,
        description="Número de controle/autenticação do comprovante",
        max_length=64,
    )
    banco_origem: Optional[str] = Field(
        None,
        description="Nome do banco de origem da transferência",
        max_length=100,
    )
    tipo: Literal["PIX", "TED", "DOC", "DESCONHECIDO"] = Field(
        ...,
        description="Tipo da transferência bancária",
    )
    banco_destino: Optional[str] = Field(
        None,
        description="Nome do banco de destino da transferência",
        max_length=100,
    )
    favorecido: Optional[str] = Field(
        None,
        description="Nome do favorecido/beneficiário da transferência",
        max_length=200,
    )
