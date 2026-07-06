# IntelDocs AI

## Overview
IntelDocs AI is an AI-powered enterprise knowledge platform where companies securely organize documents, repositories, and codebases by team. Employees can chat with their team's knowledge using advanced Retrieval-Augmented Generation (RAG), while admins monitor teams, documents, metadata, and analytics from a centralized dashboard.

## Key Features
- **Company & Team Workspaces**: Multi-tenant architecture supporting top-level companies and isolated sub-level teams with their own documents and chat history.
- **Context-Aware Chat**: Ask questions in plain language and get answers grounded in your own uploaded documents, complete with source citations.
- **Advanced RAG Pipeline**:
  - Out-of-the-box support for multiple file formats (PDF, DOCX, TXT, CSV, XLSX, PPTX, MD, HTML).
  - Configurable semantic chunking with a fallback to recursive character chunking for oversized sections.
  - Optional Contextual Chunking (using Groq LLMs) to prepend contextual notes to chunks before embedding, improving retrieval quality.
- **High-Performance Search**: Fast cosine similarity vector search utilizing PostgreSQL with the `pgvector` extension. Full-text search `tsvector` fallback available.
- **Session-Based Security**: Strict visibility rules. Team access explicitly requires an active company session validation.

## Architecture and Project Structure
The application is built on a modern, asynchronous Python backend tailored for high concurrency and heavy AI workloads.
- **Backend Framework**: FastAPI handles asynchronous HTTP requests and routing.
- **Database Layer**: PostgreSQL via `asyncpg` and SQLAlchemy ORM, using `pgvector` for embedding storage and fast similarity lookups.
- **AI/LLM Stack**: LangChain powers the retrieval chain and document loaders. HuggingFace's `all-MiniLM-L6-v2` is used for local embeddings (eagerly loaded on startup), while Groq API (`llama-3.1-8b-instant`) handles inference.
- **Frontend**: Lightweight, vanilla HTML, CSS, and JS files for serving the company and team dashboards.

## Tech Stack and Dependencies
- **Core Framework**: `fastapi`, `uvicorn`, `pydantic`
- **Database**: `sqlalchemy`, `asyncpg`, `pgvector`
- **AI / LLMs**: `langchain`, `langchain-groq`, `langchain-huggingface`, `langgraph`, `sentence-transformers`, `tiktoken`
- **Document Loaders**: `pypdf`, `unstructured` (via LangChain integrations)
- **Security**: `bcrypt`

## Installation and Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd IntelDocs-AI
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Database Setup:**
   Ensure PostgreSQL is installed and running. You must enable the `pgvector` extension in your database:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

5. **Start the server:**
   Database tables will be automatically created on startup via SQLAlchemy's lifecycle events.
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## Configuration
The application relies on environment variables (which can be provided via a `.env` file):

- `GROQ_API_KEY`: Required for the Groq LLM integration (chat generation and optional contextual chunking).
- `DATABASE_URL`: Your PostgreSQL connection string (e.g., `postgresql+asyncpg://user:password@localhost:5432/dbname`).
- `PORT`: Port on which the API runs (default: 8000).
- `DEBUG`: Set to `True` for detailed SQLAlchemy query logging.
- `SESSION_TOKEN_EXPIRE_HOURS`: Token expiration lifetime.

Additional RAG configurations (chunk sizes, overlap, threshold semantics) can be tuned directly within `config/settings.py`.

## Usage Examples

### 1. Uploading a Document (Team Level)
```bash
curl -X POST "http://localhost:8000/knowledge/team/knowledge/upload" \
  -H "Authorization: Bearer <company_token>:<team_token>" \
  -F "file=@/path/to/document.pdf"
```

### 2. Asking a Question
```bash
curl -X POST "http://localhost:8000/chat/team/ask" \
  -H "Authorization: Bearer <company_token>:<team_token>" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is our current refund policy?", "session_id": null}'
```

## API Modules
- **`company_auth` / `team_auth`**: Endpoints for registering, logging in, and logging out companies and teams.
- **`knowledge`**: Endpoints to upload, update, list, and delete documents for both company and team scopes.
- **`chat`**: Handles conversation sessions. Persists questions and RAG-generated answers for chat history.
- **`company_dashboard` / `team_dashboard`**: Endpoints serving the frontend views.

## Folder Structure
```text
IntelDocs-AI/
├── config/              # Application and RAG tuning configurations
├── database/            # SQLAlchemy models, async connection setup, and raw schema SQL
├── frontend/            # Vanilla HTML/JS/CSS client dashboards
├── services/
│   ├── pipeline/        # High-level orchestration (chat execution, knowledge ingestion)
│   ├── prompts/         # System and user prompt templates for LangChain
│   ├── rag/             # Core RAG logic: document loading, chunking, embedding, retrieval, and chain
│   └── routes/          # FastAPI routers grouping endpoints by domain
├── utils/               # Exceptions, custom logging, and authentication middleware
├── main.py              # FastAPI application entry point and lifespan management
└── requirements.txt     # Python dependencies
```

## Development Workflow
1. Use `main.py` to test routing and startup hooks.
2. The RAG pipeline is deeply modular. To experiment with chunking strategies, modify `services/rag/chunks_embed.py`.
3. To alter LLM behavior or prompt design, check `services/prompts/`.
4. Run `demo.py` or `debug_retrival.py` (if available) to manually test the document loaders and similarity search without spinning up the entire API.

## Performance and Implementation Highlights
- **Smart Chunking Recovery**: Semantic chunking identifies logical document breakpoints. If an oversized chunk is produced, only that specific chunk falls back to recursive splitting, keeping semantic boundaries intact elsewhere.
- **Asynchronous Processing**: From `asyncpg` database transactions to `asyncio.to_thread` for blocking HuggingFace embedding calls, the API is strictly non-blocking.
- **Eager Model Loading**: The `sentence-transformers` embedding model is pre-loaded during the FastAPI lifespan hook to prevent cold-start latency on the first retrieval or upload request.

## Limitations
- Document visibility is strictly segmented between "company-wide" and "team-only". Granular user-level RBAC within a team is currently out of scope.
- `tiktoken` is used as a best-effort token counter, falling back to basic word splits if unsupported.
- Duplicate filenames within the same scope will replace older files if the `update` endpoint is called, or might cause logical duplication if blindly uploaded.

## Future Improvements
- Background task queues (e.g., Celery) for handling massive document uploads asynchronously.
- Implementation of an advanced hybrid search (combining sparse `tsvector` keyword matching with dense pgvector embeddings).
- Expansion of supported models beyond Groq and local HuggingFace embeddings.

## License
[MIT License](LICENSE) - Copyright (c) 2026 Muhammad Aniq Ramzan
