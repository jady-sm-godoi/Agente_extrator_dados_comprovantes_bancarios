# Interface Contract: `extract_receipt()`

## Função Bridge para Django

```python
def extract_receipt(arquivo: ReceiptInput) -> dict:
    ...
```

### Input
| `arquivo` | `str \| Path \| BytesIO \| django.core.files.uploadedfile.UploadedFile` | Arquivo do comprovante (PDF ou imagem) |

### Output (sucesso)

```python
{
    "valor": Decimal("1234.56"),        # Decimal
    "data_transacao": date(2026, 7, 24), # date
    "numero_controle": "E4B3C2A1",      # str | None
    "banco_origem": "Itaú",             # str | None
    "tipo": "PIX",                      # Literal["PIX","TED","DOC","DESCONHECIDO"]
    "banco_destino": "Nubank",          # str | None
    "favorecido": "João Silva",         # str | None
}
```

### Output (erro)

O retorno de erro é neutro e seguro para o cliente. Detalhes técnicos (chaves, request_ids, mensagens de provedor) são logados no servidor e **nunca** expostos.

```python
{
    "erro": "Serviço de extração indisponível. Tente novamente.",  # mensagem neutra
    "status": 502,                                                 # HTTP status sugerido
    "motivo": "provider_error",                                    # classificador para a view
}
```

Ou, para encurtar o dict:

```python
{"erro": "Não foi possível ler o arquivo.", "status": 400, "motivo": "invalid_file"}
```

Para a view Django obter o status HTTP, use `erro_para_status(resultado)`:

```python
from bank_receipt_extractor.integration import extract_receipt, erro_para_status

resultado = extract_receipt(comprovante)
status = 200 if "erro" not in resultado else erro_para_status(resultado)
```

### Códigos HTTP por cenário

| Cenário | status | motivo | Mensagem neutra |
|---------|--------|--------|-----------------|
| Todos os provedores de IA falharam | 502 | `provider_error` | Serviço de extração indisponível. Tente novamente. |
| Formato não suportado (não PDF/PNG/JPG) | 415 | `unsupported_format` | Formato não suportado. Aceito: PDF, PNG, JPG. |
| Arquivo > 50MB | 413 | `file_too_large` | Arquivo excede o limite de 50MB. |
| Arquivo corrompido/ilegível | 400 | `invalid_file` | Não foi possível ler o arquivo. |
| JSON do modelo não valida no schema | 422 | `parse_error` | Não foi possível extrair os dados do comprovante. |
| Erro inesperado | 400 | `invalid_file` | Não foi possível ler o arquivo. |

### Comportamento

| Cenário | Comportamento |
|---------|---------------|
| Arquivo PDF válido | Converte para imagem, processa, retorna BankReceipt |
| Arquivo imagem válido | Processa imagem, retorna BankReceipt |
| Arquivo inválido/corrompido | Retorna error dict com status 400 |
| Formato não suportado | Retorna error dict com status 415 |
| Todos os provedores falham | Retorna error dict com status 502 |
| Comprovante não identificado | Retorna error dict com status 422 |

### Exemplo de Uso no Django

```python
from bank_receipt_extractor.integration import extract_receipt

def inscricao_view(request):
    if request.method == "POST":
        comprovante = request.FILES.get("comprovante")
        if comprovante:
            dados = extract_receipt(comprovante)
            if "erro" in dados:
                messages.error(request, dados["erro"])
            else:
                pagamento = Pagamento.objects.create(
                    inscricao=inscricao,
                    valor=dados["valor"],
                    data_transacao=dados["data_transacao"],
                    numero_controle=dados["numero_controle"],
                    banco_origem=dados["banco_origem"],
                    tipo=dados["tipo"],
                    banco_destino=dados["banco_destino"],
                    favorecido=dados["favorecido"],
                )
```
