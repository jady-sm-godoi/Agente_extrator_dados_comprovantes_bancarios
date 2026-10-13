# Research: Módulo Extrator de Comprovantes Bancários

> **Nota de revisão (2026-10-13)**: Decisões sincronizadas com a implementação v0.2.0.
> O provedor primário passou a ser DeepSeek (`deepseek-flash`) com fallback Groq
> (Emenda E001), e o runtime mínimo é Python ≥3.12.

## Decisões Técnicas

### 1. Framework de Agentes: Agno

**Decision**: Agno

**Rationale**: Framework maduro com suporte nativo a múltiplos provedores de LLM (incluindo Groq), output estruturado via Pydantic, e manipulação de imagens (multimodal).

**Alternatives considered**:
- **LangChain**: Mais pesado, curva de aprendizado maior, excesso de abstrações para o caso de uso
- **LlamaIndex**: Focado em RAG, não é o ideal para extração direta de imagem
- **Chamada direta à API Groq**: Possível, mas perderia o output estruturado e gerenciamento de contexto do Agno

### 2. Provedor de Visão: DeepSeek (deepseek-flash) com fallback Groq

**Decision**: `agno.models.deepseek.DeepSeek` com `deepseek-flash` como primário; fallback ordenado e configurável via `MODEL_FALLBACK_LIST` (`agno.models.groq.Groq` como alternativa)

**Rationale**: O `deepseek-flash` é o modelo de visão ativo na DeepSeek e tem custo ~6x menor por extração que a alternativa na Groq (Emenda E001). O fallback configurável mantém a operação resiliente à indisponibilidade de um provedor.

**Alternatives considered**:
- **Groq Llama 3.2 90B Vision**: modelo descontinuado na Groq — motivo da Emenda E001
- **OpenAI GPT-4o**: Mais caro, mesmo sendo excelente para visão
- **Google Gemini**: Bom, mas requer SDK separado
- **Claude 3.5 Sonnet**: Excelente para visão, porém mais lento que as alternativas

### 3. Conversão PDF → Imagem: pdf2image + poppler-utils

**Decision**: pdf2image + poppler-utils

**Rationale**: Biblioteca madura e confiável que converte páginas PDF em imagens PIL. Poppler é o padrão da indústria para renderização de PDF.

**Alternatives considered**:
- **PyMuPDF (fitz)**: Mais rápido, mas licença AGPL pode ser restritiva
- **pdfplumber**: Focado em extração de tabelas, não renderização
- **PyPDF2**: Apenas metadados e texto, sem renderização para imagem

### 4. Processamento de Imagem: Pillow

**Decision**: Pillow (PIL Fork)

**Rationale**: Biblioteca padrão para manipulação de imagens em Python. Necessária para redimensionar, corrigir orientação e otimizar imagens antes de enviar à API Groq.

**Alternatives considered**:
- **OpenCV**: Mais poderoso, mas pesado para o caso de uso (apenas redimensionamento e rotação)
- **scikit-image**: Muito pesado para necessidades simples

### 5. Validação de Schemas: Pydantic v2

**Decision**: Pydantic v2

**Rationale**: Padrão da indústria para validação de dados em Python. Usado nativamente pelo Agno para output estruturado. Suporte a tipos nativos (Decimal, date), validação personalizada e serialização para JSON.

### 6. Formatação de Moeda Brasileira

**Decision**: Parsing com regex em `utils.parse_brazilian_decimal` (implementado)

**Rationale**: O formato brasileiro (R$ 1.234,56) não é suportado nativamente pelo Python Decimal. O parser:
- Remove o símbolo R$
- Remove o separador de milhar (`.`)
- Troca `,` por `.` (separador decimal)
- Converte para Decimal

### 7. Gerenciamento de API Keys

**Decision**: `python-dotenv` + `.env`, com `DEEPSEEK_API_KEY` (primária), `GROQ_API_KEY` (opcional, fallback) e `MODEL_FALLBACK_LIST` (opcional)

**Rationale**: Padrão simples e seguro. As chaves são lidas de `.env` via `load_dotenv()`, carregado pela aplicação hospedeira; o `.env` está no `.gitignore`. Nenhuma chave é hardcoded (Princípio II).

## Dependências do Sistema

- **poppler-utils**: Necessário para pdf2image. Instalar via `apt install poppler-utils` ou `brew install poppler`
- **Python ≥ 3.12**: Conforme `pyproject.toml` e `.python-version`
