---
description: "Task list for feature: Módulo Extrator de Comprovantes Bancários"
---

# Tasks: Módulo Extrator de Comprovantes Bancários

**Input**: Design documents from `specs/001-extrator-comprovantes/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Not requested in spec — test tasks omitted.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize project with dependencies and configuration

- [ ] T001 Configure pyproject.toml with dependencies (agno, groq, pdf2image, Pillow, pydantic, python-dotenv)
- [ ] T002 [P] Create .env.example with GROQ_API_KEY placeholder
- [ ] T003 [P] Create agente_extrator/ package directory structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core schemas and utilities that ALL user stories depend on

- [ ] T004 Create agente_extrator/__init__.py with package exports
- [ ] T005 Create agente_extrator/schemas.py with BankReceipt Pydantic model
- [ ] T006 Create agente_extrator/utils.py with Brazilian format parsers (moeda, data)

---

## Phase 3: User Story 1 - Extrair dados de comprovante via imagem (Priority: P1) 🎯 MVP

**Goal**: Usuário faz upload de imagem PNG/JPG de comprovante e recebe JSON com dados extraídos

**Independent Test**: Fornecer imagem de comprovante PIX e verificar JSON completo com todos os campos

- [ ] T007 [P] [US1] Create agente_extrator/processors/__init__.py
- [ ] T008 [P] [US1] Create agente_extrator/processors/image_processor.py with ImageProcessor class (Pillow: redimensionar, corrigir orientação, otimizar)
- [ ] T009 [US1] Create agente_extrator/agent.py with Agno Agent configurado para Groq (llama-3.2-90b-vision-preview) com output_type=BankReceipt

**Checkpoint**: US1 funcional — imagem de comprovante → JSON validado

---

## Phase 4: User Story 2 - Extrair dados de comprovante via PDF (Priority: P2)

**Goal**: Usuário faz upload de PDF de comprovante e recebe JSON com dados extraídos

**Independent Test**: Fornecer PDF de comprovante TED e verificar JSON completo

- [ ] T010 [US2] Create agente_extrator/processors/pdf_processor.py with PdfProcessor class (pdf2image: converter páginas para imagens PIL)

**Checkpoint**: US2 funcional — PDF de comprovante → JSON validado

---

## Phase 5: User Story 3 - Integração Django via função bridge (Priority: P3)

**Goal**: Desenvolvedor Django importa `extrair_comprovante()` e recebe dict pronto para salvar no model

**Independent Test**: Chamar `extrair_comprovante(BytesIO(...))` e verificar dict de retorno

- [ ] T011 [P] [US3] Create agente_extrator/integration.py with extrair_comprovante() function (aceita str, Path, BytesIO, UploadedFile)
- [ ] T012 [P] [US3] Create exemplo_uso.py with CLI argument parsing e demonstração de uso

**Checkpoint**: US3 funcional — função bridge integrada com Django

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verificação final e documentação

- [ ] T013 Verify pyproject.toml configuration and install dependencies with `uv sync`
- [ ] T014 Validate .gitignore includes .env and __pycache__/

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — can run independently
- **US2 (Phase 4)**: Depends on Foundational (inherits agent.py from US1) — run after US1
- **US3 (Phase 5)**: Depends on Foundational + US1 + US2 — run last
- **Polish (Phase 6)**: Depends on all phases complete

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
