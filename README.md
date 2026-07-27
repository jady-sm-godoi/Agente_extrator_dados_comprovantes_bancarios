# Receipt Extractor / Extrator de Comprovantes

**v0.1.1** · Python 3.13 · [Agno](https://agno.build) + [Groq](https://groq.com)

---

## Installation

```bash
pip install bank-receipt-extractor
# or with uv
uv pip install bank-receipt-extractor
```

## Configuration

Set these environment variables:

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `GROQ_API_KEY` | ✅ Yes | Groq API key (get one at [console.groq.com](https://console.groq.com/keys)) | — |
| `GROQ_MODEL` | ❌ No | Groq vision model ID | `qwen/qwen3.6-27b` |

```bash
export GROQ_API_KEY=gsk_your_key_here
export GROQ_MODEL=qwen/qwen3.6-27b
```

Or with a `.env` file (your app loads it via `python-dotenv`):

```
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=qwen/qwen3.6-27b
```

### Recommended Models

| Model | Speed | Quality | Cost |
|-------|-------|---------|------|
| `qwen/qwen3.6-27b` | ⚡ Fast | ✅ Good | $0.60/1M tokens |
| `llama-3.2-90b-vision-preview` | ⚡ Fast | ✅ Excellent | $0.90/1M tokens |
| `llama-3.2-11b-vision-preview` | ⚡ Very fast | ✅ OK | $0.18/1M tokens |

All listed models are available on Groq's free tier for prototyping.

## System Dependency: poppler-utils

To process **PDF files**, `pdf2image` requires the `pdftoppm` command from `poppler-utils`:

```bash
# Ubuntu/Debian
sudo apt install poppler-utils

# macOS
brew install poppler

# Fedora
sudo dnf install poppler-utils

# Docker
RUN apt-get update && apt-get install -y poppler-utils
```

If you process **only images** (PNG/JPG), poppler-utils is **not needed**.

---

## English

### Overview

Python module for automated extraction of Brazilian bank receipt data (PIX, TED, DOC). Accepts PDF or image, processes with vision AI via Groq, and returns validated JSON with amount, date, transaction type, banks and recipient.

### Stack

| Layer | Technology |
|-------|-----------|
| Runtime | Python ≥3.13 |
| Agent Framework | Agno |
| Vision Model | Groq (qwen3.6-27b) |
| PDF → Image | pdf2image + poppler-utils |
| Image Processing | Pillow |
| Schemas | Pydantic v2 |
| Package Manager | uv |

### Data Flow

```
Input (str | Path | BytesIO | UploadedFile)
       │
       ▼
  _read_file() ───→ raw bytes
       │
       ▼
  _identify_type()
       │
       ├── .pdf  → PdfProcessor  → image (300 DPI, 1st page)
       └── .png/jpg → ImageProcessor → optimized JPEG (max 2048px)
       │
       ▼
  extract_from_image() ───→ Groq Vision (qwen3.6-27b)
       │
       ▼
  BankReceipt (Pydantic validated)
       │
       ▼
  model_dump() ───→ dict (JSON-serializable)

Error → {"erro": "descriptive message"}
```

### Schema: BankReceipt

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `valor` | Decimal | ✔ | > 0 |
| `data_transacao` | date | ✔ | ISO YYYY-MM-DD |
| `numero_controle` | str \| null | ✘ | max 64 chars |
| `banco_origem` | str \| null | ✘ | max 100 chars |
| `tipo` | Literal | ✔ | PIX \| TED \| DOC \| DESCONHECIDO |
| `banco_destino` | str \| null | ✘ | max 100 chars |
| `favorecido` | str \| null | ✘ | max 200 chars |

#### Sample output

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

### Quickstart

#### Prerequisites

```bash
# System
sudo apt install poppler-utils      # Ubuntu/Debian
brew install poppler                 # macOS

# Python 3.13
python --version   # ≥ 3.13
```

#### Installation

```bash
git clone <repo>
cd receipt-extractor
uv sync

# Set up Groq API key
cp .env.example .env
# Edit .env with your key: https://console.groq.com/keys
```

#### CLI Usage

```bash
python usage_example.py ~/Downloads/receipt.pdf
```

#### Code Usage

```python
from bank_receipt_extractor.integration import extract_receipt

# File path
data = extract_receipt("receipt.pdf")

# Path object
from pathlib import Path
data = extract_receipt(Path("receipt.jpg"))

# BytesIO (in-memory upload)
from io import BytesIO
with open("receipt.png", "rb") as f:
    data = extract_receipt(BytesIO(f.read()))

# Django UploadedFile (directly)
data = extract_receipt(request.FILES["receipt"])
```

### API: `extract_receipt()`

```python
def extract_receipt(file: str | Path | BytesIO | UploadedFile) -> dict
```

| Scenario | Return |
|----------|--------|
| Success | `{"valor": float, "data_transacao": str, "tipo": str, ...}` |
| Invalid file | `{"erro": "Could not process PDF..."}` |
| Unsupported format | `{"erro": "Unsupported format. Accepted: PDF, PNG, JPG"}` |
| File too large (>50MB) | `{"erro": "File exceeds the 50MB limit"}` |
| Groq API error | `{"erro": "Unexpected error: ..."}` |

The function **never raises** — always returns a dict.

### Django Integration

#### Backend View

```python
from django.http import JsonResponse
from bank_receipt_extractor.integration import extract_receipt

@require_POST
def extract_receipt_data(request):
    file = request.FILES.get("receipt")
    if not file:
        return JsonResponse({"erro": "No file uploaded"}, status=400)
    data = extract_receipt(file)
    return JsonResponse(data)
```

#### Frontend (onchange + AJAX)

```javascript
document.getElementById("id_receipt").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("receipt", file);

    try {
        const response = await fetch("/api/extract-receipt/", {
            method: "POST",
            body: formData,
        });
        const data = await response.json();

        if (data.erro) {
            alert("Error: " + data.erro);
        } else {
            document.getElementById("id_valor").value = data.valor;
            document.getElementById("id_tipo").value = data.tipo;
            // Fill hidden fields...
        }
    } catch (err) {
        alert("Error processing receipt");
    }
});
```

> **Note**: Groq API calls take 5–15 seconds. Add loading states on the frontend. For higher scale, consider Celery + Redis for async processing.

### Project Structure

```
├── bank_receipt_extractor/       # Main package
│   ├── __init__.py               # Exports: BankReceipt, extract_receipt
│   ├── schemas.py                # Pydantic BankReceipt model
│   ├── utils.py                  # Parsers: currency, date, MIME detection
│   ├── agent.py                  # Agno Agent + Groq Vision (30s timeout)
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── image_processor.py    # Resize, EXIF correction, JPEG
│   │   └── pdf_processor.py      # PDF → image (pdf2image)
│   └── integration.py            # Bridge: extract_receipt() (50MB limit, logging)
│
├── tests/                        # Test suite (101 tests, 100% coverage)
│   ├── test_schemas.py
│   ├── test_utils.py
│   ├── test_agent.py
│   ├── test_image_processor.py
│   ├── test_pdf_processor.py
│   ├── test_integration.py
│   ├── test_integration_unit.py
│   └── conftest.py               # Shared fixtures & mocks
│
├── usage_example.py              # CLI demo
├── pyproject.toml                # Dependencies & metadata
├── .env.example                  # Environment template
└── specs/                        # Feature docs (Specify)
```

### System Requirements

| Dependency | Required | Purpose |
|------------|----------|---------|
| Python ≥ 3.13 | ✔ | Runtime |
| poppler-utils | ✔ (PDF only) | pdf2image — converts PDF pages to images via `pdftoppm` |
| Internet | ✔ | Groq API |
| GROQ_API_KEY | ✔ | Groq authentication |

---

## Português

### Instalação

```bash
pip install bank-receipt-extractor
# ou com uv
uv pip install bank-receipt-extractor
```

### Configuração

Defina estas variáveis de ambiente:

| Variável | Obrigatória | Descrição | Padrão |
|----------|-------------|-----------|--------|
| `GROQ_API_KEY` | ✅ Sim | Chave da API Groq (obtenha em [console.groq.com](https://console.groq.com/keys)) | — |
| `GROQ_MODEL` | ❌ Não | Modelo de visão Groq | `qwen/qwen3.6-27b` |

```bash
export GROQ_API_KEY=gsk_sua_chave_aqui
export GROQ_MODEL=qwen/qwen3.6-27b
```

Ou com arquivo `.env` (seu app carrega via `python-dotenv`):

```
GROQ_API_KEY=gsk_sua_chave_aqui
GROQ_MODEL=qwen/qwen3.6-27b
```

### Modelos Recomendados

| Modelo | Velocidade | Qualidade | Custo |
|--------|------------|-----------|-------|
| `qwen/qwen3.6-27b` | ⚡ Rápido | ✅ Boa | $0,60/1M tokens |
| `llama-3.2-90b-vision-preview` | ⚡ Rápido | ✅ Excelente | $0,90/1M tokens |
| `llama-3.2-11b-vision-preview` | ⚡ Muito rápido | ✅ OK | $0,18/1M tokens |

Todos os modelos listados estão disponíveis no nível gratuito da Groq para prototipação.

### Dependência de Sistema: poppler-utils

Para processar **arquivos PDF**, o `pdf2image` precisa do comando `pdftoppm` do pacote `poppler-utils`:

```bash
# Ubuntu/Debian
sudo apt install poppler-utils

# macOS
brew install poppler

# Fedora
sudo dnf install poppler-utils

# Docker
RUN apt-get update && apt-get install -y poppler-utils
```

Se você processa **apenas imagens** (PNG/JPG), o `poppler-utils` **não é necessário**.

---

### Visão Geral

Módulo Python para extração automatizada de dados de comprovantes bancários brasileiros (PIX, TED, DOC). Recebe PDF ou imagem, processa com IA de visão via Groq e retorna JSON validado com valor, data, tipo, bancos e favorecido.

### Stack

| Camada | Tecnologia |
|--------|-----------|
| Runtime | Python ≥3.13 |
| Framework de Agentes | Agno |
| Modelo de Visão | Groq (qwen3.6-27b) |
| PDF → Imagem | pdf2image + poppler-utils |
| Processamento de Imagem | Pillow |
| Schemas | Pydantic v2 |
| Gerenciamento | uv |

### Fluxo de Dados

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

### Schema: BankReceipt

| Campo | Tipo | Obrigatório | Validação |
|-------|------|-------------|-----------|
| `valor` | Decimal | ✔ | > 0 |
| `data_transacao` | date | ✔ | ISO YYYY-MM-DD |
| `numero_controle` | str \| null | ✘ | max 64 chars |
| `banco_origem` | str \| null | ✘ | max 100 chars |
| `tipo` | Literal | ✔ | PIX \| TED \| DOC \| DESCONHECIDO |
| `banco_destino` | str \| null | ✘ | max 100 chars |
| `favorecido` | str \| null | ✘ | max 200 chars |

#### Exemplo de saída

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

### Início Rápido

#### Pré-requisitos

```bash
# Sistema
sudo apt install poppler-utils      # Ubuntu/Debian
brew install poppler                 # macOS

# Python 3.13
python --version   # ≥ 3.13
```

#### Instalação

```bash
git clone <repo>
cd receipt-extractor
uv sync

# Configurar chave da API Groq
cp .env.example .env
# Edite .env com sua chave: https://console.groq.com/keys
```

#### Uso via CLI

```bash
python usage_example.py ~/Downloads/comprovante.pdf
```

#### Uso via código

```python
from bank_receipt_extractor.integration import extract_receipt

# Caminho do arquivo
dados = extract_receipt("comprovante.pdf")

# Path object
from pathlib import Path
dados = extract_receipt(Path("comprovante.jpg"))

# BytesIO (upload em memória)
from io import BytesIO
with open("comprovante.png", "rb") as f:
    dados = extract_receipt(BytesIO(f.read()))

# UploadedFile do Django (diretamente)
dados = extract_receipt(request.FILES["comprovante"])
```

### API: `extract_receipt()`

```python
def extract_receipt(arquivo: str | Path | BytesIO | UploadedFile) -> dict
```

| Situação | Retorno |
|----------|---------|
| Sucesso | `{"valor": float, "data_transacao": str, "tipo": str, ...}` |
| Arquivo inválido | `{"erro": "Não foi possível processar o PDF..."}` |
| Formato não suportado | `{"erro": "Formato não suportado. Aceito: PDF, PNG, JPG"}` |
| Arquivo muito grande (>50MB) | `{"erro": "Arquivo excede o limite de 50MB"}` |
| API Groq indisponível | `{"erro": "Erro inesperado: ..."}` |

A função **nunca levanta exceção** — sempre retorna um dict.

### Integração com Django

#### View (endpoint)

```python
from django.http import JsonResponse
from bank_receipt_extractor.integration import extract_receipt

@require_POST
def extrair_dados_comprovante(request):
    arquivo = request.FILES.get("comprovante")
    if not arquivo:
        return JsonResponse({"erro": "Nenhum arquivo enviado"}, status=400)
    dados = extract_receipt(arquivo)
    return JsonResponse(dados)
```

#### Frontend (onchange + AJAX)

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
            document.getElementById("id_tipo").value = dados.tipo;
            // Preenche campos ocultos...
        }
    } catch (err) {
        alert("Erro ao processar comprovante");
    }
});
```

> **Atenção**: Chamadas à API Groq levam de 5 a 15 segundos. Implemente loading states no frontend. Para escala maior, considere Celery + Redis para processamento assíncrono.

### Estrutura do Projeto

```
├── bank_receipt_extractor/       # Pacote principal
│   ├── __init__.py               # Exporta: BankReceipt, extract_receipt
│   ├── schemas.py                # Modelo Pydantic BankReceipt
│   ├── utils.py                  # Parsers: moeda, data, detecção MIME
│   ├── agent.py                  # Agno Agent + Groq Vision (timeout 30s)
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── image_processor.py    # Redimensionamento, EXIF, JPEG
│   │   └── pdf_processor.py      # PDF → imagem (pdf2image)
│   └── integration.py            # Bridge: extract_receipt() (limite 50MB, logging)
│
├── tests/                        # Suite de testes (101 testes, 100% cobertura)
│   ├── test_schemas.py
│   ├── test_utils.py
│   ├── test_agent.py
│   ├── test_image_processor.py
│   ├── test_pdf_processor.py
│   ├── test_integration.py
│   ├── test_integration_unit.py
│   └── conftest.py               # Fixtures e mocks compartilhados
│
├── usage_example.py              # CLI de demonstração
├── pyproject.toml                # Dependências e metadados
├── .env.example                  # Template de variáveis de ambiente
└── specs/                        # Documentação da feature
```

### Pré-requisitos de Sistema

| Dependência | Obrigatório | Para quê |
|-------------|-------------|----------|
| Python ≥ 3.13 | ✔ | Runtime |
| poppler-utils | ✔ (só PDF) | pdf2image — converte páginas PDF em imagem via `pdftoppm` |
| Internet | ✔ | API Groq |
| GROQ_API_KEY | ✔ | Autenticação Groq |

### Desenvolvimento

```bash
# Quality gates
ruff check bank_receipt_extractor tests   # Lint
mypy bank_receipt_extractor tests         # Type check

# Tests (101 testes, 100% cobertura)
pytest --cov=bank_receipt_extractor --cov-report=term-missing -v
```

### Princípios / Principles

- **Modularity**: Independent package, Django bridge via `extract_receipt()`
- **Security**: API key via `.env` (gitignored), file size limit (50MB), Groq timeout (30s), MIME magic byte validation, structured logging, explicit `del` of sensitive data in memory, `pip-audit` for CVE scanning
- **Strong Typing**: Pydantic schemas for input/output validation
- **Testability**: 101 tests with 100% code coverage, mocked Groq API
- **Simplicity**: YAGNI — only the requested fields, no extra abstractions