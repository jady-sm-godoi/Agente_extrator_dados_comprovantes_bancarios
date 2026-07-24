# Implementation Plan: Módulo Extrator de Comprovantes Bancários

**Branch**: `001-extrator-comprovantes` | **Date**: 2026-07-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-extrator-comprovantes/spec.md`

## Summary

Módulo Python para extração automatizada de dados de comprovantes bancários brasileiros (PIX, TED, DOC) usando Agno + Groq (Llama 3.2 90B Vision). Aceita PDF ou imagem, processa e retorna JSON validado com valor, data, número de controle, banco de origem, tipo, banco destino e favorecido. Integração com Django via função bridge `extrair_comprovante()`.

## Technical Context

**Language/Version**: Python ≥3.13

**Primary Dependencies**: agno, groq, pdf2image, Pillow, pydantic, python-dotenv

**Storage**: N/A (processamento stateless, sem persistência)

**Testing**: pytest (pode ser adicionado posteriormente)

**Target Platform**: Linux server (onde o Django estiver hospedado); poppler-utils necessário no sistema

**Project Type**: Python library/package (pacote instalável)

**Performance Goals**: Extração < 10s para imagem, < 15s para PDF de até 5 páginas

**Constraints**: Requer internet para API Groq; poppler-utils instalado no servidor; imagem/página de PDF com resolução mínima de 300 DPI para extração confiável

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
agente_extrator/
├── __init__.py
├── schemas.py            # Pydantic models
├── utils.py              # Brazilian format parsers
├── agent.py              # Agno agent setup with Groq
├── processors/
│   ├── __init__.py
│   ├── pdf_processor.py  # PDF → image conversion
│   └── image_processor.py # Image preprocessing
└── integration.py        # Django bridge function

exemplo_uso.py            # Standalone usage example
.env.example              # Environment variables template
```

**Structure Decision**: Single Python package (`agente_extrator/`) sem subpacotes aninhados. Cada processador em módulo separado. A raiz do projeto contém apenas a configuração (`pyproject.toml`, `.env.example`) e o exemplo de uso.

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
