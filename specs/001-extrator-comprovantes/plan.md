# Implementation Plan: Módulo Extrator de Comprovantes Bancários

**Branch**: `001-extrator-comprovantes` | **Date**: 2026-07-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-extrator-comprovantes/spec.md`

> **Nota de revisão (2026-10-13)**: Plano sincronizado com a implementação v0.2.0 —
> pacote `bank_receipt_extractor`, `extract_receipt()`, DeepSeek (`deepseek-flash`)
> primário com fallback Groq via `MODEL_FALLBACK_LIST`, Python ≥3.12.

## Summary

Módulo Python (pacote `bank_receipt_extractor`) para extração automatizada de dados de comprovantes bancários brasileiros (PIX, TED, DOC) usando Agno + DeepSeek (`deepseek-flash`) com fallback configurável para Groq. Aceita PDF ou imagem, processa e retorna JSON validado com valor, data, número de controle, banco de origem, tipo, banco destino e favorecido. Integração com Django via função bridge `extract_receipt()`.

## Technical Context

**Language/Version**: Python ≥3.12

**Primary Dependencies**: agno, groq, openai (SDK usado pelo Agno para DeepSeek), pdf2image, Pillow, pydantic, python-dotenv

**Storage**: N/A (processamento stateless, sem persistência)

**Testing**: pytest + pytest-cov (123 testes, 100% de cobertura)

**Target Platform**: Linux server (onde o Django estiver hospedado); poppler-utils necessário no sistema

**Project Type**: Python library/package (pacote instalável)

**Performance Goals**: Extração < 10s para imagem, < 15s para PDF de até 5 páginas

**Constraints**: Requer internet para API DeepSeek (fallback Groq opcional via `MODEL_FALLBACK_LIST`); poppler-utils instalado no servidor; imagem/página de PDF com resolução mínima de 300 DPI para extração confiável

**Scale/Scope**: Uso em formulário de inscrição em evento (dezenas a centenas de extrações por mês)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Status | Justificativa |
|-----------|--------|---------------|
| I. Modularidade | ✅ PASS | Pacote independente, bridge para Django |
| II. Segurança | ✅ PASS | API key via .env, temp files limpos |
| III. Tipagem Forte | ✅ PASS | Schemas Pydantic para input/output |
| IV. Testabilidade | ✅ PASS | Processadores independentes, múltiplos formatos de input |
| V. Simplicidade | ✅ PASS | Apenas campos solicitados, sem abstrações extras |

## Project Structure

### Documentation (this feature)

```text
specs/001-extrator-comprovantes/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── contracts/           # Phase 1 output (interface contracts)
└── quickstart.md        # Phase 1 output
```

### Source Code (repository root)

```text
bank_receipt_extractor/
├── __init__.py
├── errors.py              # Erros tipados + mapeamento HTTP (erro_para_status)
├── schemas.py             # Pydantic models
├── utils.py               # Brazilian format parsers
├── agent.py               # Agno agent setup (DeepSeek + fallback Groq)
├── processors/
│   ├── __init__.py
│   ├── pdf_processor.py   # PDF → image conversion
│   └── image_processor.py # Image preprocessing
└── integration.py         # Django bridge function

tests/                     # pytest suite (123 testes, 100% cobertura)
usage_example.py           # Standalone usage example
.env.example               # Environment variables template
```

**Structure Decision**: Single Python package (`bank_receipt_extractor/`) sem subpacotes aninhados. Cada processador em módulo separado. A raiz do projeto contém apenas a configuração (`pyproject.toml`, `.env.example`) e o exemplo de uso.

## Complexity Tracking

*N/A — Nenhuma violação de constituição identificada.*

## Phase 0: Research

Ver [research.md](research.md)

## Phase 1: Design

### Data Model

Ver [data-model.md](data-model.md)

### Contracts

Ver [contracts/](contracts/)

### Quickstart

Ver [quickstart.md](quickstart.md)
