# Interface Contract: `extrair_comprovante()`

## Contrato da Função Bridge (Django)

```python
def extrair_comprovante(arquivo: ComprovanteInput) -> dict:
    ...
```

### Input

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
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

```python
{
    "erro": "Mensagem descritiva do erro"
}
```

### Comportamento

| Cenário | Comportamento |
|---------|---------------|
| Arquivo PDF válido | Converte para imagem, processa, retorna BankReceipt |
| Arquivo imagem válido | Processa imagem, retorna BankReceipt |
| Arquivo inválido/corrompido | Retorna `{"erro": "..."}` |
| Formato não suportado | Retorna `{"erro": "Formato não suportado. Aceito: PDF, PNG, JPG"}` |
| Erro de API Groq | Retorna `{"erro": "Serviço de IA indisponível. Tente novamente."}` |
| Comprovante não identificado | Retorna `{"erro": "Não foi possível extrair dados. Verifique o comprovante."}` |

### Exemplo de Uso no Django

```python
from agente_extrator.integration import extrair_comprovante

def inscricao_view(request):
    if request.method == "POST":
        comprovante = request.FILES.get("comprovante")
        if comprovante:
            dados = extrair_comprovante(comprovante)
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
