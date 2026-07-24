# Quickstart: Módulo Extrator de Comprovantes Bancários

## Pré-requisitos

- Python ≥ 3.13
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

# Configurar chave da API Groq
cp .env.example .env
# Edite .env e coloque sua GROQ_API_KEY
```

## Uso Básico

```python
from agente_extrator.integration import extrair_comprovante

# De um arquivo no disco
dados = extrair_comprovante("comprovante_pix.pdf")
print(dados)
# {'valor': 1500.0, 'data_transacao': '2026-07-20', 'numero_controle': 'E4B3C2A1', ...}

# De uma imagem
dados = extrair_comprovante("comprovante.jpg")
print(dados)

# De bytes (ex: upload Django)
from io import BytesIO
with open("comprovante.pdf", "rb") as f:
    dados = extrair_comprovante(BytesIO(f.read()))
print(dados)
```

## Uso com Django (no formulário de inscrição)

```python
from agente_extrator.integration import extrair_comprovante

def pagamento_view(request):
    if request.method == "POST":
        comprovante = request.FILES.get("comprovante")
        if comprovante:
            dados = extrair_comprovante(comprovante)
            if "erro" in dados:
                # Mostrar erro ao usuário
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
python exemplo_uso.py --arquivo ~/Downloads/comprovante.pdf
```
