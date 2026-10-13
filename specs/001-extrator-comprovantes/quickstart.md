# Quickstart: Módulo Extrator de Comprovantes Bancários

> **Nota de revisão (2026-10-13)**: Sincronizado com a implementação v0.2.0 —
> pacote `bank_receipt_extractor`, função `extract_receipt()`, Python ≥3.12.

## Pré-requisitos

- Python ≥ 3.12
- `poppler-utils` instalado no sistema:
  ```bash
  # Ubuntu/Debian
  sudo apt install poppler-utils

  # macOS
  brew install poppler

  # Fedora
  sudo dnf install poppler-utils
  ```

## Instalação

```bash
# Instalar dependências
uv sync  # ou: pip install -e .

# Configurar chave da API DeepSeek
cp .env.example .env
# Edite .env e coloque sua DEEPSEEK_API_KEY
```

> Opcional: para fallback com Groq, defina também `GROQ_API_KEY` e
> `MODEL_FALLBACK_LIST=deepseek:deepseek-flash,groq:qwen/qwen3.8-27b`.

## Uso Básico

```python
from bank_receipt_extractor.integration import extract_receipt

# De um arquivo no disco
dados = extract_receipt("comprovante_pix.pdf")
print(dados)
# {'valor': 1500.0, 'data_transacao': '2026-07-20', 'numero_controle': 'E4B3C2A1', ...}

# De uma imagem
dados = extract_receipt("comprovante.jpg")
print(dados)

# De bytes (ex: upload Django)
from io import BytesIO
with open("comprovante.pdf", "rb") as f:
    dados = extract_receipt(BytesIO(f.read()))
print(dados)
```

## Uso com Django (no formulário de inscrição)

```python
from bank_receipt_extractor.integration import extract_receipt

def pagamento_view(request):
    if request.method == "POST":
        comprovante = request.FILES.get("comprovante")
        if comprovante:
            dados = extract_receipt(comprovante)
            if "erro" in dados:
                # Mostrar erro ao usuário; dados["status"]/dados["motivo"] estão
                # disponíveis para mapear o HTTP status com erro_para_status()
                form.add_error("comprovante", dados["erro"])
            else:
                # Salvar no model de pagamento
                pagamento.valor = dados["valor"]
                pagamento.data_transacao = dados["data_transacao"]
                pagamento.numero_controle = dados["numero_controle"]
                pagamento.banco_origem = dados["banco_origem"]
                pagamento.tipo = dados["tipo"]
                pagamento.banco_destino = dados["banco_destino"]
                pagamento.favorecido = dados["favorecido"]
                pagamento.save()
```

## Script de Teste Rápido

```bash
python usage_example.py ~/Downloads/comprovante.pdf
```
