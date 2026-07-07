<div align="center">
  <h1>IntelDocs AI</h1>
  <p><strong>AI-powered Enterprise Knowledge & RAG Platform</strong></p>
  <p>
    <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI"></a>
    <a href="https://www.postgresql.org"><img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"></a>
    <a href="https://python.langchain.com/"><img src="https://img.shields.io/badge/LangChain-121212?style=for-the-badge&logo=chainlink&logoColor=white" alt="LangChain"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="License"></a>
  </p>
</div>

---

## Overview

**IntelDocs AI** is a highly scalable, AI-powered enterprise knowledge platform. It enables companies to securely organize documents, repositories, and codebases by team. Through advanced **Retrieval-Augmented Generation (RAG)**, employees can chat with their team's specific knowledge base, while administrators monitor teams, documents, metadata, and analytics from a centralized dashboard.

## Key Features

- **Multi-Tenant Architecture**: Robust workspaces supporting top-level company management and isolated sub-level teams with their own secure documents and chat histories.
- **Context-Aware Chat**: Interact with your data using plain language. Receive highly accurate answers grounded entirely in your uploaded documents, complete with source citations.
- **Advanced RAG Pipeline**:
  - **Omni-Format Support**: Process PDF, DOCX, TXT, CSV, XLSX, PPTX, MD, and HTML files seamlessly.
  - **Intelligent Chunking**: Configurable semantic chunking with fallback to recursive character splitting for optimal retrieval context.
  - **Contextual Enrichment**: Leverage Groq LLMs to prepend contextual notes to chunks prior to embedding, significantly boosting retrieval quality.
- **High-Performance Vector Search**: Lightning-fast cosine similarity vector search utilizing PostgreSQL + `pgvector`.
- **Session-Based Security**: Strict, hierarchical visibility rules ensuring team access explicitly requires active company session validation.

## Architecture & Tech Stack

Built on a modern, asynchronous Python backend, IntelDocs AI is tailored for high concurrency and heavy AI inference workloads.

| Layer | Technologies |
|-------|--------------|
| **Backend Framework** | FastAPI (Asynchronous HTTP requests & routing) |
| **Database Layer** | PostgreSQL, `asyncpg`, SQLAlchemy ORM, `pgvector` |
| **AI / LLM Stack** | LangChain, LangGraph, HuggingFace (`all-MiniLM-L6-v2`), Groq API |
| **Document Processing** | `pypdf`, `unstructured`, `tiktoken` |
| **Frontend** | Vanilla HTML, CSS, JavaScript (Lightweight Dashboards) |
| **Security** | `bcrypt` |

## Quick Start

### 1. Prerequisites
- Python 3.9+
- PostgreSQL database with the `pgvector` extension enabled.

### 2. Installation

Clone the repository and set up your virtual environment:

```bash
git clone <repository-url>
cd IntelDocs-AI
python -m venv .venv

# On Linux/macOS
source .venv/bin/activate  
# On Windows
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Configuration

Ensure PostgreSQL is running and execute the following SQL command in your database to enable vector storage:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 4. Environment Variables

Create a `.env` file in the root directory and configure the following variables (you can use `.env.example` if available):

```env
GROQ_API_KEY=your_groq_api_key
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
PORT=8000
DEBUG=True
SESSION_TOKEN_EXPIRE_HOURS=24
```
*(RAG configurations like chunk sizes and threshold semantics can be tuned in `config/settings.py`)*

### 5. Run the Server

Database tables are automatically created on startup via SQLAlchemy's lifecycle events.

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Usage Examples

### Uploading a Document (Team Scope)
```bash
curl -X POST "http://localhost:8000/knowledge/team/knowledge/upload" \
  -H "Authorization: Bearer <company_token>:<team_token>" \
  -F "file=@/path/to/document.pdf"
```

### Asking a Question
```bash
curl -X POST "http://localhost:8000/chat/team/ask" \
  -H "Authorization: Bearer <company_token>:<team_token>" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is our current refund policy?", "session_id": null}'
```

## Project Structure

```text
IntelDocs-AI/
├── config/              # Application & RAG tuning settings
├── database/            # SQLAlchemy models, async setup, and schema logic
├── frontend/            # Vanilla HTML/JS/CSS client dashboards
├── services/
│   ├── pipeline/        # High-level orchestration (chat execution, ingestion)
│   ├── prompts/         # LangChain prompt templates
│   ├── rag/             # Core RAG: loading, chunking, embedding, retrieval
│   └── routes/          # FastAPI REST endpoints
├── utils/               # Exceptions, logging, auth middleware
├── main.py              # Application entry point & lifespan management
└── requirements.txt     # Python dependencies
```

## Performance Highlights
- **Smart Chunking Recovery**: Identifies logical breakpoints seamlessly. If a chunk is oversized, only that specific chunk falls back to recursive splitting, keeping semantic boundaries intact.
- **Strictly Asynchronous**: From database transactions (`asyncpg`) to blocking embedding calls (`asyncio.to_thread`), the API guarantees non-blocking execution.
- **Zero Cold-Start Latency**: The `sentence-transformers` embedding model is pre-loaded during the FastAPI lifespan hook to ensure immediate availability for the first request.

## Future Roadmap
- [ ] **Background Queues**: Celery integration for handling massive document uploads asynchronously.
- [ ] **Hybrid Search**: Combining sparse keyword matching (`tsvector`) with dense vector embeddings (`pgvector`).
- [ ] **Model Agnosticism**: Expanded support for local LLMs and alternative commercial APIs (OpenAI, Anthropic).

## License
This project is licensed under the [MIT License](LICENSE) - Copyright (c) 2026 Muhammad Aniq Ramzan
