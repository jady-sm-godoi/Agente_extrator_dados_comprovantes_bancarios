<!--
  Sync Impact Report
  Version: 1.0.0 → 1.1.0
  Principles created: I. Modularidade, II. Segurança, III. Tipagem Forte, IV. Testabilidade, V. Simplicidade
  Emendas: E001 (modelo de visão DeepSeek + fallback Groq)
  Templates requiring updates: none
-->

# Agente Extrator de Comprovantes Bancários — Constituição

**Versão**: 1.1.0 | **Ratificada**: 2026-07-24 | **Última Emenda**: 2026-10-08

## Princípios Fundamentais

### I. Modularidade

O módulo de extração (`agente_extrator/`) deve ser um pacote Python independente, sem acoplamento com Django. A integração com Django deve ocorrer exclusivamente via uma função bridge em `integration.py`. O pacote deve poder ser testado e executado de forma autônoma.

### II. Segurança

Nenhuma chave de API (Groq, DeepSeek, OpenAI, etc.) pode ser hardcoded no código fonte. Todas as credenciais devem ser carregadas de variáveis de ambiente via `python-dotenv`. Arquivos temporários criados durante o processamento (PDF convertido para imagem, etc.) devem ser removidos após o uso. O arquivo `.env` nunca deve ser commitado. A escolha de provedor de IA não é restrita por localização geográfica dos servidores; a avaliação é exclusivamente funcional (qualidade, latência, custo).

### III. Tipagem Forte

Todas as estruturas de dados de entrada e saída devem ser definidas com Pydantic. O JSON de resposta deve ser validado contra o schema `BankReceipt`. Parsers de formato brasileiro (moeda, data) devem ser explícitos e testados.

### IV. Testabilidade

Cada processador (PDF, imagem) deve ser testável de forma independente. O schema de saída deve ter validações claras. A função bridge `extrair_comprovante()` deve aceitar múltiplos formatos de entrada (path, file-like, UploadedFile) e retornar sempre um dict.

### V. Simplicidade (YAGNI)

Apenas os campos solicitados devem ser extraídos: valor, data_transacao, numero_controle, banco_origem, tipo, banco_destino, favorecido. Não adicionar campos extras sem necessidade. Não criar abstrações desnecessárias.

## Stack Tecnológica

| Camada | Tecnologia | Versão |
|--------|-----------|--------|
| Runtime | Python | ≥3.13 |
| Framework de Agentes | Agno | latest |
| Modelo de Visão | DeepSeek (`deepseek-flash`) + fallback Groq (`qwen/qwen3.8-27b`) | via API |
| PDF → Imagem | pdf2image + poppler-utils | latest |
| Imagem | Pillow | latest |
| Schemas | Pydantic | v2 |
| Gerenciamento | uv | latest |

## Desenvolvimento

### Workflow

1. Alterações devem ser feitas em branch feature separada
2. Testar o schema de saída antes de testar o agente
3. Processadores (PDF, imagem) devem ser testados com fixtures reais
4. A função bridge deve ser testada com mocks dos processadores

### Quality Gates

- Código deve passar em `ruff` (lint) e `mypy` (typecheck)
- Schemas Pydantic devem ter testes de validação (valores inválidos, campos ausentes)
- Nenhum `.env` ou chave de API no repositório
- A função `extrair_comprovante()` deve tratar erros gracefulmente (retornar dict com chave `erro`)

## Governança

- **Versionamento**: Semântico (MAJOR.MINOR.PATCH)
  - MAJOR: Mudança incompatível no schema de saída ou API
  - MINOR: Novo campo, novo processador, novo formato de entrada
  - PATCH: Correções, refinamentos de prompt, melhorias internas
- **Emendas**: Propostas devem ser documentadas com justificativa e aprovadas antes da implementação
- **Conformidade**: Todo PR deve ser revisado contra estes princípios antes de merge

## Registro de Emendas

### E001 — Troca do modelo de visão para DeepSeek com fallback Groq (2026-10-08)

**Justificativa**: O modelo anterior (Groq Llama 3.2 90B Vision) foi descontinuado na Groq. O `deepseek-flash` é o único modelo de visão ativo na DeepSeek e oferece custo ~6x menor por extração que o `qwen/qwen3.8-27b` da Groq.

**Decisão**: `deepseek-flash` como modelo primário; lista de fallback `MODEL_FALLBACK_LIST` permite alternância ordenada entre provedores via variável de ambiente (padrão: `deepseek:deepseek-flash`). A lista é opcional — quando ausente, usa somente o padrão.

**Pontos alterados**: Stack Tecnológica (modelo de visão), Princípio II (esclarecimento sobre provedores). Não altera o schema de saída `BankReceipt` (compatível com v1.0.0).
