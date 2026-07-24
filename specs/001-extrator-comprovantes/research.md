# Research: Módulo Extrator de Comprovantes Bancários

## Decisiones Técnicas

### 1. Framework de Agentes: Agno

**Decision**: Agno

**Rationale**: Framework maduro com suporte nativo a múltiplos provedores de LLM (incluindo Groq), output estruturado via Pydantic, e manipulação de imagens (multimodal).

**Alternatives considered**:
- **LangChain**: Mais pesado, curva de aprendizado maior, excesso de abstrações para o caso de uso
- **LlamaIndex**: Focado em RAG, não é o ideal para extração direta de imagem
- **Chamada direta à API Groq**: Possível, mas perderia o output estruturado e gerenciamento de contexto do Agno

### 2. Provedor de Visão: Groq (Llama 3.2 90B Vision)

**Decision**: Groq via `agno.models.groq.Groq`

**Rationale**: Inferência extremamente rápida (tokens/s muito superior a concorrentes), modelo Llama 3.2 90B Vision com boa capacidade de extração de texto em imagens, API compatível com OpenAI.

**Alternatives considered**:
- **OpenAI GPT-4o**: Mais caro, mesmo sendo excelente para visão
- **Google Gemini**: Bom, mas requer SDK separado
- **Claude 3.5 Sonnet**: Excelente para visão, porém mais lento que Groq

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

**Decision**: Parsing manual com `locale` ou regex

**Rationale**: O formato brasileiro (R$ 1.234,56) não é suportado nativamente pelo Python Decimal. Será necessário um parser que:
- Remova o símbolo R$
- Troque `.` por ` ` (separador de milhar)
- Troque `,` por `.` (separador decimal)
- Converta para Decimal

### 7. Gerenciamento de API Key

**Decision**: `python-dotenv` + `.env`

**Rationale**: Padrão simples e seguro. A chave `GROQ_API_KEY` será lida de `.env` e carregada com `load_dotenv()`. O `.env` está no `.gitignore`.

## Dependências do Sistema

- **poppler-utils**: Necessário para pdf2image. Instalar via `apt install poppler-utils` ou `brew install poppler`
- **Python ≥ 3.13**: Conforme `.python-version`
