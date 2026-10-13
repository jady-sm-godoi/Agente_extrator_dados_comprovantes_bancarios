---
description: "Task list for feature: Módulo Extrator de Comprovantes Bancários"
---

# Tasks: Módulo Extrator de Comprovantes Bancários

**Input**: Design documents from `specs/001-extrator-comprovantes/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Não solicitados na spec original; suite de testes adicionada na Fase 7 (T015).

> **Nota de revisão (2026-10-13)**: Nomes sincronizados com a implementação v0.2.0
> (`bank_receipt_extractor/`, `extract_receipt()`, `usage_example.py`, DeepSeek).
> A Fase 7 registra as evoluções pós-MVP efetivamente realizadas.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize project with dependencies and configuration

- [X] T001 Configure pyproject.toml with dependencies (agno, groq, pdf2image, Pillow, pydantic, python-dotenv)
- [X] T002 [P] Create .env.example with DEEPSEEK_API_KEY placeholder (GROQ_API_KEY opcional)
- [X] T003 [P] Create bank_receipt_extractor/ package directory structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core schemas and utilities that ALL user stories depend on

- [X] T004 Create bank_receipt_extractor/__init__.py with package exports
- [X] T005 Create bank_receipt_extractor/schemas.py with BankReceipt Pydantic model
- [X] T006 Create bank_receipt_extractor/utils.py with Brazilian format parsers (moeda, data)

---

## Phase 3: User Story 1 - Extrair dados de comprovante via imagem (Priority: P1) 🎯 MVP

**Goal**: Usuário faz upload de imagem PNG/JPG de comprovante e recebe JSON com dados extraídos

**Independent Test**: Fornecer imagem de comprovante PIX e verificar JSON completo com todos os campos

- [X] T007 [P] [US1] Create bank_receipt_extractor/processors/__init__.py
- [X] T008 [P] [US1] Create bank_receipt_extractor/processors/image_processor.py with ImageProcessor class (Pillow: redimensionar, corrigir orientação, otimizar)
- [X] T009 [US1] Create bank_receipt_extractor/agent.py with Agno Agent configurado para DeepSeek (deepseek-flash) com output_schema=BankReceipt e fallback via MODEL_FALLBACK_LIST

**Checkpoint**: US1 funcional — imagem de comprovante → JSON validado

---

## Phase 4: User Story 2 - Extrair dados de comprovante via PDF (Priority: P2)

**Goal**: Usuário faz upload de PDF de comprovante e recebe JSON com dados extraídos

**Independent Test**: Fornecer PDF de comprovante TED e verificar JSON completo

- [X] T010 [US2] Create bank_receipt_extractor/processors/pdf_processor.py with PdfProcessor class (pdf2image: converter páginas para imagens PIL)

**Checkpoint**: US2 funcional — PDF de comprovante → JSON validado

---

## Phase 5: User Story 3 - Integração Django via função bridge (Priority: P3)

**Goal**: Desenvolvedor Django importa `extract_receipt()` e recebe dict pronto para salvar no model

**Independent Test**: Chamar `extract_receipt(BytesIO(...))` e verificar dict de retorno

- [X] T011 [P] [US3] Create bank_receipt_extractor/integration.py with extract_receipt() function (aceita str, Path, BytesIO, UploadedFile)
- [X] T012 [P] [US3] Create usage_example.py with CLI argument parsing e demonstração de uso

**Checkpoint**: US3 funcional — função bridge integrada com Django

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verificação final e documentação

- [X] T013 Verify pyproject.toml configuration and install dependencies with `uv sync`
- [X] T014 Validate .gitignore includes .env and __pycache__/

---

## Phase 7: Pós-MVP (evoluções realizadas)

**Purpose**: Registrar as evoluções entregues após o MVP (v0.1.x → v0.2.0)

- [X] T015 Add automated test suite (100% de cobertura) — commit d7c940a
- [X] T016 Add security hardening (limite 50MB, timeout de 30s, validação MIME por magic bytes, logging estruturado, pip-audit) — commit 84ddb35
- [X] T017 Prepare PyPI package (hatchling, classifiers oficiais, README bilíngue, documentação de segurança) — commits 8c9369f, d4a4be2, 6ff4dcc
- [X] T018 Rename package to `bank_receipt_extractor` com README bilíngue — commit f6172ea
- [X] T019 Support Python ≥3.12 (compat) e atualização do modelo Groq padrão — commit 27851bb
- [X] T020 Implement multi-provider fallback via `MODEL_FALLBACK_LIST` — commit 0c7c4c4
- [X] T021 Typed extraction errors com `status` HTTP e `motivo` — commit 26a9630
- [X] T022 Expose fallback cause in output dict (campo `fallback`) — commit 11e2ff4

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — can run independently
- **US2 (Phase 4)**: Depends on Foundational (inherits agent.py from US1) — run after US1
- **US3 (Phase 5)**: Depends on Foundational + US1 + US2 — run last
- **Polish (Phase 6)**: Depends on all phases complete
- **Pós-MVP (Phase 7)**: Executada após o MVP — registra as evoluções entregues (v0.1.x → v0.2.0)

### Parallel Opportunities

- T002 and T003 can run in parallel (different files)
- T007 and T008 can run in parallel (different files)
- T011 and T012 can run in parallel (different files)

## Implementation Strategy

### MVP First (Phase 1 + 2 + US1)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (T004, T005, T006)
3. Complete Phase 3: US1 — imagem funcional
4. **STOP and VALIDATE**: Testar com imagem de comprovante real

### Incremental Delivery

1. Setup + Foundational + US1 → MVP (extração por imagem) ✅
2. Add US2 → extração por PDF
3. Add US3 → bridge Django + exemplo de uso
