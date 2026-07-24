# Agente Extrator de Comprovantes Bancários

**v0.1.0** · Python 3.13 · [Agno](https://agno.build) + [Groq](https://groq.com)

Módulo Python para extração automatizada de dados de comprovantes bancários brasileiros (PIX, TED, DOC). Recebe PDF ou imagem, processa com visão computacional via IA e retorna JSON validado com valor, data, tipo, bancos e favorecido.

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Runtime | Python ≥3.13 |
| Framework de Agentes | Agno |
| Modelo de Visão | Groq (qwen3.6-27b) |
| PDF → Imagem | pdf2image + poppler-utils |
| Imagem | Pillow (PIL Fork) |
| Schemas | Pydantic v2 |
| Gerenciamento | uv |

---

## Fluxo de Dados

```
Entrada (str | Path | BytesIO | UploadedFile)
       │
       ▼
  _read_file() ───→ bytes brutos
       │
       ▼
  _identify_type()
       │
       ├── .pdf  → PdfProcessor  → imagem (300 DPI, 1ª página)
       └── .png/jpg → ImageProcessor → JPEG otimizado (max 2048px)
       │
       ▼
  extract_from_image() ───→ Groq Vision (qwen3.6-27b)
       │
       ▼
  BankReceipt (Pydantic validado)
       │
       ▼
  model_dump() ───→ dict (JSON-serializável)

Erro → {"erro": "mensagem descritiva"}
```

---

## Schema: BankReceipt

| Campo | Tipo | Obrigatório | Validação |
|-------|------|-------------|-----------|
| `valor` | Decimal | ✔ | > 0 |
| `data_transacao` | date | ✔ | ISO YYYY-MM-DD |
| `numero_controle` | str \| null | ✘ | max 64 chars |
| `banco_origem` | str \| null | ✘ | max 100 chars |
| `tipo` | Literal | ✔ | PIX \| TED \| DOC \| DESCONHECIDO |
| `banco_destino` | str \| null | ✘ | max 100 chars |
| `favorecido` | str \| null | ✘ | max 200 chars |

### Exemplo de saída

```json
{
  "valor": 1500.0,
  "data_transacao": "2026-07-20",
  "numero_controle": "E4B3C2A1F5D8",
  "banco_origem": "Itaú Unibanco S.A.",
  "tipo": "PIX",
  "banco_destino": "Nubank",
  "favorecido": "Maria Oliveira Santos"
}
```

---

## Quickstart

### Pré-requisitos

```bash
# Sistema
sudo apt install poppler-utils      # Ubuntu/Debian
brew install poppler                 # macOS

# Python 3.13
python --version   # ≥ 3.13
```

### Instalação

```bash
git clone <repo>
cd agente_extrator_dados_comprovantes_bancarios
uv sync

# Configurar chave da API Groq
cp .env.example .env
# Edite .env com sua chave: https://console.groq.com/keys
```

### Uso via CLI

```bash
python exemplo_uso.py ~/Downloads/comprovante.pdf
```

### Uso via código

```python
from agente_extrator.integration import extrair_comprovante

# String de caminho
dados = extrair_comprovante("comprovante.pdf")

# Path object
from pathlib import Path
dados = extrair_comprovante(Path("comprovante.jpg"))

# BytesIO (upload em memória)
from io import BytesIO
with open("comprovante.png", "rb") as f:
    dados = extrair_comprovante(BytesIO(f.read()))

# UploadedFile do Django (diretamente)
dados = extrair_comprovante(request.FILES["comprovante"])
```

---

## API: `extrair_comprovante()`

### Assinatura

```python
def extrair_comprovante(arquivo: str | Path | BytesIO | UploadedFile) -> dict
```

### Retorno

| Situação | Retorno |
|----------|---------|
| Sucesso | `{"valor": float, "data_transacao": str, "tipo": str, ...}` |
| Arquivo inválido | `{"erro": "Não foi possível processar o PDF..."}` |
| Formato não suportado | `{"erro": "Formato não suportado. Aceito: PDF, PNG, JPG"}` |
| API Groq indisponível | `{"erro": "Erro inesperado: ..."}` |

A função **nunca levanta exceção** — sempre retorna um dict.

---

## Integração com Django

Em formulários com upload de comprovante no `onchange`:

### Backend (view endpoint)

```python
# views.py
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from agente_extrator.integration import extrair_comprovante

@require_POST
def extrair_dados_comprovante(request):
    arquivo = request.FILES.get("comprovante")
    if not arquivo:
        return JsonResponse({"erro": "Nenhum arquivo enviado"}, status=400)
    dados = extrair_comprovante(arquivo)
    return JsonResponse(dados)
```

### Frontend (onchange + AJAX)

```javascript
document.getElementById("id_comprovante").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("comprovante", file);

    try {
        const response = await fetch("/api/extrair-comprovante/", {
            method: "POST",
            body: formData,
        });
        const dados = await response.json();

        if (dados.erro) {
            alert("Erro: " + dados.erro);
        } else {
            document.getElementById("id_valor").value = dados.valor;
            document.getElementById("id_data_transacao").value = dados.data_transacao;
            document.getElementById("id_tipo").value = dados.tipo;
            // Preenche os campos ocultos...
        }
    } catch (err) {
        alert("Erro ao processar comprovante");
    }
});
```

> **Atenção**: Chamadas à API Groq levam de 5 a 15 segundos. Implemente loading states no frontend e considere async tasks (Celery) para escala maior.

---

## Estrutura do Projeto

```
├── agente_extrator/              # Pacote principal
│   ├── __init__.py               # Exporta: BankReceipt, extrair_comprovante
│   ├── schemas.py                # Modelo Pydantic BankReceipt
│   ├── utils.py                  # Parsers BR: moeda, data, detect_file_type
│   ├── agent.py                  # Agno Agent + Groq Vision
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── image_processor.py    # Redimensionamento, correção EXIF, JPEG
│   │   └── pdf_processor.py      # PDF → imagem (pdf2image)
│   └── integration.py            # Bridge function extrair_comprovante()
│
├── exemplo_uso.py                # CLI de demonstração
├── pyproject.toml                # Dependências e metadados
├── .env.example                  # Template de variáveis de ambiente
├── specs/                        # Documentação da feature (Specify)
│   └── 001-extrator-comprovantes/
│       ├── spec.md               # Especificação funcional
│       ├── plan.md               # Plano de implementação
│       ├── research.md           # Decisões técnicas
│       ├── data-model.md         # Modelo de dados
│       ├── quickstart.md         # Guia rápido
│       └── tasks.md              # Lista de tarefas
└── .specify/memory/constitution.md  # Princípios do projeto
```

---

## Pré-requisitos de Sistema

| Dependência | Obrigatório | Para quê |
|-------------|-------------|----------|
| Python ≥ 3.13 | ✔ | Runtime |
| poppler-utils | ✔ | pdf2image converter PDF |
| Internet | ✔ | API Groq |
| GROQ_API_KEY | ✔ | Autenticação Groq |

---

## Desenvolvimento

```bash
# Quality gates
ruff check .          # Lint
mypy agente_extrator  # Type check (em breve)

# Testes
pytest -v             # (em breve)
```

### Princípios

- **Modularidade**: Pacote independente, bridge para Django
- **Segurança**: API key via `.env`, sem secrets no repositório
- **Tipagem**: Schemas Pydantic validados na entrada e saída
- **Simplicidade**: Apenas os campos solicitados, YAGNI