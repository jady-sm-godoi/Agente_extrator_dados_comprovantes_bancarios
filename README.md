# Receipt Extractor / Extrator de Comprovantes

**v0.2.1** · Python ≥3.12 · [Agno](https://agno.build) + [DeepSeek](https://deepseek.com) (+ [Groq](https://groq.com) fallback)

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
| `DEEPSEEK_API_KEY` | ✅ Yes | DeepSeek API key (get one at [platform.deepseek.com](https://platform.deepseek.com/api_keys)) | — |
| `MODEL_FALLBACK_LIST` | ❌ No | Ordered `provider:model` fallback list, comma-separated. Supported providers: `deepseek`, `groq` | `deepseek:deepseek-flash` |
| `GROQ_API_KEY` | ❌ No | Groq API key — needed only if Groq is in the fallback list (get one at [console.groq.com](https://console.groq.com/keys)) | — |

```bash
export DEEPSEEK_API_KEY=sk_your_key_here
export MODEL_FALLBACK_LIST=deepseek:deepseek-flash,groq:qwen/qwen3.8-27b
```

Or with a `.env` file (your app loads it via `python-dotenv`):

```
DEEPSEEK_API_KEY=sk_your_key_here
MODEL_FALLBACK_LIST=deepseek:deepseek-flash,groq:qwen/qwen3.8-27b
```

### Model Fallback

The extractor tries the models in `MODEL_FALLBACK_LIST` in order and caches the first one that succeeds. If it later fails, it falls through to the next. Call `extract_receipt(arquivo, force_retry=True)` to skip the cache and restart from the list.

| Model | Provider | Vision | Cost (input/1M tok) |
|-------|----------|--------|----------------------|
| `deepseek-flash` | DeepSeek | ✅ | $0.15 |
| `qwen/qwen3.8-27b` | Groq | ✅ | $0.80 |

**Detecting fallback on the client:** when a provider fails but a fallback succeeds, the output dict includes a `fallback` field so the operator can fix the relevant API key:

```json
{
  "valor": 12.5, "tipo": "PIX", "...": "...",
  "fallback": {
    "usado": true,
    "motivo": "authentication",
    "provedores_falhos": ["deepseek:deepseek-flash"]
  }
}
```

`motivo` is a safe category (`authentication`, `timeout`, `parse`, `unknown`) — it never contains API keys, request IDs or raw provider messages. If the same model recovers on a retry, the output has no `fallback` field — only a real provider switch is reported. The HTTP status stays implicit (200) on success; error responses still use `status`/`motivo` with `erro_para_status()`.

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

Python module for automated extraction of Brazilian bank receipt data (PIX, TED, DOC). Accepts PDF or image, processes with vision AI via DeepSeek (with Groq fallback), and returns validated JSON with amount, date, transaction type, banks and recipient.

### Stack

| Layer | Technology |
|-------|-----------|
| Runtime | Python ≥3.12 |
| Agent Framework | Agno |
| Vision Model | DeepSeek (deepseek-flash), Groq fallback |
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
  extract_from_image() ───→ DeepSeek Vision (deepseek-flash)
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

# Python 3.12
python --version   # ≥ 3.12
```

#### Installation

```bash
git clone <repo>
cd receipt-extractor
uv sync

# Set up DeepSeek API key
cp .env.example .env
# Edit .env with your key: https://platform.deepseek.com/api_keys
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
| Provider(s) down | `{"erro": "Extraction service unavailable. Try again later.", "status": 502, "motivo": "provider_error"}` |
| Unsupported format | `{"erro": "Unsupported format. Accepted: PDF, PNG, JPG", "status": 415, "motivo": "unsupported_format"}` |
| File too large (>50MB) | `{"erro": "File exceeds the 50MB limit", "status": 413, "motivo": "file_too_large"}` |
| Invalid/unreadable file | `{"erro": "Could not read the file.", "status": 400, "motivo": "invalid_file"}` |
| Model output failed validation | `{"erro": "Could not extract receipt data.", "status": 422, "motivo": "parse_error"}` |

The function **never raises** — always returns a dict. Error responses are **neutral**: internal details (API keys, request IDs, provider messages) are logged server-side and never exposed to the client. The error dict includes `status` (HTTP code) and `motivo` (classifier) for the view.

### Django Integration

#### Backend View

```python
from django.http import JsonResponse
from bank_receipt_extractor.integration import extract_receipt, erro_para_status

@require_POST
def extract_receipt_data(request):
    file = request.FILES.get("receipt")
    if not file:
        return JsonResponse({"erro": "No file uploaded"}, status=400)
    data = extract_receipt(file)
    status = 200 if "erro" not in data else erro_para_status(data)
    return JsonResponse(data, status=status)
```

The `erro_para_status()` helper maps the error dict to the right HTTP status:

| `motivo` | HTTP status |
|----------|-------------|
| `provider_error` | 502 Bad Gateway |
| `unsupported_format` | 415 Unsupported Media Type |
| `file_too_large` | 413 Payload Too Large |
| `invalid_file` | 400 Bad Request |
| `parse_error` | 422 Unprocessable Entity |

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

> **Note**: Vision API calls take 1–15 seconds. Add loading states on the frontend. For higher scale, consider Celery + Redis for async processing.

### Project Structure

```
├── bank_receipt_extractor/       # Main package
│   ├── __init__.py               # Exports: BankReceipt, extract_receipt, erro_para_status
│   ├── errors.py                 # Typed extraction errors + HTTP status mapping
│   ├── schemas.py                # Pydantic BankReceipt model
│   ├── utils.py                  # Parsers: currency, date, MIME detection
│   ├── agent.py                  # Agno Agent + DeepSeek Vision (fallback, 30s timeout)
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── image_processor.py    # Resize, EXIF correction, JPEG
│   │   └── pdf_processor.py      # PDF → image (pdf2image)
│   └── integration.py            # Bridge: extract_receipt() (50MB limit, logging)
│
├── tests/                        # Test suite (123 tests, 100% coverage)
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
| Python ≥ 3.12 | ✔ | Runtime |
| poppler-utils | ✔ (PDF only) | pdf2image — converts PDF pages to images via `pdftoppm` |
| Internet | ✔ | Vision APIs (DeepSeek primary) |
| DEEPSEEK_API_KEY | ✔ | DeepSeek authentication |

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
| `DEEPSEEK_API_KEY` | ✅ Sim | Chave da API DeepSeek (obtenha em [platform.deepseek.com](https://platform.deepseek.com/api_keys)) | — |
| `MODEL_FALLBACK_LIST` | ❌ Não | Lista de fallback `provedor:modelo` em ordem, separada por vírgula. Provedores suportados: `deepseek`, `groq` | `deepseek:deepseek-flash` |
| `GROQ_API_KEY` | ❌ Não | Chave da API Groq — necessária apenas se Groq estiver na lista de fallback (obtenha em [console.groq.com](https://console.groq.com/keys)) | — |

```bash
export DEEPSEEK_API_KEY=sk_sua_chave_aqui
export MODEL_FALLBACK_LIST=deepseek:deepseek-flash,groq:qwen/qwen3.8-27b
```

Ou com arquivo `.env` (seu app carrega via `python-dotenv`):

```
DEEPSEEK_API_KEY=sk_sua_chave_aqui
MODEL_FALLBACK_LIST=deepseek:deepseek-flash,groq:qwen/qwen3.8-27b
```

### Modelos Recomendados

| Modelo | Provedor | Visão | Custo (input/1M tokens) |
|--------|----------|-------|--------------------------|
| `deepseek-flash` | DeepSeek | ✅ | $0,15 |
| `qwen/qwen3.8-27b` | Groq | ✅ | $0,80 |

O extrator tenta os modelos de `MODEL_FALLBACK_LIST` em ordem e cacheia o primeiro que funcionar. Se ele falhar depois, tenta o próximo da lista. Use `extract_receipt(arquivo, force_retry=True)` para ignorar o cache e recomeçar da lista.

**Detectando o fallback no cliente:** quando um provedor falha mas o fallback extrai com sucesso, o dict de saída inclui o campo `fallback` para o operador corrigir a chave relevante:

```json
{
  "valor": 12.5, "tipo": "PIX", "...": "...",
  "fallback": {
    "usado": true,
    "motivo": "authentication",
    "provedores_falhos": ["deepseek:deepseek-flash"]
  }
}
```

`motivo` é sempre uma categoria segura (`authentication`, `timeout`, `parse`, `unknown`) — nunca contém chave de API, `request_id` ou mensagem crua do provedor. Se o mesmo modelo se recuperar em um retry, a saída não inclui o campo `fallback` — apenas uma troca real de provedor é reportada. O `status` HTTP continua implícito (200) no sucesso; respostas de erro seguem usando `status`/`motivo` com `erro_para_status()`.

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

Módulo Python para extração automatizada de dados de comprovantes bancários brasileiros (PIX, TED, DOC). Recebe PDF ou imagem, processa com IA de visão via DeepSeek (com fallback Groq) e retorna JSON validado com valor, data, tipo, bancos e favorecido.

### Stack

| Camada | Tecnologia |
|--------|-----------|
| Runtime | Python ≥3.12 |
| Framework de Agentes | Agno |
| Modelo de Visão | DeepSeek (deepseek-flash), fallback Groq |
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
  extract_from_image() ───→ DeepSeek Vision (deepseek-flash)
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

# Python 3.12
python --version   # ≥ 3.12
```

#### Instalação

```bash
git clone <repo>
cd receipt-extractor
uv sync

# Configurar chave da API DeepSeek
cp .env.example .env
# Edite .env com sua chave: https://platform.deepseek.com/api_keys
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
| Provedor(es) indisponível(is) | `{"erro": "Serviço de extração indisponível. Tente novamente.", "status": 502, "motivo": "provider_error"}` |
| Formato não suportado | `{"erro": "Formato não suportado. Aceito: PDF, PNG, JPG", "status": 415, "motivo": "unsupported_format"}` |
| Arquivo muito grande (>50MB) | `{"erro": "Arquivo excede o limite de 50MB", "status": 413, "motivo": "file_too_large"}` |
| Arquivo inválido/ilegível | `{"erro": "Não foi possível ler o arquivo.", "status": 400, "motivo": "invalid_file"}` |
| Saída do modelo falhou validação | `{"erro": "Não foi possível extrair os dados do comprovante.", "status": 422, "motivo": "parse_error"}` |

A função **nunca levanta exceção** — sempre retorna um dict. As respostas de erro são **neutras**: detalhes internos (chaves de API, request IDs, mensagens do provedor) são logados no servidor e nunca expostos ao cliente. O dict de erro inclui `status` (código HTTP) e `motivo` (classificador) para a view.

### Integração com Django

#### View (endpoint)

```python
from django.http import JsonResponse
from bank_receipt_extractor.integration import extract_receipt, erro_para_status

@require_POST
def extrair_dados_comprovante(request):
    arquivo = request.FILES.get("comprovante")
    if not arquivo:
        return JsonResponse({"erro": "Nenhum arquivo enviado"}, status=400)
    dados = extract_receipt(arquivo)
    status = 200 if "erro" not in dados else erro_para_status(dados)
    return JsonResponse(dados, status=status)
```

O helper `erro_para_status()` mapeia o dict de erro para o código HTTP correto:

| `motivo` | Código HTTP |
|----------|-------------|
| `provider_error` | 502 Bad Gateway |
| `unsupported_format` | 415 Unsupported Media Type |
| `file_too_large` | 413 Payload Too Large |
| `invalid_file` | 400 Bad Request |
| `parse_error` | 422 Unprocessable Entity |

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

> **Atenção**: Chamadas à API de visão levam de 1 a 15 segundos. Implemente loading states no frontend. Para escala maior, considere Celery + Redis para processamento assíncrono.

### Estrutura do Projeto

```
├── bank_receipt_extractor/       # Pacote principal
│   ├── __init__.py               # Exporta: BankReceipt, extract_receipt, erro_para_status
│   ├── errors.py                 # Erros tipados de extração + status HTTP
│   ├── schemas.py                # Modelo Pydantic BankReceipt
│   ├── utils.py                  # Parsers: moeda, data, detecção MIME
│   ├── agent.py                  # Agno Agent + DeepSeek Vision (fallback, timeout 30s)
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── image_processor.py    # Redimensionamento, EXIF, JPEG
│   │   └── pdf_processor.py      # PDF → imagem (pdf2image)
│   └── integration.py            # Bridge: extract_receipt() (limite 50MB, logging)
│
├── tests/                        # Suite de testes (123 testes, 100% cobertura)
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
| Python ≥ 3.12 | ✔ | Runtime |
| poppler-utils | ✔ (só PDF) | pdf2image — converte páginas PDF em imagem via `pdftoppm` |
| Internet | ✔ | APIs de visão (DeepSeek principal) |
| DEEPSEEK_API_KEY | ✔ | Autenticação DeepSeek |

### Desenvolvimento

```bash
# Quality gates
ruff check bank_receipt_extractor tests   # Lint
mypy bank_receipt_extractor tests         # Type check

# Tests (123 testes, 100% cobertura)
pytest --cov=bank_receipt_extractor --cov-report=term-missing -v
```

### Princípios / Principles

- **Modularity**: Independent package, Django bridge via `extract_receipt()`
- **Security**: API key via `.env` (gitignored), file size limit (50MB), 30s model timeout, MIME magic byte validation, structured logging, explicit `del` of sensitive data in memory, `pip-audit` for CVE scanning
- **Strong Typing**: Pydantic schemas for input/output validation
- **Testability**: 123 tests with 100% code coverage, mocked vision APIs
- **Simplicity**: YAGNI — only the requested fields, no extra abstractions