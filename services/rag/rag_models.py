import os
import logging
from pathlib import Path
from dotenv import load_dotenv

from langchain_classic.embeddings import CacheBackedEmbeddings
from langchain_classic.storage import LocalFileStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq


from config.settings import settings
from utils.exception import MyException


load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
 
if not api_key:
            raise MyException(ValueError("GROQ_API_KEY is not set in the environment."))



# ---------------------------------------------------------------------------
# Process-wide embedding model singleton
# ---------------------------------------------------------------------------

_embeddings_instance = None


def embeddings_model():
    """Build and return a fresh cached embedding model (internal helper)."""
    logging.info("Loading embedding model...")

    # Underlying Hugging Face embedding model
    underlying_embeddings = HuggingFaceEmbeddings(
        model_name=settings.rag.embedding_model,
        model_kwargs={"device": "cpu"},  # Change to "cuda" if using a GPU
    )

    # Directory to store cached embeddings
    cache_path = Path(settings.rag.embedding_cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    cache_store = LocalFileStore(str(cache_path))

    # Wrap the model with a cache
    embeddings = CacheBackedEmbeddings.from_bytes_store(
        underlying_embeddings=underlying_embeddings,
        document_embedding_cache=cache_store,
        namespace=settings.rag.embedding_model,
    )

    logging.info("Embedding model loaded successfully.")
    return embeddings


def get_embeddings_model():
    """
    Return the process-wide embedding model singleton.

    Call ``warm_up_embeddings_model()`` once at application startup
    (e.g. inside the FastAPI lifespan handler) so that the first real
    request never blocks on model loading.  If that hasn't happened yet
    this function will still work — it just loads the model on first call.
    """
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = embeddings_model()
    return _embeddings_instance


def warm_up_embeddings_model():
    """
    Eagerly load the embedding model at startup.

    Invoke this from the FastAPI ``lifespan`` handler so the (potentially
    large) HuggingFace model is resident in memory before the first
    request arrives — eliminating the cold-start delay on the first
    document upload or the first chat query.
    """
    logging.info("[startup] Warming up embedding model...")
    get_embeddings_model()
    logging.info("[startup] Embedding model is ready.")



def load_llm_models():
    """Load and return different llm models of GROQ using langchain"""

    llm = ChatGroq(model=settings.rag.llm_model, temperature=0, api_key=api_key)

    return llm


