# Feature Specification: Módulo Extrator de Comprovantes Bancários

**Feature Branch**: `001-extrator-comprovantes`

**Created**: 2026-07-24

**Status**: Implemented (v0.2.0)

> **Nota de revisão (2026-10-13)**: Documento sincronizado com a implementação v0.2.0 —
> pacote `bank_receipt_extractor`, função `extract_receipt()`, modelo de visão DeepSeek
> (`deepseek-flash`) como primário com fallback Groq (conforme Emenda E001).

**Input**: User description: "Módulo de extração automatizada de dados de comprovantes de transferência bancária (PIX, TED, DOC) usando Agno e Groq, que recebe PDF ou imagem e retorna JSON com valor, data, número de controle e banco de origem"

## User Scenarios & Testing

### User Story 1 - Extrair dados de comprovante via upload de imagem (Priority: P1)

Um usuário faz upload de uma imagem (PNG/JPG) de um comprovante bancário brasileiro e o sistema extrai automaticamente os dados estruturados.

**Why this priority**: É o caso de uso mais comum e fundamental — comprovantes são frequentemente compartilhados como prints/fotos. Sem ele, não há produto mínimo viável.

**Independent Test**: Pode ser testado fornecendo uma imagem de comprovante bancário e verificando se o JSON retornado contém todos os campos obrigatórios preenchidos.

**Acceptance Scenarios**:

1. **Given** uma imagem PNG de comprovante PIX, **When** o processador de imagem recebe o arquivo, **Then** retorna JSON com valor, data, numero_controle, banco_origem, tipo="PIX"
2. **Given** uma imagem JPG de comprovante TED, **When** o processador de imagem recebe o arquivo, **Then** retorna JSON com valor, data, tipo="TED" e banco_destino
3. **Given** uma imagem borrada ou de má qualidade, **When** o processador tenta extrair, **Then** retorna JSON com campos que conseguiu extrair e null nos não identificados (sem erro fatal)

---

### User Story 2 - Extrair dados de comprovante via upload de PDF (Priority: P2)

Um usuário faz upload de um arquivo PDF de um comprovante bancário e o sistema extrai os dados automaticamente.

**Why this priority**: Muitos bancos emitem comprovantes em PDF. Essencial para cobrir todos os formatos comuns, mas imagens são mais frequentes.

**Independent Test**: Pode ser testado fornecendo um PDF de comprovante bancário e verificando se o JSON retornado contém os campos extraídos.

**Acceptance Scenarios**:

1. **Given** um PDF de comprovante PIX de 1 página, **When** o processador PDF converte para imagem e extrai, **Then** retorna JSON completo
2. **Given** um PDF de comprovante DOC de múltiplas páginas, **When** o processador converte o PDF para imagem, **Then** usa a primeira página (onde estão os dados principais) e retorna o JSON
3. **Given** um PDF inválido ou corrompido, **When** o processador tenta abrir, **Then** retorna erro amigável

---

### User Story 3 - Integração com Django via função bridge (Priority: P3)

Um desenvolvedor Django importa a função `extract_receipt()` e a utiliza no fluxo de formulário de inscrição em evento, recebendo um dict Python pronto para salvar no model.

**Why this priority**: A integração é necessária para o contexto real de uso, mas a lógica central de extração (US1, US2) deve estar madura primeiro.

**Independent Test**: Pode ser testado chamando `extract_receipt()` com um `BytesIO` ou `UploadedFile` simulado e verificando o dict de retorno.

**Acceptance Scenarios**:

1. **Given** um caminho de arquivo (str), **When** `extract_receipt("/path/to/file.pdf")` é chamado, **Then** retorna dict com dados extraídos
2. **Given** um objeto `BytesIO`, **When** `extract_receipt(io.BytesIO(...))` é chamado, **Then** retorna dict com dados extraídos
3. **Given** um arquivo inválido, **When** `extract_receipt(...)` é chamado, **Then** retorna `{"erro": "mensagem descritiva", "status": 400, "motivo": "invalid_file"}`
4. **Given** que todos os provedores de IA estão indisponíveis, **When** a extração é chamada, **Then** retorna `{"erro": "Serviço de extração indisponível. Tente novamente.", "status": 502, "motivo": "provider_error"}`

