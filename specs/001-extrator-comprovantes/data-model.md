# Data Model: Módulo Extrator de Comprovantes Bancários

> **Nota de revisão (2026-10-13)**: Sincronizado com a implementação v0.2.0 —
> validações reais do schema, formato do dict de erro (`erro`/`status`/`motivo`)
> e fluxo com DeepSeek Vision (fallback Groq).

## Entidade Principal: BankReceipt

Schema Pydantic que representa os dados extraídos de um comprovante bancário.

```python
from decimal import Decimal
from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, Field, ValidationError


class BankReceipt(BaseModel):
    valor: Decimal = Field(
        ...,
        description="Valor da transação em formato Decimal (ex: 1234.56)",
        gt=0,
        examples=["1234.56", "99.90"],
    )
    data_transacao: date = Field(
        ...,
        description="Data da transação no formato ISO (YYYY-MM-DD)",
        examples=["2026-07-24"],
    )
    numero_controle: Optional[str] = Field(
        None,
        description="Número de controle/autenticação do comprovante (E4B3C2A1...)",
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
```

### Validações

| Campo | Regra |
|-------|-------|
| `valor` | Deve ser positivo (> 0) |
| `data_transacao` | Deve ser uma data válida, parseável nos formatos DD/MM/AAAA ou ISO YYYY-MM-DD |
| `numero_controle` | Opcional, mas se presente deve ter ≤ 64 caracteres |
| `banco_origem` | Opcional, ≤ 100 caracteres |
| `tipo` | Apenas PIX, TED, DOC, DESCONHECIDO |
| `banco_destino` | Opcional, ≤ 100 caracteres |
| `favorecido` | Opcional, ≤ 200 caracteres |

### Exemplo de JSON de Saída

```json
{
  "valor": 1500.00,
  "data_transacao": "2026-07-20",
  "numero_controle": "E4B3C2A1F5D8",
  "banco_origem": "Itaú Unibanco S.A.",
  "tipo": "PIX",
  "banco_destino": "Nubank",
  "favorecido": "Maria Oliveira Santos"
}
```

### Exemplo de Erro

```json
{
  "erro": "Não foi possível extrair os dados do comprovante.",
  "status": 422,
  "motivo": "parse_error"
}
```

## Entidade de Entrada: ComprovanteInput

Tipo union que representa os formatos de entrada aceitos:

```python
from pathlib import Path
from io import BytesIO
from typing import Union

# Tipos aceitos pela função bridge
ComprovanteInput = Union[str, Path, BytesIO]
# Django UploadedFile também é aceito (é file-like)
```

## Fluxo de Dados

```
ComprovanteInput (str | Path | BytesIO | UploadedFile)
    │
    ├── É string/Path? → Abrir arquivo do disco
    ├── É BytesIO? → Ler da memória
    └── É UploadedFile? → Ler do Django
    │
    ▼
Detectar tipo:
    ├── Extensão .pdf → pdf_processor → lista de imagens PIL
    └── Extensão .png/.jpg/.jpeg → image_processor → imagem PIL otimizada
    │
    ▼
Agno Agent (DeepSeek Vision, fallback Groq) → BankReceipt Pydantic
    │
    ▼
BankReceipt.model_dump() → dict (JSON-serializável)
```
