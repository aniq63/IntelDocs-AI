from dataclasses import dataclass


# =============================================================================
# RAG CONFIGURATION
# =============================================================================

@dataclass(frozen=True)
class RAGConfig:

    # -------------------------------------------------------------------------
    # Embedding Model
    # -------------------------------------------------------------------------
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    embedding_cache_dir: str = "./.cache_embeddings"

    # -------------------------------------------------------------------------
    # Chunking Strategy
    # -------------------------------------------------------------------------
    semantic_chunking: bool = False

    # -------------------------------------------------------------------------
    # Recursive Chunking (Fallback)
    # -------------------------------------------------------------------------
    fallback_chunk_size: int = 1000

    fallback_chunk_overlap: int = 200

    # Maximum allowed chunk size before falling back
    max_chunk_size: int = 2000

    # -------------------------------------------------------------------------
    # Semantic Chunking
    # -------------------------------------------------------------------------
    breakpoint_threshold_type: str = "percentile"

    breakpoint_threshold_amount: int = 95

    # -------------------------------------------------------------------------
    # Embedding Dimensions
    # -------------------------------------------------------------------------
    embedding_dimension: int = 384

    # -------------------------------------------------------------------------
    # Contextual Chunking (Groq LLM context enrichment)
    # -------------------------------------------------------------------------

    # Master switch - off by default. When True, every chunk gets an
    # LLM-generated context note prepended before embedding.
    contextual_chunking: bool = True

    # Groq model used to generate context notes
    contextual_model: str = "llama-3.1-8b-instant"

    # Max characters of the source document sent as reference context
    # to the LLM (keeps prompts small/cheap even for very long files)
    contextual_max_doc_chars: int = 20000

    # Max concurrent Groq calls when contextualizing chunks
    contextual_max_workers: int = 5


# =============================================================================
# APPLICATION SETTINGS
# =============================================================================

class Settings:

    def __init__(self):
        self.rag = RAGConfig()


settings = Settings()