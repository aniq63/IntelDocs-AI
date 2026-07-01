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
    semantic_chunking: bool = True

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


# =============================================================================
# APPLICATION SETTINGS
# =============================================================================

class Settings:

    def __init__(self):
        self.rag = RAGConfig()


settings = Settings()