### Edge Cases

- Comprovante sem número de controle visível → campo `numero_controle` retorna `null`
- Comprovante com valor em formato brasileiro (R$ 1.234,56) → parse para Decimal 1234.56
- Imagem com rotação/orientação incorreta → deve ser corrigida antes do processamento
- PDF protegido por senha → retorna erro amigável
- Múltiplos comprovantes na mesma imagem → extrai apenas o primeiro identificado

## Requirements

### Functional Requirements

- **FR-001**: Sistema MUST aceitar imagens nos formatos PNG, JPG, JPEG
- **FR-002**: Sistema MUST aceitar arquivos PDF
- **FR-003**: Sistema MUST extrair campo `valor` (Decimal) do comprovante
- **FR-004**: Sistema MUST extrair campo `data_transacao` (date) do comprovante
- **FR-005**: Sistema MUST extrair campo `numero_controle` (str | null) se presente
- **FR-006**: Sistema MUST extrair campo `banco_origem` (str | null) se presente
- **FR-007**: Sistema MUST classificar `tipo` como "PIX", "TED", "DOC" ou "DESCONHECIDO"
- **FR-008**: Sistema MUST extrair campo `banco_destino` (str | null) se presente
- **FR-009**: Sistema MUST extrair campo `favorecido` (str | null) se presente
- **FR-010**: Sistema MUST retornar um objeto JSON validado contra schema Pydantic
- **FR-011**: Sistema MUST usar o modelo de visão DeepSeek (`deepseek-flash`) como primário para extração via Agno, com fallback ordenado e configurável via `MODEL_FALLBACK_LIST` (provedores suportados: `deepseek`, `groq`)
- **FR-012**: Sistema MUST expor função `extract_receipt()` que aceita str | Path | BytesIO | UploadedFile
- **FR-013**: Sistema MUST limpar arquivos temporários após o processamento
- **FR-014**: Sistema MUST tratar erros gracefulmente retornando dict com `erro` (mensagem neutra), `status` (HTTP) e `motivo` (classificador)

### Key Entities

- **BankReceipt**: Schema Pydantic que representa os dados extraídos. Atributos: valor (Decimal), data_transacao (date), numero_controle (str | None), banco_origem (str | None), tipo (Literal["PIX", "TED", "DOC", "DESCONHECIDO"]), banco_destino (str | None), favorecido (str | None)
- **Comprovante**: Arquivo de entrada (PDF ou imagem) que contém as informações bancárias a serem extraídas

## Success Criteria

### Measurable Outcomes

- **SC-001**: Extração de comprovante PIX leva menos de 10 segundos (incluindo processamento + API de visão)
- **SC-002**: Precisão de extração ≥ 90% para comprovantes com boa qualidade de imagem
- **SC-003**: Taxa de erro (retorno com campo `erro`) < 5% para comprovantes válidos
- **SC-004**: PDFs de até 5 páginas são processados em menos de 15 segundos
- **SC-005**: Função bridge retorna dict em formato compatível com Django models sem necessidade de transformação adicional

## Assumptions

- Usuários têm conexão com internet estável para chamar a API de visão
- Comprovantes seguem o padrão brasileiro (formato de moeda R$ 1.234,56, data DD/MM/AAAA)
- O modelo DeepSeek (`deepseek-flash`) tem capacidade suficiente para extrair textos de comprovantes em português
- pdf2image + poppler-utils estão disponíveis no ambiente de execução
- A API key da DeepSeek será fornecida via variável de ambiente `DEEPSEEK_API_KEY`; `GROQ_API_KEY` é opcional (usada apenas se Groq estiver no `MODEL_FALLBACK_LIST`)
- O Django estará em um ambiente separado; o módulo não depende de Django
